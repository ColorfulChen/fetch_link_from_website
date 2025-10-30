"""
MongoDB 文档模型定义
"""
from .website import WebsiteModel
from .crawl_task import CrawlTaskModel
from .crawled_link import CrawledLinkModel
from .crawl_log import CrawlLogModel
from .schedule import ScheduleModel

__all__ = [
    'WebsiteModel',
    'CrawlTaskModel',
    'CrawledLinkModel',
    'CrawlLogModel',
    'ScheduleModel'
]
