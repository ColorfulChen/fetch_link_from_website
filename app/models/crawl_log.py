"""
爬取日志模型
"""
from datetime import datetime
from typing import Optional, Dict, Any
from bson import ObjectId


class CrawlLogModel:
    """爬取日志模型"""

    COLLECTION_NAME = 'crawl_logs'

    @staticmethod
    def create(task_id: ObjectId, level: str, message: str,
               details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        创建日志文档

        Args:
            task_id: 任务ID
            level: 日志级别 (INFO/WARNING/ERROR)
            message: 日志消息
            details: 详细信息

        Returns:
            日志文档字典
        """
        return {
            'task_id': task_id,
            'level': level,
            'message': message,
            'details': details or {},
            'created_at': datetime.utcnow()
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
        doc['task_id'] = str(doc['task_id'])

        if 'created_at' in doc:
            doc['created_at'] = doc['created_at'].isoformat()

        return doc

    @staticmethod
    def validate(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        验证日志数据

        Args:
            data: 待验证的数据

        Returns:
            (是否有效, 错误消息)
        """
        if not data.get('task_id'):
            return False, '任务ID不能为空'
        if not data.get('message'):
            return False, '日志消息不能为空'
        if data.get('level') not in ['INFO', 'WARNING', 'ERROR']:
            return False, '日志级别必须是 INFO、WARNING 或 ERROR'

        return True, None
