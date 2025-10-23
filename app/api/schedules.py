"""
调度管理 API
"""
from flask import request
from bson import ObjectId
from bson.errors import InvalidId

from . import schedules_bp
from ..database import get_db
from ..models import ScheduleModel
from ..utils import success_response, error_response


@schedules_bp.route('', methods=['POST'])
def create_schedule():
    """创建调度任务"""
    try:
        data = request.get_json()

        # 验证必填字段
        if not data.get('website_id'):
            return error_response('网站ID不能为空')
        if not data.get('name'):
            return error_response('调度名称不能为空')
        if not data.get('schedule_type'):
            return error_response('调度类型不能为空')

        is_valid, msg = ScheduleModel.validate(data)
        if not is_valid:
            return error_response(msg)

        db = get_db()
        website_id = ObjectId(data['website_id'])

        # 检查网站是否存在
        website = db.websites.find_one({'_id': website_id})
        if not website:
            return error_response('网站不存在', 404)

        # 生成 cron 表达式（简化版）
        cron_expression = '0 * * * *'  # 默认每小时
        if data['schedule_type'] == 'daily':
            hour = data.get('hour', 2)
            cron_expression = f"0 {hour} * * *"
        elif data['schedule_type'] == 'monthly':
            hour = data.get('hour', 0)
            day = data.get('day', 1)
            cron_expression = f"0 {hour} {day} * *"

        # 创建调度文档
        schedule_doc = ScheduleModel.create(
            website_id=website_id,
            name=data['name'],
            schedule_type=data['schedule_type'],
            cron_expression=cron_expression,
            strategy=data.get('strategy', 'incremental')
        )

        # 插入数据库
        result = db.schedules.insert_one(schedule_doc)
        schedule_doc['_id'] = result.inserted_id

        return success_response(
            ScheduleModel.to_dict(schedule_doc),
            '调度任务创建成功',
            201
        )

    except InvalidId:
        return error_response('网站ID格式无效', 400)
    except Exception as e:
        return error_response(f'创建调度任务失败: {str(e)}', 500)


@schedules_bp.route('', methods=['GET'])
def get_schedules():
    """获取调度列表"""
    try:
        website_id = request.args.get('website_id', None)

        # 构建查询条件
        query = {}
        if website_id:
            query['website_id'] = ObjectId(website_id)

        # 查询数据库
        db = get_db()
        schedules = list(db.schedules.find(query).sort('created_at', -1))

        # 转换为字典
        schedules_list = [ScheduleModel.to_dict(s) for s in schedules]

        return success_response(schedules_list)

    except Exception as e:
        return error_response(f'获取调度列表失败: {str(e)}', 500)


@schedules_bp.route('/<schedule_id>', methods=['PATCH'])
def update_schedule(schedule_id):
    """更新调度状态"""
    try:
        data = request.get_json()
        db = get_db()

        # 检查调度是否存在
        schedule = db.schedules.find_one({'_id': ObjectId(schedule_id)})
        if not schedule:
            return error_response('调度不存在', 404)

        # 更新激活状态
        if 'is_active' in data:
            db.schedules.update_one(
                {'_id': ObjectId(schedule_id)},
                ScheduleModel.toggle_active(data['is_active'])
            )

        # 获取更新后的调度
        updated_schedule = db.schedules.find_one({'_id': ObjectId(schedule_id)})

        return success_response(
            ScheduleModel.to_dict(updated_schedule),
            '调度更新成功'
        )

    except InvalidId:
        return error_response('调度ID格式无效', 400)
    except Exception as e:
        return error_response(f'更新调度失败: {str(e)}', 500)


@schedules_bp.route('/<schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    """删除调度"""
    try:
        db = get_db()

        # 检查调度是否存在
        schedule = db.schedules.find_one({'_id': ObjectId(schedule_id)})
        if not schedule:
            return error_response('调度不存在', 404)

        # 删除调度
        db.schedules.delete_one({'_id': ObjectId(schedule_id)})

        return success_response(message='调度删除成功')

    except InvalidId:
        return error_response('调度ID格式无效', 400)
    except Exception as e:
        return error_response(f'删除调度失败: {str(e)}', 500)
