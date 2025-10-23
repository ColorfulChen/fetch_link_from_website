"""
API 路由模块
"""
from flask import Blueprint

# 创建蓝图
websites_bp = Blueprint('websites', __name__, url_prefix='/api/websites')
tasks_bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')
schedules_bp = Blueprint('schedules', __name__, url_prefix='/api/schedules')
export_bp = Blueprint('export', __name__, url_prefix='/api/export')
statistics_bp = Blueprint('statistics', __name__, url_prefix='/api/statistics')

# 导入路由（避免循环导入）
from . import websites, tasks, schedules, export_api, statistics

__all__ = [
    'websites_bp',
    'tasks_bp',
    'schedules_bp',
    'export_bp',
    'statistics_bp'
]
