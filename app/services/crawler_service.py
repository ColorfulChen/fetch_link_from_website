"""
爬虫服务
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path
import re
import os
import uuid
import chardet
from app.config import config
import app.global_vars as app_global


def safe_soup(content, content_type=None):
    """安全的HTML/XML解析，支持智能检测"""
    try:
        is_xml = False
        # 通过 content_type 检测 XML
        if content_type:
            ct = content_type.lower()
            if 'xml' in ct or 'xhtml' in ct:
                is_xml = True
        else:
            # 通过内容头部检测 XML
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

        # 使用对应的解析器
        if is_xml:
            return BeautifulSoup(content, 'xml')
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


def safe_request(url, headers, timeout=2):
    """带异常处理的请求封装"""
    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=timeout,
            allow_redirects=True,
            verify=True
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


def screenshot_page(url, save_dir):
    """
    对指定 URL 截图并保存到指定目录

    参数:
        url: str - 需要截图的 URL
        save_dir: str - 截图保存目录

    返回:
        save_path: str - 截图文件路径，失败返回 None
    """
    try:
        drv = app_global.get_driver()
        if not drv:
            return None
        drv.get(url)
        import time
        time.sleep(1)  # 简单等待，避免空白截图

        # 生成安全的文件名
        illegal_chars = r'[<>:"/\\|?*\x00-\x1F]'
        fname = "screenshot-" + re.sub(illegal_chars, '', url) + ".png"
        save_path = os.path.join(save_dir, fname)

        drv.save_screenshot(save_path)
        print(f"网页截图已保存: {save_path}")
        return save_path
    except Exception as e:
        print(f"截图失败 {url}: {e}")
        return None


def get_all_links(url, depth=3):
    """
    递归爬取链接

    参数:
        url: str - 需要爬虫处理的 url 链接
        depth: int - 需要爬虫处理的深度

    返回:
        links: list[str] - 爬到的 links
    """
    if depth == 0:
        return []

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    response = safe_request(url, headers)
    if not response:
        print(f"{url} 无响应")
        return []

    base_url = response.url
    soup = safe_soup(response.content, response.headers.get('Content-Type', ''))
    if not soup:
        print(f"无法解析 {url} 的内容")
        return []

    # 定义需要检查的HTML元素和属性
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

    # 提取所有链接
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

    # 过滤有效链接
    valid_schemes = ['http', 'https']
    invalid_file = ['.js', '.css']

    valid_links = []
    for link in links:
        if urlparse(link).scheme in valid_schemes:
            if not any(ext in link for ext in invalid_file):
                valid_links.append(link)

    # 递归爬取子链接
    all_links = list(valid_links)
    if depth > 1:
        for link in valid_links:
            sub_links = get_all_links(link, depth=depth-1)
            all_links.extend(sub_links)

    return all_links


def crawler_link(url, depth=3):
    """
    爬虫主函数 - API调用入口

    参数:
        url: str - 需要爬虫的 url 链接
        depth: int - 爬虫的深度

    返回:
        dict: {
            'links': [{'link': str, 'content_path': str}, ...],
            'valid_rate': float,
            'precision_rate': float
        }
    """
    # 获取所有链接
    print(f"开始爬取: {url}, 深度: {depth}")

    # 创建保存目录（使用 UUID 生成唯一目录名）
    domain = urlparse(url).netloc
    unique_id = str(uuid.uuid4())
    save_dir = os.path.join(config.save_path, f"{domain}_{unique_id}")
    os.makedirs(save_dir, exist_ok=True)
    print(f"保存目录: {save_dir}")

    # 对入口页面进行截图
    try:
        screenshot_page(url, save_dir)
    except Exception as e:
        print(f"入口页面截图失败 {url}: {e}")

    all_links = get_all_links(url, depth)

    # 去重
    unique_links = list(set(all_links))
    print(f"总共爬取到 {len(unique_links)} 个唯一链接")

    # 统计变量
    valid_links = []
    invalid_links = []
    success_downloads = 0
    failed_downloads = 0

    illegal_chars = r'[<>:"/\\|?*\x00-\x1F]'

    # 下载内容并分类链接
    results = []
    for link in unique_links:
        print(f"处理链接: {link}")

        # 尝试请求链接验证有效性
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        response = safe_request(link, headers)

        if response:
            valid_links.append(link)

            # 生成安全的文件名
            filename = re.sub(illegal_chars, '', link)
            if len(filename) > 200:  # 限制文件名长度
                filename = filename[:200]
            save_path = os.path.join(save_dir, filename)

            # 下载内容
            try:
                with open(save_path, 'wb') as file:
                    file.write(response.content)
                print(f"文件已下载到: {save_path}")
                success_downloads += 1
                results.append({
                    'link': link,
                    'content_path': save_path
                })
            except Exception as e:
                print(f"下载失败: {link} - {str(e)}")
                failed_downloads += 1
                results.append({
                    'link': link,
                    'content_path': None
                })
        else:
            invalid_links.append(link)

    # 计算指标
    total_links = len(valid_links) + len(invalid_links)
    valid_rate = len(valid_links) / total_links if total_links > 0 else 0.0
    precision_rate = success_downloads / len(valid_links) if len(valid_links) > 0 else 0.0

    print(f"\n=== 爬取完成 ===")
    print(f"有效链接: {len(valid_links)}")
    print(f"无效链接: {len(invalid_links)}")
    print(f"Valid Rate: {valid_rate:.2%}")
    print(f"Precision Rate: {precision_rate:.2%}")

    return results, valid_rate, precision_rate