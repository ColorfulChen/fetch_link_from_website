"""
爬虫服务 - 支持增量和全量爬取策略
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path
import re
import os
import uuid
import chardet
from datetime import datetime
from bson import ObjectId

from app.config import config
import app.global_vars as app_global
from app.database import get_db
from app.models import CrawledLinkModel, CrawlTaskModel, CrawlLogModel


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


def get_all_links(url, depth=3, exclude=None, visited=None):
    """
    递归爬取链接（支持增量爬取）

    参数:
        url: str - 需要爬虫处理的 url 链接
        depth: int - 需要爬虫处理的深度
        exclude: set - 需要排除的 url 集合（用于增量更新策略）
        visited: set - 已访问的 url 集合（避免重复爬取）

    返回:
        links: list[str] - 爬到的 links
    """
    if depth == 0:
        return []

    # 初始化 exclude 和 visited
    if exclude is None:
        exclude = set()
    if visited is None:
        visited = set()

    # 如果当前 URL 在排除列表中或已访问，则跳过
    if url in exclude or url in visited:
        return []

    # 标记为已访问
    visited.add(url)

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
        # 跳过排除列表中的链接
        if link in exclude:
            continue
        if urlparse(link).scheme in valid_schemes:
            if not any(ext in link for ext in invalid_file):
                valid_links.append(link)

    # 递归爬取子链接
    all_links = list(valid_links)
    if depth > 1:
        for link in valid_links:
            # 传递 exclude 和 visited 集合，避免重复爬取
            sub_links = get_all_links(link, depth=depth-1, exclude=exclude, visited=visited)
            all_links.extend(sub_links)

    return all_links


def crawler_link(url, depth=3, exclude=None):
    """
    爬虫主函数 - API调用入口（支持增量爬取）

    参数:
        url: str - 需要爬虫的 url 链接
        depth: int - 爬虫的深度
        exclude: list[str] - 需要排除的 url (用于增量更新策略)

    返回:
        tuple: (results, valid_rate, precision_rate)
        - results: list[dict] - [{'link': str, 'content_path': str}, ...]
        - valid_rate: float - 有效率
        - precision_rate: float - 精准率
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

    # 转换 exclude 为 set 以提高查找效率
    exclude_set = set(exclude) if exclude else set()

    # 调用 get_all_links 获取所有链接（已自动排除 exclude 中的链接）
    all_links = get_all_links(url, depth, exclude=exclude_set)

    # 去重
    unique_links = list(set(all_links))
    print(f"总共爬取到 {len(unique_links)} 个唯一链接（已排除 {len(exclude_set)} 个已存在链接）")

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
                    'content_path': save_path,
                    'status_code': response.status_code,
                    'content_type': response.headers.get('Content-Type', '')
                })
            except Exception as e:
                print(f"下载失败: {link} - {str(e)}")
                failed_downloads += 1
                results.append({
                    'link': link,
                    'content_path': None,
                    'status_code': response.status_code,
                    'content_type': response.headers.get('Content-Type', '')
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


class CrawlerService:
    """
    爬虫服务类 - 集成 MongoDB 数据库
    支持增量和全量两种爬取策略
    """

    def __init__(self):
        self.db = get_db()

    def crawl(self, task_id, website_id, strategy='incremental', depth=3, max_links=1000):
        """
        执行爬取任务

        参数:
            task_id: ObjectId - 任务ID
            website_id: ObjectId - 网站ID
            strategy: str - 爬取策略 (incremental/full)
            depth: int - 爬取深度
            max_links: int - 最大链接数

        返回:
            dict - 爬取结果统计
        """
        try:
            # 清除之前的停止标志(如果存在)
            app_global.clear_stop_flag(task_id)

            # 更新任务状态为 running
            self.db.crawl_tasks.update_one(
                {'_id': task_id},
                CrawlTaskModel.update_status('running')
            )

            # 记录日志
            self._log(task_id, 'INFO', f'开始爬取任务 - 策略: {strategy}')

            # 获取网站信息
            website = self.db.websites.find_one({'_id': website_id})
            if not website:
                raise Exception(f"网站不存在: {website_id}")

            url = website['url']
            domain = website['domain']

            # 根据策略准备 exclude 列表
            exclude_urls = []
            if strategy == 'incremental':
                # 增量策略：查询已爬取的链接
                crawled_docs = self.db.crawled_links.find(
                    {'website_id': website_id},
                    {'url': 1}
                )
                exclude_urls = [doc['url'] for doc in crawled_docs]
                self._log(task_id, 'INFO', f'增量模式：排除 {len(exclude_urls)} 个已存在链接')
            else:
                # 全量策略：不排除任何链接
                self._log(task_id, 'INFO', '全量模式：爬取所有链接')

            # 执行爬取
            results, valid_rate, precision_rate = crawler_link(url, depth, exclude_urls)

            # 检查是否需要停止（任务可能已被强制取消）
            if app_global.should_stop(task_id):
                self._log(task_id, 'INFO', '检测到取消信号，停止执行')
                app_global.clear_stop_flag(task_id)
                return {
                    'total_links': 0,
                    'valid_links': 0,
                    'invalid_links': 0,
                    'new_links': 0,
                    'valid_rate': 0,
                    'precision_rate': 0
                }

            # 保存爬取结果到数据库
            new_links = 0
            for result in results[:max_links]:  # 限制最大链接数
                # 检查是否需要停止
                if app_global.should_stop(task_id):
                    self._log(task_id, 'INFO', '检测到取消信号，停止保存')
                    break

                link_url = result['link']

                # 检查链接是否已存在
                existing_link = self.db.crawled_links.find_one({
                    'website_id': website_id,
                    'url': link_url
                })

                if existing_link:
                    # 更新已存在的链接
                    self.db.crawled_links.update_one(
                        {'_id': existing_link['_id']},
                        CrawledLinkModel.update_crawl_info()
                    )
                else:
                    # 插入新链接
                    link_doc = CrawledLinkModel.create(
                        website_id=website_id,
                        task_id=task_id,
                        url=link_url,
                        domain=urlparse(link_url).netloc,
                        link_type='valid' if result.get('content_path') else 'invalid',
                        status_code=result.get('status_code'),
                        content_type=result.get('content_type'),
                        source_url=url
                    )
                    self.db.crawled_links.insert_one(link_doc)
                    new_links += 1

            # 统计结果
            total_links = len(results)
            valid_links = len([r for r in results if r.get('content_path')])
            invalid_links = total_links - valid_links

            # 更新任务统计
            self.db.crawl_tasks.update_one(
                {'_id': task_id},
                CrawlTaskModel.update_statistics(
                    total_links=total_links,
                    valid_links=valid_links,
                    invalid_links=invalid_links,
                    new_links=new_links
                )
            )

            # 检查是否被取消（任务可能在保存过程中被取消）
            if app_global.should_stop(task_id):
                self._log(task_id, 'INFO', f'任务已取消 - 已处理: {new_links} 个链接')
                app_global.clear_stop_flag(task_id)
            else:
                # 更新任务状态为 completed
                self.db.crawl_tasks.update_one(
                    {'_id': task_id},
                    CrawlTaskModel.update_status('completed')
                )
                # 记录日志
                self._log(task_id, 'INFO', f'爬取任务完成 - 总链接: {total_links}, 新增: {new_links}')
                # 清除停止标志
                app_global.clear_stop_flag(task_id)

            return {
                'total_links': total_links,
                'valid_links': valid_links,
                'invalid_links': invalid_links,
                'new_links': new_links,
                'valid_rate': valid_rate,
                'precision_rate': precision_rate
            }

        except Exception as e:
            # 更新任务状态为 failed
            self.db.crawl_tasks.update_one(
                {'_id': task_id},
                CrawlTaskModel.update_status('failed', error_message=str(e))
            )

            # 记录错误日志
            self._log(task_id, 'ERROR', f'爬取任务失败: {str(e)}')

            # 清除停止标志
            app_global.clear_stop_flag(task_id)

            raise

    def _log(self, task_id, level, message, details=None):
        """
        记录日志到数据库

        参数:
            task_id: ObjectId - 任务ID
            level: str - 日志级别
            message: str - 日志消息
            details: dict - 详细信息
        """
        try:
            log_doc = CrawlLogModel.create(
                task_id=task_id,
                level=level,
                message=message,
                details=details
            )
            self.db.crawl_logs.insert_one(log_doc)
        except Exception as e:
            print(f"记录日志失败: {str(e)}")
