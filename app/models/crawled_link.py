"""
爬取链接模型
"""
from datetime import datetime
from typing import Optional, Dict, Any
from bson import ObjectId


class CrawledLinkModel:
    """爬取链接模型"""

    COLLECTION_NAME = 'crawled_links'

    @staticmethod
    def create(website_id: ObjectId, task_id: ObjectId, url: str,
               domain: str, link_type: str, status_code: Optional[int] = None,
               content_type: Optional[str] = None, source_url: Optional[str] = None,
               ip_address: Optional[str] = None, importance_score: Optional[float] = None) -> Dict[str, Any]:
        """
        创建爬取链接文档

        Args:
            website_id: 网站ID
            task_id: 任务ID
            url: 链接URL
            domain: 域名
            link_type: 链接类型 (valid/invalid)
            status_code: HTTP状态码
            content_type: 内容类型
            source_url: 来源URL
            ip_address: IP地址
            importance_score: 重要性评分

        Returns:
            链接文档字典
        """
        return {
            'website_id': website_id,
            'task_id': task_id,
            'url': url,
            'domain': domain,
            'link_type': link_type,
            'status_code': status_code,
            'content_type': content_type,
            'ip_address': ip_address,
            'importance_score': importance_score,
            'first_crawled_at': datetime.utcnow(),
            'last_crawled_at': datetime.utcnow(),
            'crawl_count': 1,
            'source_url': source_url
        }

    @staticmethod
    def update_crawl_info() -> Dict[str, Any]:
        """
        更新爬取信息（增量爬取时使用）

        Returns:
            MongoDB 更新操作符字典
        """
        return {
            '$set': {
                'last_crawled_at': datetime.utcnow()
            },
            '$inc': {
                'crawl_count': 1
            }
        }

    @staticmethod
    def to_dict(doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        将 MongoDB 文档转换为字典（用于 API 响应）

        Args:
            doc: MongoDB 文档

        Returns:
            处理后的字典
        """
        if doc is None:
            return None

        doc['id'] = str(doc.pop('_id'))
        doc['website_id'] = str(doc['website_id'])
        doc['task_id'] = str(doc['task_id'])

        if 'first_crawled_at' in doc:
            doc['first_crawled_at'] = doc['first_crawled_at'].isoformat()
        if 'last_crawled_at' in doc:
            doc['last_crawled_at'] = doc['last_crawled_at'].isoformat()

        return doc

    @staticmethod
    def validate(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        验证链接数据

        Args:
            data: 待验证的数据

        Returns:
            (是否有效, 错误消息)
        """
        if not data.get('url'):
            return False, '链接URL不能为空'
        if not data.get('domain'):
            return False, '域名不能为空'
        if data.get('link_type') not in ['valid', 'invalid']:
            return False, '链接类型必须是 valid 或 invalid'

        return True, None
