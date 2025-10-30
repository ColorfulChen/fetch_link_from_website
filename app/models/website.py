"""
网站模型
"""
from datetime import datetime
from typing import Optional, Dict, Any
from bson import ObjectId


class WebsiteModel:
    """网站配置模型"""

    COLLECTION_NAME = 'websites'

    @staticmethod
    def create(name: str, url: str, domain: str,
               crawl_depth: int = 3, max_links: int = 1000) -> Dict[str, Any]:
        """
        创建网站文档

        Args:
            name: 网站名称
            url: 网站URL
            domain: 域名
            crawl_depth: 爬取深度
            max_links: 最大链接数

        Returns:
            网站文档字典
        """
        return {
            'name': name,
            'url': url,
            'domain': domain,
            'status': 'active',
            'crawl_depth': crawl_depth,
            'max_links': max_links,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }

    @staticmethod
    def update(update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成更新文档

        Args:
            update_data: 要更新的字段

        Returns:
            MongoDB 更新操作符字典
        """
        update_data['updated_at'] = datetime.utcnow()
        return {'$set': update_data}

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
        if 'created_at' in doc:
            doc['created_at'] = doc['created_at'].isoformat()
        if 'updated_at' in doc and doc['updated_at']:
            doc['updated_at'] = doc['updated_at'].isoformat()

        return doc

    @staticmethod
    def validate(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        验证网站数据

        Args:
            data: 待验证的数据

        Returns:
            (是否有效, 错误消息)
        """
        if not data.get('name'):
            return False, '网站名称不能为空'
        if not data.get('url'):
            return False, '网站URL不能为空'
        if not data.get('domain'):
            return False, '域名不能为空'

        if 'crawl_depth' in data:
            if not isinstance(data['crawl_depth'], int) or data['crawl_depth'] < 1:
                return False, '爬取深度必须是正整数'

        if 'max_links' in data:
            if not isinstance(data['max_links'], int) or data['max_links'] < 1:
                return False, '最大链接数必须是正整数'

        return True, None
