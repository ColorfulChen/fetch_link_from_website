"""
爬取任务模型
"""
from datetime import datetime
from typing import Optional, Dict, Any
from bson import ObjectId


class CrawlTaskModel:
    """爬取任务模型"""

    COLLECTION_NAME = 'crawl_tasks'

    @staticmethod
    def create(website_id: ObjectId, strategy: str,
               task_type: str = 'manual') -> Dict[str, Any]:
        """
        创建爬取任务文档

        Args:
            website_id: 网站ID
            strategy: 爬取策略 (incremental/full)
            task_type: 任务类型 (scheduled/manual)

        Returns:
            任务文档字典
        """
        return {
            'website_id': website_id,
            'task_type': task_type,
            'strategy': strategy,
            'status': 'pending',
            'started_at': None,
            'completed_at': None,
            'statistics': {
                'total_links': 0,
                'valid_links': 0,
                'invalid_links': 0,
                'new_links': 0,
                'valid_rate': 0.0,
                'precision_rate': 0.0
            },
            'screenshot_path': None,
            'error_message': None
        }

    @staticmethod
    def update_status(status: str, **kwargs) -> Dict[str, Any]:
        """
        更新任务状态

        Args:
            status: 任务状态 (pending/running/completed/failed/cancelled)
            **kwargs: 其他要更新的字段

        Returns:
            MongoDB 更新操作符字典
        """
        update_data = {'status': status}

        if status == 'running':
            update_data['started_at'] = datetime.utcnow()
        elif status in ['completed', 'failed', 'cancelled']:
            update_data['completed_at'] = datetime.utcnow()

        update_data.update(kwargs)
        return {'$set': update_data}

    @staticmethod
    def update_statistics(total_links: int, valid_links: int,
                         invalid_links: int, new_links: int = 0, valid_rate: float = 0.0, precision_rate: float = 0.0) -> Dict[str, Any]:
        """
        更新任务统计信息

        Args:
            total_links: 总链接数
            valid_links: 有效链接数
            invalid_links: 无效链接数
            new_links: 新增链接数

        Returns:
            MongoDB 更新操作符字典
        """
        # valid_rate = valid_links / total_links if total_links > 0 else 0
        # precision_rate = valid_links / (valid_links + invalid_links) if (valid_links + invalid_links) > 0 else 0

        return {
            '$set': {
                'statistics': {
                    'total_links': total_links,
                    'valid_links': valid_links,
                    'invalid_links': invalid_links,
                    'new_links': new_links,
                    'valid_rate': round(valid_rate, 4),
                    'precision_rate': round(precision_rate, 4)
                }
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

        if 'started_at' in doc and doc['started_at']:
            doc['started_at'] = doc['started_at'].isoformat()
        if 'completed_at' in doc and doc['completed_at']:
            doc['completed_at'] = doc['completed_at'].isoformat()

        return doc

    @staticmethod
    def validate(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        验证任务数据

        Args:
            data: 待验证的数据

        Returns:
            (是否有效, 错误消息)
        """
        if not data.get('website_id'):
            return False, '网站ID不能为空'

        if data.get('strategy') not in ['incremental', 'full']:
            return False, '策略必须是 incremental 或 full'

        if data.get('task_type') not in ['scheduled', 'manual']:
            return False, '任务类型必须是 scheduled 或 manual'

        return True, None
