import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import argparse

result_links = set()

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

def get_all_links(url,depth):
    if depth == 0:
        return []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    
    response = safe_request(url, headers)
    if not response:
        return []
    
    base_url = response.url
    soup = safe_soup(response.content)
    if not soup:
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
    filtered_links = sorted([link for link in links if urlparse(link).scheme in valid_schemes])

    for link in filtered_links:
        result_links.add(link)
        get_all_links(link,depth-1)

    return filtered_links

if __name__ == "__main__":
    #input_url = "https://www.bbc.com/zhongwen/simp"
    #input_url = "https://www.baidu.com"
    #result_file = 'result/result.txt'

    parser = argparse.ArgumentParser()
    parser.add_argument('link')
    args = parser.parse_args()
    input_url = args.link
    result_file = "result/" + input_url +".txt"

    get_all_links(input_url,3)
    with open(result_file, "w+") as f:
        for link in result_links:
            f.write(link)
            f.write('\n')