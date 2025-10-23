"""
调度配置模型
"""
from datetime import datetime
from typing import Optional, Dict, Any
from bson import ObjectId


class ScheduleModel:
    """调度配置模型"""

    COLLECTION_NAME = 'schedules'

    @staticmethod
    def create(website_id: ObjectId, name: str, schedule_type: str,
               cron_expression: str, strategy: str = 'incremental') -> Dict[str, Any]:
        """
        创建调度配置文档

        Args:
            website_id: 网站ID
            name: 调度名称
            schedule_type: 调度类型 (hourly/daily/monthly)
            cron_expression: Cron表达式
            strategy: 爬取策略 (incremental/full)

        Returns:
            调度配置文档字典
        """
        return {
            'website_id': website_id,
            'name': name,
            'schedule_type': schedule_type,
            'cron_expression': cron_expression,
            'strategy': strategy,
            'is_active': True,
            'next_run_time': None,
            'last_run_time': None,
            'created_at': datetime.utcnow()
        }

    @staticmethod
    def update_run_time(next_run_time: Optional[datetime] = None,
                       last_run_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        更新运行时间

        Args:
            next_run_time: 下次运行时间
            last_run_time: 上次运行时间

        Returns:
            MongoDB 更新操作符字典
        """
        update_data = {}
        if next_run_time is not None:
            update_data['next_run_time'] = next_run_time
        if last_run_time is not None:
            update_data['last_run_time'] = last_run_time

        return {'$set': update_data}

    @staticmethod
    def toggle_active(is_active: bool) -> Dict[str, Any]:
        """
        切换激活状态

        Args:
            is_active: 是否激活

        Returns:
            MongoDB 更新操作符字典
        """
        return {'$set': {'is_active': is_active}}

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

        if 'next_run_time' in doc and doc['next_run_time']:
            doc['next_run_time'] = doc['next_run_time'].isoformat()
        if 'last_run_time' in doc and doc['last_run_time']:
            doc['last_run_time'] = doc['last_run_time'].isoformat()
        if 'created_at' in doc:
            doc['created_at'] = doc['created_at'].isoformat()

        return doc

    @staticmethod
    def validate(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        验证调度配置数据

        Args:
            data: 待验证的数据

        Returns:
            (是否有效, 错误消息)
        """
        if not data.get('website_id'):
            return False, '网站ID不能为空'
        if not data.get('name'):
            return False, '调度名称不能为空'
        if data.get('schedule_type') not in ['hourly', 'daily', 'monthly']:
            return False, '调度类型必须是 hourly、daily 或 monthly'
        if data.get('strategy') not in ['incremental', 'full']:
            return False, '策略必须是 incremental 或 full'

        return True, None
