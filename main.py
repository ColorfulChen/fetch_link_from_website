import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path
import argparse
import re
import time

input_url = ""
result_dir = ""
valid_link_path = ""
invalid_link_path = ""
result_path = ""
download_path = ""

valid_link = None
invalid_link = None
result = None

valid_link_set = set()
invalid_link_set = set()

def safe_soup(content):
    try:
        return BeautifulSoup(content, 'lxml')
    except:
        try:
            return BeautifulSoup(content, 'html.parser')
        except:
            try:
                encoding = chardet.detect(content)['encoding']
                return BeautifulSoup(content.decode(encoding, errors='replace'), 'html.parser')
            except:
                return None

def safe_request(url, headers, timeout=2):
    """带异常处理的请求封装"""
    try:
        response = requests.get(url, 
                              headers=headers, 
                              timeout=timeout,
                              allow_redirects=True,
                              verify=True)  # 验证SSL证书
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

def get_all_links(url,depth = 1):
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
    soup = safe_soup(response.content)
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
            response = requests.get(link,stream=True)
            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
                    print(f"文件已下载到: {save_path}")
                    success = success + 1.0
        except:
            try:
                response = requests.get(link)
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
    args = parser.parse_args()
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

    valid_link = open(valid_link_path, "w+")
    invalid_link = open(invalid_link_path, "w+")
    result = open(result_path, "w+")

    get_all_links(input_url)
    valid_link.close()
    invalid_link.close()

    precision = download_all_content()
    validrate = len(valid_link_set) / (len(valid_link_set) + len(invalid_link_set))
    result.write(f'precision:{precision}\n')
    result.write(f'validrate:{validrate}\n')
    result.close()