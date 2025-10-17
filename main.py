import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path
import argparse
import re
import time
import os
import chardet

input_url = ""
result_dir = ""
valid_link_path = ""
invalid_link_path = ""
result_path = ""
download_path = ""

# 新增：代理配置
proxy_url = None
requests_proxies = None

valid_link = None
invalid_link = None
result = None

valid_link_set = set()
invalid_link_set = set()

# 新增：全局浏览器实例（延迟初始化）
driver = None

def safe_soup(content, content_type=None):
    try:
        is_xml = False
        if content_type:
            ct = content_type.lower()
            if 'xml' in ct or 'xhtml' in ct:
                is_xml = True
        else:
            head = content[:200].lstrip() if isinstance(content, (bytes, bytearray)) else str(content)[:200].lstrip()
            try:
                if isinstance(head, (bytes, bytearray)):
                    h = head.lower()
                    if h.startswith(b'<?xml') or b'<rss' in h or b'<feed' in h:
                        is_xml = True
                else:
                    h = head.lower()
                    if h.startswith('<?xml') or '<rss' in h or '<feed' in h:
                        is_xml = True
            except:
                pass
        if is_xml:
            return BeautifulSoup(content, 'xml')  # 使用 XML 解析器，避免警告
        return BeautifulSoup(content, 'lxml')
    except:
        try:
            return BeautifulSoup(content, 'html.parser')
        except:
            try:
                encoding = chardet.detect(content)['encoding']
                decoded = content.decode(encoding or 'utf-8', errors='replace')
                if content_type and ('xml' in content_type.lower() or 'xhtml' in content_type.lower()):
                    return BeautifulSoup(decoded, 'xml')
                return BeautifulSoup(decoded, 'html.parser')
            except:
                return None

# 新增：初始化无头浏览器（Selenium/Chrome）
def init_driver():
    global driver
    if driver is not None:
        return driver
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        opts = Options()
        # 现代无头模式
        opts.add_argument('--headless=new')
        opts.add_argument('--disable-gpu')
        opts.add_argument('--no-sandbox')
        opts.add_argument('--window-size=1280,1024')
        # 新增：Selenium 代理
        if proxy_url:
            opts.add_argument(f'--proxy-server={proxy_url}')
        driver = webdriver.Chrome(options=opts)
        driver.set_page_load_timeout(12)
        return driver
    except Exception as e:
        print(f"初始化截图浏览器失败: {e}")
        driver = None
        return None

# 新增：对指定 URL 截图并保存到 result_dir
def screenshot_page(url):
    global driver
    try:
        drv = init_driver()
        if not drv:
            return None
        drv.get(url)
        time.sleep(1)  # 简单等待，避免空白截图
        illegal_chars = r'[<>:"/\\|?*\x00-\x1F]'
        fname = "screenshot-" + re.sub(illegal_chars, '', url) + ".png"
        save_path = os.path.join(result_dir, fname)
        drv.save_screenshot(save_path)
        print(f"网页截图已保存: {save_path}")
        return save_path
    except Exception as e:
        print(f"截图失败 {url}: {e}")
        return None
    finally:
        # 截图后立即关闭无头浏览器
        try:
            if driver:
                driver.quit()
        except:
            pass
        driver = None

def safe_request(url, headers, timeout=2):
    """带异常处理的请求封装"""
    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=timeout,
            allow_redirects=True,
            verify=True,
            proxies=requests_proxies  # 新增：请求代理
        )
        response.raise_for_status()
        return response
    except requests.exceptions.HTTPError as e:
        print(f"HTTP错误 [{e.response.status_code}]: {url}")
    except requests.exceptions.ConnectionError:
        print(f"连接失败: {url}")
    except requests.exceptions.Timeout:
        print(f"请求超时: {url}")
    except requests.exceptions.RequestException as e:
        print(f"请求异常: {url} - {str(e)}")
    return None

def get_all_links(url,depth = 2):
    # 新增：仅在入口深度（depth==3）时对该页面截图
    if depth == 2:
        pass
        try:
            screenshot_page(url)
        except Exception as e:
            print(f"入口页面截图失败 {url}: {e}")
    if depth == 0:
        return []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    
    response = safe_request(url, headers)
    if not response:
        if url not in invalid_link_set:
            invalid_link_set.add(url)
            invalid_link.write(url)
            invalid_link.write('\n')
        print(f" {url} 无响应")
        return []
    
    base_url = response.url
    soup = safe_soup(response.content, response.headers.get('Content-Type', ''))
    if not soup:
        if url not in invalid_link_set:
            invalid_link_set.add(url)
            invalid_link.write(url)
            invalid_link.write('\n')
        print(f"无法解析 {url} 的内容")
        return []
    
    elements_to_check = {
        'a': ['href'],
        'img': ['src', 'srcset', 'data-src', 'data-srcset'],
        'script': ['src'],
        'link': ['href'],
        'video': ['src', 'poster', 'data-src'],
        'audio': ['src', 'data-src'],
        'iframe': ['src', 'data-src'],
        'source': ['src', 'srcset', 'data-src'],
        'embed': ['src', 'data-src'],
        'track': ['src'],
        'object': ['data']
    }

    links = set()

    for tag, attributes in elements_to_check.items():
        for element in soup.find_all(tag):
            for attr in attributes:
                if element.has_attr(attr):
                    value = element[attr].strip()
                    if not value:
                        continue

                    if attr in ['srcset', 'data-srcset']:
                        parts = [p.strip() for p in value.split(',') if p.strip()]
                        for part in parts:
                            url_part = part.split()[0]
                            absolute_url = urljoin(base_url, url_part)
                            links.add(absolute_url)
                    else:
                        absolute_url = urljoin(base_url, value)
                        links.add(absolute_url)

    valid_schemes = ['http', 'https']
    invalid_file = ['.js','.css']

    for link in links:
        if urlparse(link).scheme in valid_schemes:
            if not any(ext in link for ext in invalid_file):
                if(link not in valid_link_set):
                    valid_link_set.add(link)
                    valid_link.write(link)
                    valid_link.write('\n')
                    get_all_links(link,depth = depth-1)
            elif link not in invalid_link_set:
                    invalid_link_set.add(link)
                    invalid_link.write(link)
                    invalid_link.write('\n')

    return []

def download_all_content():
    success = 0.0
    fail = 0.0
    precision = 0.0
    illegal_chars = r'[<>:"/\\|?*\x00-\x1F]'

    for link in valid_link_set:
        print(link)
        save_path = download_path + re.sub(illegal_chars,'',link)
        try:
            response = requests.get(link, stream=True, proxies=requests_proxies)  # 新增：代理
            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
                    print(f"文件已下载到: {save_path}")
                    success = success + 1.0
        except:
            try:
                response = requests.get(link, proxies=requests_proxies)  # 新增：代理
                with open(save_path, 'wb') as file:
                    file.write(response.text)
                    print(f"文件已下载到: {save_path}")
                    success = success + 1.0
            except:
                print(f"下载失败")
                fail = fail + 1.0
    
    if success != 0:
        precision = success / (success + fail)

    return precision


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('link')
    # 新增：--proxy 参数，默认 127.0.0.1:10809，传 none 可禁用
    parser.add_argument('--proxy', default='http://127.0.0.1:10809', help='HTTP/HTTPS 代理，设为 none 以禁用')
    args = parser.parse_args()
    # 新增：初始化代理配置
    if args.proxy and args.proxy.lower() != 'none':
        proxy_url = args.proxy if args.proxy.startswith('http') else f'http://{args.proxy}'
        requests_proxies = {'http': proxy_url, 'https': proxy_url}
        print(f"已启用代理: {proxy_url}")
    else:
        proxy_url = None
        requests_proxies = None
        print("未使用代理")

    input_url = args.link
    url = urlparse(input_url).netloc
    timestamp = time.time()

    result_dir = "result/" + url + "-" + str(int(timestamp))
    valid_link_path = result_dir + "/valid_link.txt"
    invalid_link_path = result_dir + "/invalid_link.txt"
    result_path = result_dir + "/result.txt"
    download_path = result_dir + "/content/"

    precision = 0.0
    validrate = 0.0

    try:
        Path(result_dir).mkdir(parents=True, exist_ok=True)  
        print(f"Folder '{result_dir}' created successfully.")
    except OSError as error:
        print(f"Error occurred while creating folder: {error}")
    try:
        Path(download_path).mkdir(parents=True, exist_ok=True)  
        print(f"Folder '{download_path}' created successfully.")
    except OSError as error:
        print(f"Error occurred while creating folder: {error}")

    valid_link = open(valid_link_path, "w+",encoding='utf-8')
    invalid_link = open(invalid_link_path, "w+",encoding='utf-8')
    result = open(result_path, "w+",encoding='utf-8')

    get_all_links(input_url)
    
    valid_link.close()
    invalid_link.close()

    validrate = len(valid_link_set) / (len(valid_link_set) + len(invalid_link_set))
    result.write(f'validrate:{validrate}\n')

    precision = download_all_content()
    result.write(f'precision:{precision}\n')
    result.close()

    # 新增：退出浏览器
    try:
        if driver:
            driver.quit()
    except:
        pass