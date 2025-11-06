"""
统计数据 API
"""
from flask import request
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime

from . import statistics_bp
from ..database import get_db
from ..utils import success_response, error_response


@statistics_bp.route('', methods=['GET'])
def get_statistics():
    """获取统计数据"""
    try:
        website_id = request.args.get('website_id', None)
        date_from = request.args.get('date_from', None)
        date_to = request.args.get('date_to', None)

        if not website_id:
            return error_response('网站ID不能为空')

        db = get_db()
        website_obj_id = ObjectId(website_id)

        # 检查网站是否存在
        website = db.websites.find_one({'_id': website_obj_id})
        if not website:
            return error_response('网站不存在', 404)

        # 构建查询条件
        query = {'website_id': website_obj_id}
        if date_from and date_to:
            query['started_at'] = {
                '$gte': datetime.fromisoformat(date_from),
                '$lte': datetime.fromisoformat(date_to)
            }

        # 统计任务数据
        tasks = list(db.crawl_tasks.find(query))
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t['status'] == 'completed'])
        failed_tasks = len([t for t in tasks if t['status'] == 'failed'])

        # 计算链接统计
        total_links_crawled = sum(t['statistics']['total_links'] for t in tasks)
        new_links_found = sum(t['statistics']['new_links'] for t in tasks)

        # 计算平均有效率和精准率
        avg_valid_rate = 0
        avg_precision_rate = 0
        if completed_tasks > 0:
            valid_rates = [t['statistics']['valid_rate'] for t in tasks if t['status'] == 'completed']
            precision_rates = [t['statistics']['precision_rate'] for t in tasks if t['status'] == 'completed']
            avg_valid_rate = sum(valid_rates) / len(valid_rates) if valid_rates else 0
            avg_precision_rate = sum(precision_rates) / len(precision_rates) if precision_rates else 0

        # 构建响应数据
        response_data = {
            'website': {
                'id': str(website['_id']),
                'name': website['name']
            },
            'period': {
                'from': date_from,
                'to': date_to
            },
            'summary': {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'failed_tasks': failed_tasks,
                'total_links_crawled': total_links_crawled,
                'new_links_found': new_links_found,
                'avg_valid_rate': round(avg_valid_rate, 4),
                'avg_precision_rate': round(avg_precision_rate, 4)
            }
        }

        return success_response(response_data)

    except InvalidId:
        return error_response('网站ID格式无效', 400)
    except Exception as e:
        return error_response(f'获取统计数据失败: {str(e)}', 500)


@statistics_bp.route('/all', methods=['GET'])
def get_all_statistics():
    """获取所有网站的平均统计数据"""
    try:
        date_from = request.args.get('date_from', None)
        date_to = request.args.get('date_to', None)

        db = get_db()

        # 构建查询条件
        query = {}
        if date_from and date_to:
            query['started_at'] = {
                '$gte': datetime.fromisoformat(date_from),
                '$lte': datetime.fromisoformat(date_to)
            }

        # 统计所有任务数据
        tasks = list(db.crawl_tasks.find(query))
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t['status'] == 'completed'])
        failed_tasks = len([t for t in tasks if t['status'] == 'failed'])

        # 计算链接统计
        total_links_crawled = sum(t['statistics']['total_links'] for t in tasks)
        new_links_found = sum(t['statistics']['new_links'] for t in tasks)

        # 计算平均有效率和精准率
        avg_valid_rate = 0
        avg_precision_rate = 0
        if completed_tasks > 0:
            valid_rates = [t['statistics']['valid_rate'] for t in tasks if t['status'] == 'completed']
            precision_rates = [t['statistics']['precision_rate'] for t in tasks if t['status'] == 'completed']
            avg_valid_rate = sum(valid_rates) / len(valid_rates) if valid_rates else 0
            avg_precision_rate = sum(precision_rates) / len(precision_rates) if precision_rates else 0

        # 构建响应数据
        response_data = {
            'period': {
                'from': date_from,
                'to': date_to
            },
            'summary': {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'failed_tasks': failed_tasks,
                'total_links_crawled': total_links_crawled,
                'new_links_found': new_links_found,
                'avg_valid_rate': round(avg_valid_rate, 4),
                'avg_precision_rate': round(avg_precision_rate, 4)
            }
        }

        return success_response(response_data)

    except Exception as e:
        return error_response(f'获取统计数据失败: {str(e)}', 500)
