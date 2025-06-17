import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path
import argparse
import re
import time
from pymongo import MongoClient
from datetime import datetime
import chardet
import os
from dotenv import load_dotenv
load_dotenv()

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

# MongoDB 配置
MONGO_URI = os.environ.get("DATABASE_BASE_URL", "mongodb://localhost:27017/")
DB_NAME = "data"
COLLECTION_NAME = "web"

# 初始化MongoDB连接
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]


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


def get_all_links(url, depth=3):
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
            # 存储无效链接到MongoDB
            collection.insert_one({
                'url': url,
                'status': 'invalid',
                'reason': 'no_response',
                'timestamp': datetime.now()
            })
        print(f" {url} 无响应")
        return []

    base_url = response.url
    soup = safe_soup(response.content)
    if not soup:
        if url not in invalid_link_set:
            invalid_link_set.add(url)
            invalid_link.write(url)
            invalid_link.write('\n')
            # 存储无效链接到MongoDB
            collection.insert_one({
                'url': url,
                'status': 'invalid',
                'reason': 'parse_error',
                'timestamp': datetime.now()
            })
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
    invalid_file = ['.js', '.css']

    for link in links:
        if urlparse(link).scheme in valid_schemes:
            if not any(ext in link for ext in invalid_file):
                if link not in valid_link_set:
                    valid_link_set.add(link)
                    valid_link.write(link)
                    valid_link.write('\n')
                    # 存储有效链接到MongoDB
                    collection.insert_one({
                        'url': link,
                        'status': 'valid',
                        'source_url': url,
                        'timestamp': datetime.now()
                    })
                    get_all_links(link, depth=depth - 1)
            elif link not in invalid_link_set:
                invalid_link_set.add(link)
                invalid_link.write(link)
                invalid_link.write('\n')
                # 存储无效链接到MongoDB
                collection.insert_one({
                    'url': link,
                    'status': 'invalid',
                    'reason': 'invalid_file_type',
                    'timestamp': datetime.now()
                })

    return []


def download_all_content():
    success = 0.0
    fail = 0.0
    precision = 0.0
    illegal_chars = r'[<>:"/\\|?*\x00-\x1F]'

    for link in valid_link_set:
        print(link)
        save_path = download_path + re.sub(illegal_chars, '', link)
        try:
            response = requests.get(link, stream=True)
            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
                print(f"文件已下载到: {save_path}")
                success = success + 1.0

                # 存储下载成功的记录到MongoDB
                collection.update_one(
                    {'url': link},
                    {'$set': {
                        'download_status': 'success',
                        'download_path': save_path,
                        'download_time': datetime.now()
                    }},
                    upsert=True
                )
        except:
            try:
                response = requests.get(link)
                with open(save_path, 'wb') as file:
                    file.write(response.text)
                    print(f"文件已下载到: {save_path}")
                    success = success + 1.0

                    # 存储下载成功的记录到MongoDB
                    collection.update_one(
                        {'url': link},
                        {'$set': {
                            'download_status': 'success',
                            'download_path': save_path,
                            'download_time': datetime.now()
                        }},
                        upsert=True
                    )
            except Exception as e:
                print(f"下载失败: {str(e)}")
                fail = fail + 1.0

                # 存储下载失败的记录到MongoDB
                collection.update_one(
                    {'url': link},
                    {'$set': {
                        'download_status': 'failed',
                        'error': str(e),
                        'download_time': datetime.now()
                    }},
                    upsert=True
                )

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

    # 初始化MongoDB连接
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    # 记录爬虫开始
    crawl_id = None
    try:
        crawl_id = collection.insert_one({
            'start_url': input_url,
            'status': 'started',
            'start_time': datetime.now()
        }).inserted_id
    except Exception as e:
        print(f"无法记录爬虫开始状态到MongoDB: {str(e)}")
        crawl_id = None

    valid_link = None
    invalid_link = None
    result = None

    try:
        valid_link = open(valid_link_path, "w+", encoding='utf-8')
        invalid_link = open(invalid_link_path, "w+", encoding='utf-8')
        result = open(result_path, "w+", encoding='utf-8')

        get_all_links(input_url)

        valid_link.close()
        invalid_link.close()

        validrate = len(valid_link_set) / (len(valid_link_set) + len(invalid_link_set))
        result.write(f'validrate:{validrate}\n')

        precision = download_all_content()
        result.write(f'precision:{precision}\n')
        result.close()

        # 记录爬虫完成状态
        if crawl_id:
            try:
                collection.update_one(
                    {'_id': crawl_id},
                    {'$set': {
                        'status': 'completed',
                        'end_time': datetime.now(),
                        'valid_links_count': len(valid_link_set),
                        'invalid_links_count': len(invalid_link_set),
                        'valid_rate': validrate,
                        'download_precision': precision
                    }}
                )
            except Exception as e:
                print(f"无法更新爬虫完成状态到MongoDB: {str(e)}")

    except Exception as e:
        print(f"爬虫运行出错: {str(e)}")
        # 记录错误状态
        if crawl_id:
            try:
                collection.update_one(
                    {'_id': crawl_id},
                    {'$set': {
                        'status': 'failed',
                        'end_time': datetime.now(),
                        'error': str(e),
                        'valid_links_count': len(valid_link_set),
                        'invalid_links_count': len(invalid_link_set)
                    }}
                )
            except Exception as e:
                print(f"无法记录爬虫错误状态到MongoDB: {str(e)}")
    finally:
        # 确保文件句柄关闭
        if valid_link and not valid_link.closed:
            valid_link.close()
        if invalid_link and not invalid_link.closed:
            invalid_link.close()
        if result and not result.closed:
            result.close()
        # 关闭MongoDB连接
        client.close()