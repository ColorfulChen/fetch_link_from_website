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
import socket
from datetime import datetime
from bson import ObjectId
from concurrent.futures import ThreadPoolExecutor, as_completed  # 多线程
import random
import json

from app.config import config
import app.global_vars as app_global
from app.database import get_db
from app.models import CrawledLinkModel, CrawlTaskModel, CrawlLogModel
from pymongo.errors import DuplicateKeyError  # 新增：捕获唯一索引冲突


def safe_soup(content, content_type=None):
    """安全的HTML/XML解析，支持智能检测和编码处理"""
    import io
    from contextlib import redirect_stderr

    # 先将 bytes 转换为字符串，避免 lxml 的编码错误
    if isinstance(content, (bytes, bytearray)):
        try:
            # 使用 chardet 检测编码
            detected = chardet.detect(content)
            encoding = detected.get('encoding', 'utf-8')
            confidence = detected.get('confidence', 0)

            # 如果检测置信度太低，使用常见编码尝试
            if confidence < 0.7:
                for enc in ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin1']:
                    try:
                        content = content.decode(enc, errors='ignore')
                        break
                    except:
                        continue
                else:
                    # 所有编码都失败，使用 replace 模式
                    content = content.decode('utf-8', errors='replace')
            else:
                content = content.decode(encoding or 'utf-8', errors='ignore')
        except Exception:
            # 解码失败，使用 replace 模式
            content = content.decode('utf-8', errors='replace')

    # 检测是否是 XML
    is_xml = False
    if content_type:
        ct = content_type.lower()
        if 'xml' in ct or 'xhtml' in ct:
            is_xml = True

    if not is_xml:
        # 通过内容头部检测 XML
        head = content[:200].lstrip() if isinstance(content, str) else ''
        h = head.lower()
        if h.startswith('<?xml') or '<rss' in h or '<feed' in h:
            is_xml = True

    # 抑制 lxml 的编码警告信息
    stderr_buffer = io.StringIO()

    try:
        # 使用对应的解析器，抑制错误输出
        with redirect_stderr(stderr_buffer):
            if is_xml:
                # XML 使用 xml 解析器
                return BeautifulSoup(content, 'xml', from_encoding='utf-8')
            else:
                # HTML 使用 lxml 解析器
                return BeautifulSoup(content, 'lxml', from_encoding='utf-8')
    except Exception:
        # lxml 失败，尝试 html.parser（更宽容）
        try:
            return BeautifulSoup(content, 'html.parser')
        except Exception:
            # 所有解析器都失败
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


# 基于链接特征的轻量级重要性评估
class LinkAnalyzer:
    def __init__(self):
        # 中英关键词混合，适配常见站点导航
        self.important_keywords = [
            '首页', '主页', '产品', '服务', '关于我们', '联系我们',
            '新闻', '博客', '帮助', '支持', '下载', '登录', '注册',
            'home', 'index', 'product', 'service', 'about', 'contact',
            'news', 'blog', 'help', 'support', 'download', 'login',
            'signin', 'signup', 'register'
        ]
        self.ad_keywords = [
            '广告', '推广', '赞助', 'ad', 'ads', 'advertisement',
            'sponsor', 'promotion', 'buy', '购买', '优惠', 'utm', 'banner', 'track'
        ]
        self.suspicious_domains = [
            'ad.', 'ads.', 'doubleclick', 'googlead', 'amazon-adsystem'
        ]


class CriticalLinkDetector:
    def __init__(self):
        self.analyzer = LinkAnalyzer()
        self.importance_threshold = 0.6
        self.target_filter_rate = 0.3

    def calculate_link_importance(self, link_url, base_domain=None, original_domain=None):
        """计算链接重要性得分（0-1） - 基于URL启发式，兼容无DOM环境"""
        url_lower = (link_url or '').lower()
        score = 0.0
        score += self._analyze_text_content(url_lower) * 0.6
        score += self._analyze_position(url_lower) * 0.2
        score += self._analyze_visual_features(url_lower) * 0.2

        domain = re.sub(r'^https?://', '', original_domain)
        domain = re.sub(r'/.*$', '', domain)
        pattern = r'(?:www\.)?([a-zA-Z0-9-]+)\.(?:com|cn|net|org|edu|gov|co\.[a-z]+|[a-z]{2,})'
        match = re.search(pattern, domain)
        
        if match.group(1) in link_url:
            score += 0.4  # 同源域名加分
        else:
            score -= 0.3  # 非同源域名扣分

        return min(max(score, 0.0), 1.0)

    def _analyze_text_content(self, url_text):
        """用URL路径近似替代链接文本分析"""
        from urllib.parse import unquote, urlparse
        try:
            p = urlparse(url_text)
            text = unquote((p.path or '').strip('/').lower())
            text = re.sub(r'[-_/]+', ' ', text)
        except Exception:
            text = url_text or ''

        importance_bonus = 0.0
        for kw in self.analyzer.important_keywords:
            if kw.lower() in text:
                importance_bonus += 0.2

        ad_penalty = 0.0
        for kw in self.analyzer.ad_keywords:
            if kw.lower() in text:
                ad_penalty += 0.3

        length_score = min(len(text) / 20.0, 0.3)  # 最长20字符得0.3分
        base = 0.4 + length_score + importance_bonus - ad_penalty
        return max(0.0, min(base, 1.0))

    def _analyze_position(self, url_text):
        """用路径深度近似位置重要性"""
        from urllib.parse import urlparse
        try:
            p = urlparse(url_text)
            depth = len([seg for seg in (p.path or '').split('/') if seg])
            if depth == 0:
                pos = 0.8
            elif depth <= 2:
                pos = 0.6
            else:
                pos = 0.35
            if re.search(r'\.(js|css|png|jpe?g|gif|svg|ico|pdf|zip)$', p.path or '', re.I):
                pos -= 0.3
            return max(0.0, min(pos, 1.0))
        except Exception:
            return 0.5

    def _analyze_visual_features(self, href):
        """URL中广告/装饰性特征"""
        score = 0.5
        if any(x in href for x in ['ad=', 'ads=', '/ad/', '/ads/', 'banner', 'promo']):
            score -= 0.2
        if any(x in href for x in ['icon', 'sprite', 'small']):
            score -= 0.1
        return max(0.0, min(score, 1.0))



def get_ip_address(domain):
    """
    获取域名的IPv4地址

    参数:
        domain: str - 域名

    返回:
        str - IPv4地址，失败返回 None
    """
    try:
        # 使用 socket.gethostbyname 获取IPv4地址
        ip_address = socket.gethostbyname(domain)
        return ip_address
    except socket.gaierror as e:
        print(f"获取IP地址失败 {domain}: {e}")
        return None
    except Exception as e:
        print(f"获取IP地址异常 {domain}: {e}")
        return None


def screenshot_page(url, save_dir):
    """
    对指定 URL 截图并保存到指定目录

    参数:
        url: str - 需要截图的 URL
        save_dir: str - 截图保存目录

    返回:
        save_path: str - 截图文件相对路径（相对于项目根目录），失败返回 None
    """
    driver = None
    try:
        # 为每次截图创建独立的驱动实例
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.common.exceptions import TimeoutException, WebDriverException
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        # 重试以缓解 renderer 超时
        RETRIES = 2
        last_err = None

        # 生成安全的文件名
        illegal_chars = r'[<>:"/\\|?*\x00-\x1F]'
        fname = "screenshot-" + re.sub(illegal_chars, '', url) + ".png"
        save_path = os.path.join(save_dir, fname)

        for attempt in range(1, RETRIES + 1):
            try:
                opts = Options()
                opts.add_argument('--headless=new')
                opts.add_argument('--disable-gpu')
                opts.add_argument('--no-sandbox')
                opts.add_argument('--disable-dev-shm-usage')
                opts.add_argument('--disable-software-rasterizer')
                opts.add_argument('--window-size=1280,1024')
                opts.add_argument('--disable-extensions')
                opts.add_argument('--disable-logging')
                opts.add_argument('--log-level=3')
                opts.add_argument('--ignore-certificate-errors')
                # 更快返回，减少渲染等待导致的 renderer 超时
                opts.page_load_strategy = 'eager'

                driver = webdriver.Chrome(options=opts)
                driver.set_page_load_timeout(15)
                driver.set_script_timeout(15)

                # 访问页面
                try:
                    driver.get(url)
                except TimeoutException:
                    # 停止继续加载，尽量使用当前已渲染内容
                    try:
                        driver.execute_script("window.stop();")
                    except Exception:
                        pass

                # 等待 DOM 就绪或至少有 <body>
                try:
                    WebDriverWait(driver, 8).until(
                        lambda d: d.execute_script("return document.readyState") in ("interactive", "complete")
                    )
                except Exception:
                    # 退而求其次，等待 body 元素出现
                    try:
                        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                    except Exception:
                        pass

                # 轻微等待以稳定首屏
                import time
                time.sleep(0.5)

                # 保存截图
                driver.save_screenshot(save_path)
                print(f"网页截图已保存: {save_path}")

                # 返回相对于项目根目录的相对路径
                project_root = os.getcwd()
                relative_path = os.path.relpath(save_path, project_root)
                return relative_path

            except (TimeoutException, WebDriverException, Exception) as e:
                last_err = e
                print(f"第 {attempt}/{RETRIES} 次截图尝试失败: {e}")
            finally:
                if driver:
                    try:
                        driver.quit()
                    except Exception:
                        pass
                    driver = None

        # 所有重试失败
        print(f"截图失败 {url}: {last_err}")
        return None

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

    # 检查内容类型，跳过二进制文件
    content_type = response.headers.get('Content-Type', '').lower()
    binary_types = [
        'image/', 'video/', 'audio/', 'application/pdf',
        'application/zip', 'application/x-rar', 'application/octet-stream',
        'font/', 'application/x-font', 'application/vnd.ms-fontobject'
    ]
    if any(bt in content_type for bt in binary_types):
        print(f"跳过二进制文件: {url} (Content-Type: {content_type})")
        return []

    # 只解析 HTML/XML 类型的内容
    parseable_types = ['text/html', 'application/xhtml', 'text/xml', 'application/xml', 'application/rss', 'application/atom']
    if content_type and not any(pt in content_type for pt in parseable_types):
        # 如果有明确的 Content-Type 但不是可解析类型，跳过
        if 'text/' not in content_type and 'application/' in content_type:
            print(f"跳过不可解析的内容: {url} (Content-Type: {content_type})")
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


def crawler_link(url, depth=3, exclude=None, original_domain=None, threads=10):
    """
    爬虫主函数 - API调用入口（支持增量爬取，链接处理多线程）

    参数:
        url: str - 需要爬虫的 url 链接
        depth: int - 爬虫的深度
        exclude: list[str] - 需要排除的 url (用于增量更新策略)
        threads: int - 并发线程数
    返回:
        tuple: (results, valid_rate, precision_rate, screenshot_path)
        - results: list[dict] - [{'link': str, 'content_path': str}, ...]
        - valid_rate: float - 有效率
        - precision_rate: float - 精准率
        - screenshot_path: str - 截图路径
    """
    # 获取所有链接
    print(f"开始爬取: {url}, 深度: {depth}")

    # 创建保存目录（使用 UUID 生成唯一目录名）
    domain = urlparse(url).netloc
    unique_id = str(uuid.uuid4())
    save_dir = os.path.join(config.save_path, f"{domain}_{unique_id}")
    os.makedirs(save_dir, exist_ok=True)
    print(f"保存目录: {save_dir}")

    # 初始化链接重要性检测器
    detector = CriticalLinkDetector()
    base_domain = domain

    # 对入口页面进行截图
    screenshot_path = None
    try:
        screenshot_path = screenshot_page(url, save_dir)
    except Exception as e:
        print(f"入口页面截图失败 {url}: {e}")

    # 转换 exclude 为 set 以提高查找效率
    exclude_set = set(exclude) if exclude else set()

    # 调用 get_all_links 获取所有链接（已自动排除 exclude 中的链接）
    all_links = get_all_links(url, depth, exclude=exclude_set)

    # 去重
    unique_links = list(set(all_links))
    print(f"总共爬取到 {len(unique_links)} 个唯一链接（已排除 {len(exclude_set)} 个已存在链接）")

    illegal_chars = r'[<>:"/\\|?*\x00-\x1F]'

    # 多线程处理每个链接
    results = []

    def process_link(link: str):
        print(f"处理链接: {link}")
        link_domain = urlparse(link).netloc
        ip_address = get_ip_address(link_domain)
        importance_score = detector.calculate_link_importance(link, base_domain=base_domain, original_domain=original_domain)

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        response = safe_request(link, headers)

        if response:
            filename = re.sub(illegal_chars, '', link)
            if len(filename) > 200:
                filename = filename[:200]
            save_path = os.path.join(save_dir, filename)
            return {
                'link': link,
                'content_path': save_path,
                'status_code': response.status_code,
                'content_type': response.headers.get('Content-Type', ''),
                'ip_address': ip_address,
                'importance_score': round(importance_score, 4)
            }
        else:
            return {
                'link': link,
                'content_path': None,
                'status_code': None,
                'content_type': '',
                'ip_address': ip_address,
                'importance_score': round(importance_score, 4)
            }

    with ThreadPoolExecutor(max_workers=max(1, int(threads))) as executor:
        for res in executor.map(process_link, unique_links):
            results.append(res)

    # 计算指标
    total_links = len(results)
    valid_links_count = 0
    invalid_links_count = 0
    err_link = 0

    for r in results:
        if r.get('importance_score'):
            valid_links_count += 1
            if r.get('importance_score') < 0.8:
                invalid_links_count += 1
                r['link_type'] = 'invalid'
            else:
                # 仅当域名在 domain.json 中时才计入 err_link
                domain = r.get('url', '')
                # if domain and domain in domain_set:
                if 'ad' in domain.lower() or 'ads' in domain.lower():
                    err_link += 1
    # valid_links = len([r for r in results if r.get('content_path')])
    # invalid_links = total_links - valid_links
    valid_rate = round(((valid_links_count - invalid_links_count) / valid_links_count), 4) if valid_links_count else 1.0
    precision_rate = round(1 - (err_link / invalid_links_count), 4) if invalid_links_count else 1.0

    print(f"\n=== 爬取完成 ===")
    print(f"有效链接: {valid_links_count}")
    print(f"无效链接: {invalid_links_count}")
    print(f"Valid Rate: {valid_rate:.2%}")
    print(f"Precision Rate: {precision_rate:.2%}")

    return results, valid_rate, precision_rate, screenshot_path, valid_links_count, invalid_links_count


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
            original_domain = website['domain']

            if not website:
                raise Exception(f"网站不存在: {website_id}")

            url = website['url']

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
            results, valid_rate, precision_rate, screenshot_path,valid_links,invalid_links = crawler_link(url, depth, exclude_urls, original_domain)
            total_links = len(results)

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

                # 准备待插入文档
                link_doc = CrawledLinkModel.create(
                    website_id=website_id,
                    task_id=task_id,
                    url=link_url,
                    domain=urlparse(link_url).netloc,
                    link_type='valid' if result.get('content_path') else 'invalid',
                    status_code=result.get('status_code'),
                    content_type=result.get('content_type'),
                    source_url=url,
                    ip_address=result.get('ip_address'),
                    importance_score=result.get('importance_score')
                )

                # 若存在相同链接：删除旧数据后插入新数据
                existing_link = self.db.crawled_links.find_one({
                    'website_id': website_id,
                    'url': link_url
                })
                if existing_link:
                    self.db.crawled_links.delete_one({'_id': existing_link['_id']})
                    try:
                        self.db.crawled_links.insert_one(link_doc)
                    except DuplicateKeyError:
                        # 并发竞争导致再次重复：强制清理后重插一次
                        self.db.crawled_links.delete_many({'website_id': website_id, 'url': link_url})
                        self.db.crawled_links.insert_one(link_doc)
                    # 覆盖不计入 new_links
                else:
                    # 不存在则直接插入；若并发下重复，则按规则删除后重插
                    try:
                        self.db.crawled_links.insert_one(link_doc)
                        new_links += 1
                    except DuplicateKeyError:
                        self.db.crawled_links.delete_many({'website_id': website_id, 'url': link_url})
                        self.db.crawled_links.insert_one(link_doc)
                        # 并发覆盖不计入 new_links


            # 更新任务统计和截图路径
            update_data = CrawlTaskModel.update_statistics(
                total_links=total_links+invalid_links,
                valid_links=valid_links,
                invalid_links=invalid_links,
                new_links=new_links,
                valid_rate = valid_rate,
                precision_rate = precision_rate,
            )
            # 添加截图路径
            if screenshot_path:
                update_data['$set']['screenshot_path'] = screenshot_path

            self.db.crawl_tasks.update_one(
                {'_id': task_id},
                update_data
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
