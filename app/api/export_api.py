"""
数据导出 API
"""
from flask import request, send_file
from bson import ObjectId
from bson.errors import InvalidId
import csv
import json
import os
from datetime import datetime

from . import export_bp
from ..database import get_db
from ..utils import success_response, error_response
from ..utils.validators import parse_iso_datetime


@export_bp.route('', methods=['POST'])
def export_data():
    """导出爬取数据"""
    try:
        data = request.get_json()

        # 验证必填字段
        if not data.get('website_id'):
            return error_response('网站ID不能为空')
        if not data.get('export_type'):
            return error_response('导出类型不能为空')
        if data['export_type'] not in ['incremental', 'full']:
            return error_response('导出类型必须是 incremental 或 full')

        format_type = data.get('format', 'csv')
        if format_type not in ['csv', 'json']:
            return error_response('导出格式必须是 csv 或 json')

        db = get_db()
        website_id = ObjectId(data['website_id'])

        # 构建查询条件
        query = {'website_id': website_id}

        # 增量导出
        if data['export_type'] == 'incremental' and data.get('since_date'):
            try:
                since_date = parse_iso_datetime(data['since_date'])
            except ValueError:
                return error_response('since_date 格式无效，应为 ISO-8601 日期时间字符串', 400)
            query['first_crawled_at'] = {'$gt': since_date}

        # 过滤条件
        filters = data.get('filters', {})
        if filters.get('link_type'):
            query['link_type'] = filters['link_type']
        if filters.get('domain'):
            query['domain'] = filters['domain']

        # 查询数据
        links = list(db.crawled_links.find(query))
        total_records = len(links)

        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"export_{website_id}_{timestamp}.{format_type}"
        export_dir = 'exports'
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
        filepath = os.path.join(export_dir, filename)

        # 导出数据
        if format_type == 'csv':
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                if links:
                    writer = csv.DictWriter(
                        f, fieldnames=['url', 'domain', 'ip_address', 'link_type', 'status_code', 'last_crawled_at'])
                    writer.writeheader()
                    for link in links:
                        writer.writerow({
                            'url': link['url'],
                            'domain': link['domain'],
                            'ip_address': link.get('ip_address', ''),
                            'link_type': link['link_type'],
                            'status_code': link.get('status_code', ''),
                            'last_crawled_at': link['last_crawled_at'].isoformat() if link.get('last_crawled_at') else ''
                        })
        else:  # json
            # 转换 ObjectId 和 datetime
            for link in links:
                link['_id'] = str(link['_id'])
                link['website_id'] = str(link['website_id'])
                link['task_id'] = str(link['task_id'])
                if link.get('first_crawled_at'):
                    link['first_crawled_at'] = link['first_crawled_at'].isoformat()
                if link.get('last_crawled_at'):
                    link['last_crawled_at'] = link['last_crawled_at'].isoformat()

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(links, f, ensure_ascii=False, indent=2)

        # 获取文件大小
        file_size = os.path.getsize(filepath)
        file_size_str = f"{file_size / 1024:.2f} KB" if file_size < 1024 * \
            1024 else f"{file_size / (1024 * 1024):.2f} MB"

        return success_response({
            'download_url': f'/api/export/download/{filename}',
            'file_name': filename,
            'total_records': total_records,
            'file_size': file_size_str
        }, '数据导出成功')

    except InvalidId:
        return error_response('网站ID格式无效', 400)
    except Exception as e:
        return error_response(f'导出数据失败: {str(e)}', 500)


@export_bp.route('/batch', methods=['POST'])
def batch_export_data():
    """批量导出爬取数据"""
    try:
        data = request.get_json()

        # 验证必填字段
        if not data.get('website_ids'):
            return error_response('网站ID列表不能为空')
        if not isinstance(data['website_ids'], list):
            return error_response('website_ids 必须是数组')

        export_type = data.get('export_type', 'full')
        if export_type not in ['incremental', 'full']:
            return error_response('导出类型必须是 incremental 或 full')

        format_type = data.get('format', 'csv')
        if format_type not in ['csv', 'json']:
            return error_response('导出格式必须是 csv 或 json')

        db = get_db()
        website_ids = [ObjectId(wid) for wid in data['website_ids']]

        # 构建查询条件
        query = {'website_id': {'$in': website_ids}}

        # 增量导出
        if export_type == 'incremental' and data.get('since_date'):
            try:
                since_date = parse_iso_datetime(data['since_date'])
            except ValueError:
                return error_response('since_date 格式无效，应为 ISO-8601 日期时间字符串', 400)
            query['first_crawled_at'] = {'$gt': since_date}

        # 过滤条件
        filters = data.get('filters', {})
        if filters.get('link_type'):
            query['link_type'] = filters['link_type']
        if filters.get('domain'):
            query['domain'] = filters['domain']

        # 查询数据
        links = list(db.crawled_links.find(query))
        total_records = len(links)

        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"batch_export_{timestamp}.{format_type}"
        export_dir = 'exports'
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
        filepath = os.path.join(export_dir, filename)

        # 导出数据
        if format_type == 'csv':
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                if links:
                    writer = csv.DictWriter(
                        f, fieldnames=['url', 'domain', 'ip_address', 'link_type', 'status_code', 'last_crawled_at', 'website_id'])
                    writer.writeheader()
                    for link in links:
                        writer.writerow({
                            'url': link['url'],
                            'domain': link['domain'],
                            'ip_address': link.get('ip_address', ''),
                            'link_type': link['link_type'],
                            'status_code': link.get('status_code', ''),
                            'last_crawled_at': link['last_crawled_at'].isoformat() if link.get('last_crawled_at') else '',
                            'website_id': str(link['website_id'])
                        })
        else:  # json
            # 转换 ObjectId 和 datetime
            for link in links:
                link['_id'] = str(link['_id'])
                link['website_id'] = str(link['website_id'])
                link['task_id'] = str(link['task_id'])
                if link.get('first_crawled_at'):
                    link['first_crawled_at'] = link['first_crawled_at'].isoformat()
                if link.get('last_crawled_at'):
                    link['last_crawled_at'] = link['last_crawled_at'].isoformat()

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(links, f, ensure_ascii=False, indent=2)

        # 获取文件大小
        file_size = os.path.getsize(filepath)
        file_size_str = f"{file_size / 1024:.2f} KB" if file_size < 1024 * \
            1024 else f"{file_size / (1024 * 1024):.2f} MB"

        return success_response({
            'download_url': f'/api/export/download/{filename}',
            'file_name': filename,
            'total_records': total_records,
            'file_size': file_size_str,
            'website_count': len(website_ids)
        }, '批量数据导出成功')

    except InvalidId:
        return error_response('网站ID格式无效', 400)
    except Exception as e:
        return error_response(f'批量导出数据失败: {str(e)}', 500)


@export_bp.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """下载导出文件"""
    try:
        filepath = os.path.join(os.getcwd(), 'exports', filename)
        print(filepath)
        if not os.path.exists(filepath):
            return error_response('文件不存在', 404)

        return send_file(filepath, as_attachment=True, download_name=filename)

    except Exception as e:
        return error_response(f'下载文件失败: {str(e)}', 500)
