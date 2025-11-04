"""
任务管理 API
"""
from flask import request
from bson import ObjectId
from bson.errors import InvalidId
import threading

from . import tasks_bp
from ..database import get_db
from ..models import CrawlTaskModel
from ..utils import success_response, error_response, paginate_response
from ..services.crawler_service import CrawlerService


def run_crawler_task(task_id, website_id, strategy, depth, max_links):
    """在后台线程中运行爬虫任务"""
    try:
        crawler = CrawlerService()
        crawler.crawl(task_id, website_id, strategy, depth, max_links)
    except Exception as e:
        print(f"爬虫任务执行失败: {str(e)}")


@tasks_bp.route('/crawl', methods=['POST'])
def create_crawl_task():
    """手动启动爬取任务"""
    try:
        data = request.get_json()

        # 验证必填字段
        if not data.get('website_id'):
            return error_response('网站ID不能为空')
        if not data.get('strategy'):
            return error_response('爬取策略不能为空')
        if data['strategy'] not in ['incremental', 'full']:
            return error_response('策略必须是 incremental 或 full')

        db = get_db()
        website_id = ObjectId(data['website_id'])

        # 检查网站是否存在
        website = db.websites.find_one({'_id': website_id})
        if not website:
            return error_response('网站不存在', 404)

        # 检查是否有正在运行的任务
        running_task = db.crawl_tasks.find_one({
            'website_id': website_id,
            'status': 'running'
        })
        if running_task:
            return error_response('该网站已有正在运行的任务', 409)

        # 创建任务文档
        task_doc = CrawlTaskModel.create(
            website_id=website_id,
            strategy=data['strategy'],
            task_type='manual'
        )

        # 插入数据库
        result = db.crawl_tasks.insert_one(task_doc)
        task_id = result.inserted_id
        task_doc['_id'] = task_id

        # 获取爬取参数
        depth = data.get('depth', website.get('crawl_depth', 3))
        max_links = data.get('max_links', website.get('max_links', 1000))

        # 在后台线程中启动爬取任务
        thread = threading.Thread(
            target=run_crawler_task,
            args=(task_id, website_id, data['strategy'], depth, max_links)
        )
        thread.daemon = True
        thread.start()

        return success_response(
            CrawlTaskModel.to_dict(task_doc),
            '爬取任务已创建并开始执行',
            202
        )

    except InvalidId:
        return error_response('网站ID格式无效', 400)
    except Exception as e:
        return error_response(f'创建爬取任务失败: {str(e)}', 500)


@tasks_bp.route('', methods=['GET'])
def get_tasks():
    """获取任务列表"""
    try:
        # 获取查询参数
        website_id = request.args.get('website_id', None)
        status = request.args.get('status', None)
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))

        # 构建查询条件
        query = {}
        if website_id:
            query['website_id'] = ObjectId(website_id)
        if status:
            query['status'] = status

        # 查询数据库
        db = get_db()
        total = db.crawl_tasks.count_documents(query)
        skip = (page - 1) * page_size

        tasks = list(db.crawl_tasks.find(query)
                    .sort('started_at', -1)
                    .skip(skip)
                    .limit(page_size))

        # 转换为字典
        tasks_list = [CrawlTaskModel.to_dict(t) for t in tasks]

        # 为每个任务添加网站信息
        from ..models import WebsiteModel
        for task in tasks_list:
            website = db.websites.find_one({'_id': ObjectId(task['website_id'])})
            if website:
                task['website'] = WebsiteModel.to_dict(website)
            else:
                task['website'] = None

        return paginate_response(tasks_list, total, page, page_size)

    except Exception as e:
        return error_response(f'获取任务列表失败: {str(e)}', 500)


@tasks_bp.route('/<task_id>', methods=['GET'])
def get_task(task_id):
    """获取任务详情"""
    try:
        db = get_db()
        task = db.crawl_tasks.find_one({'_id': ObjectId(task_id)})

        if not task:
            return error_response('任务不存在', 404)

        task_dict = CrawlTaskModel.to_dict(task)
        
        # 添加网站信息
        from ..models import WebsiteModel
        website = db.websites.find_one({'_id': ObjectId(task['website_id'])})
        if website:
            task_dict['website'] = WebsiteModel.to_dict(website)
        else:
            task_dict['website'] = None

        return success_response(task_dict)

    except InvalidId:
        return error_response('任务ID格式无效', 400)
    except Exception as e:
        return error_response(f'获取任务详情失败: {str(e)}', 500)


@tasks_bp.route('/<task_id>/logs', methods=['GET'])
def get_task_logs(task_id):
    """获取任务日志"""
    try:
        level = request.args.get('level', None)
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 50))

        # 构建查询条件
        query = {'task_id': ObjectId(task_id)}
        if level:
            query['level'] = level.upper()

        # 查询数据库
        db = get_db()
        total = db.crawl_logs.count_documents(query)
        skip = (page - 1) * page_size

        logs = list(db.crawl_logs.find(query)
                   .sort('created_at', -1)
                   .skip(skip)
                   .limit(page_size))

        # 转换为字典
        from ..models import CrawlLogModel
        logs_list = [CrawlLogModel.to_dict(log) for log in logs]

        return paginate_response(logs_list, total, page, page_size)

    except InvalidId:
        return error_response('任务ID格式无效', 400)
    except Exception as e:
        return error_response(f'获取任务日志失败: {str(e)}', 500)


@tasks_bp.route('/<task_id>/cancel', methods=['POST'])
def cancel_task(task_id):
    """强制取消运行中的任务"""
    try:
        db = get_db()
        task = db.crawl_tasks.find_one({'_id': ObjectId(task_id)})

        if not task:
            return error_response('任务不存在', 404)

        # 只能取消运行中的任务
        if task['status'] != 'running':
            return error_response(f'只能取消运行中的任务，当前状态: {task["status"]}', 400)

        # 设置停止标志（通知后台任务停止）
        from ..global_vars import set_stop_flag
        set_stop_flag(task_id)

        # 立即将任务状态改为 cancelled（强制取消）
        db.crawl_tasks.update_one(
            {'_id': ObjectId(task_id)},
            CrawlTaskModel.update_status('cancelled')
        )

        return success_response(
            {'task_id': task_id, 'status': 'cancelled'},
            '任务已强制取消'
        )

    except InvalidId:
        return error_response('任务ID格式无效', 400)
    except Exception as e:
        return error_response(f'取消任务失败: {str(e)}', 500)


@tasks_bp.route('/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """删除任务及相关数据"""
    try:
        db = get_db()
        task = db.crawl_tasks.find_one({'_id': ObjectId(task_id)})

        if not task:
            return error_response('任务不存在', 404)

        # 不允许删除运行中的任务
        if task['status'] == 'running':
            return error_response('不能删除运行中的任务，请先取消任务', 409)

        # 删除任务相关的日志
        db.crawl_logs.delete_many({'task_id': ObjectId(task_id)})

        # 删除任务
        db.crawl_tasks.delete_one({'_id': ObjectId(task_id)})

        return success_response(
            {'task_id': task_id},
            '任务及相关数据已删除'
        )

    except InvalidId:
        return error_response('任务ID格式无效', 400)
    except Exception as e:
        return error_response(f'删除任务失败: {str(e)}', 500)
