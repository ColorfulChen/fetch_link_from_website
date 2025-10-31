"""
网站管理 API
"""
from flask import request
from bson import ObjectId
from bson.errors import InvalidId
from urllib.parse import urlparse
import csv
import io

from . import websites_bp
from ..database import get_db
from ..models import WebsiteModel
from ..utils import success_response, error_response, paginate_response, validate_url


@websites_bp.route('', methods=['POST'])
def create_website():
    """创建网站"""
    try:
        data = request.get_json()

        # 验证必填字段
        if not data.get('name'):
            return error_response('网站名称不能为空')
        if not data.get('url'):
            return error_response('网站URL不能为空')

        # 验证 URL
        is_valid, msg = validate_url(data['url'])
        if not is_valid:
            return error_response(msg)

        # 提取域名
        parsed_url = urlparse(data['url'])
        domain = parsed_url.netloc

        # 检查 URL 是否已存在
        db = get_db()
        existing = db.websites.find_one({'url': data['url']})
        if existing:
            return error_response('该网站URL已存在', 409)

        # 创建网站文档
        website_doc = WebsiteModel.create(
            name=data['name'],
            url=data['url'],
            domain=domain,
            crawl_depth=data.get('crawl_depth', 3),
            max_links=data.get('max_links', 1000)
        )

        # 插入数据库
        result = db.websites.insert_one(website_doc)
        website_doc['_id'] = result.inserted_id

        return success_response(
            WebsiteModel.to_dict(website_doc),
            '网站创建成功',
            201
        )

    except Exception as e:
        return error_response(f'创建网站失败: {str(e)}', 500)


@websites_bp.route('', methods=['GET'])
def get_websites():
    """获取网站列表"""
    try:
        # 获取查询参数
        status = request.args.get('status', None)
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 2000))

        # 构建查询条件
        query = {}
        if status:
            query['status'] = status

        # 查询数据库
        db = get_db()
        total = db.websites.count_documents(query)
        skip = (page - 1) * page_size

        websites = list(db.websites.find(query)
                       .sort('created_at', -1)
                       .skip(skip)
                       .limit(page_size))

        # 转换为字典
        websites_list = [WebsiteModel.to_dict(w) for w in websites]

        return paginate_response(websites_list, total, page, page_size)

    except Exception as e:
        return error_response(f'获取网站列表失败: {str(e)}', 500)


@websites_bp.route('/<website_id>', methods=['GET'])
def get_website(website_id):
    """获取网站详情"""
    try:
        db = get_db()
        website = db.websites.find_one({'_id': ObjectId(website_id)})

        if not website:
            return error_response('网站不存在', 404)

        return success_response(WebsiteModel.to_dict(website))

    except InvalidId:
        return error_response('网站ID格式无效', 400)
    except Exception as e:
        return error_response(f'获取网站详情失败: {str(e)}', 500)


@websites_bp.route('/<website_id>', methods=['PUT'])
def update_website(website_id):
    """更新网站"""
    try:
        data = request.get_json()
        db = get_db()

        # 检查网站是否存在
        website = db.websites.find_one({'_id': ObjectId(website_id)})
        if not website:
            return error_response('网站不存在', 404)

        # 准备更新数据
        update_data = {}
        if 'name' in data:
            update_data['name'] = data['name']
        if 'status' in data:
            if data['status'] not in ['active', 'inactive']:
                return error_response('状态必须是 active 或 inactive')
            update_data['status'] = data['status']
        if 'crawl_depth' in data:
            update_data['crawl_depth'] = int(data['crawl_depth'])
        if 'max_links' in data:
            update_data['max_links'] = int(data['max_links'])

        # 更新数据库
        db.websites.update_one(
            {'_id': ObjectId(website_id)},
            WebsiteModel.update(update_data)
        )

        # 获取更新后的网站
        updated_website = db.websites.find_one({'_id': ObjectId(website_id)})

        return success_response(
            WebsiteModel.to_dict(updated_website),
            '网站更新成功'
        )

    except InvalidId:
        return error_response('网站ID格式无效', 400)
    except Exception as e:
        return error_response(f'更新网站失败: {str(e)}', 500)


@websites_bp.route('/<website_id>', methods=['DELETE'])
def delete_website(website_id):
    """删除网站"""
    try:
        db = get_db()

        # 检查网站是否存在
        website = db.websites.find_one({'_id': ObjectId(website_id)})
        if not website:
            return error_response('网站不存在', 404)

        # 删除网站
        db.websites.delete_one({'_id': ObjectId(website_id)})

        # 可以选择是否删除相关的任务和链接数据
        # db.crawl_tasks.delete_many({'website_id': ObjectId(website_id)})
        # db.crawled_links.delete_many({'website_id': ObjectId(website_id)})
        # db.schedules.delete_many({'website_id': ObjectId(website_id)})

        return success_response(message='网站删除成功')

    except InvalidId:
        return error_response('网站ID格式无效', 400)
    except Exception as e:
        return error_response(f'删除网站失败: {str(e)}', 500)


@websites_bp.route('/batch-import', methods=['POST'])
def batch_import_websites():
    """批量导入网站（CSV）"""
    try:
        # 检查是否有文件
        if 'file' not in request.files:
            return error_response('未找到上传的文件', 400)

        file = request.files['file']
        if file.filename == '':
            return error_response('未选择文件', 400)

        # 检查文件类型
        if not file.filename.endswith('.csv'):
            return error_response('只支持CSV文件', 400)

        # 读取文件内容
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)

        # 验证CSV表头
        required_fields = ['name', 'url']

        if not csv_reader.fieldnames:
            return error_response('CSV文件为空', 400)

        # 检查必填字段
        missing_fields = [field for field in required_fields if field not in csv_reader.fieldnames]
        if missing_fields:
            return error_response(f'CSV文件缺少必填字段: {", ".join(missing_fields)}', 400)

        # 处理数据
        db = get_db()
        success_count = 0
        failed_count = 0
        errors = []

        for row_num, row in enumerate(csv_reader, start=2):  # start=2 因为第1行是表头
            try:
                # 获取必填字段
                name = row.get('name', '').strip()
                url = row.get('url', '').strip()

                if not name:
                    errors.append(f'第{row_num}行: 网站名称不能为空')
                    failed_count += 1
                    continue

                if not url:
                    errors.append(f'第{row_num}行: 网站URL不能为空')
                    failed_count += 1
                    continue

                # 验证URL
                is_valid, msg = validate_url(url)
                if not is_valid:
                    errors.append(f'第{row_num}行: {msg}')
                    failed_count += 1
                    continue

                # 检查URL是否已存在
                existing = db.websites.find_one({'url': url})
                if existing:
                    errors.append(f'第{row_num}行: URL {url} 已存在')
                    failed_count += 1
                    continue

                # 获取可选字段
                crawl_depth = 3  # 默认值
                max_links = 1000  # 默认值

                if 'depth' in row and row['depth'].strip():
                    try:
                        crawl_depth = int(row['depth'])
                        if crawl_depth < 1:
                            errors.append(f'第{row_num}行: 爬取深度必须大于0')
                            failed_count += 1
                            continue
                    except ValueError:
                        errors.append(f'第{row_num}行: 爬取深度必须是整数')
                        failed_count += 1
                        continue

                if 'maxLinks' in row and row['maxLinks'].strip():
                    try:
                        max_links = int(row['maxLinks'])
                        if max_links < 1:
                            errors.append(f'第{row_num}行: 最大链接数必须大于0')
                            failed_count += 1
                            continue
                    except ValueError:
                        errors.append(f'第{row_num}行: 最大链接数必须是整数')
                        failed_count += 1
                        continue

                # 提取域名
                parsed_url = urlparse(url)
                domain = parsed_url.netloc

                # 创建网站文档
                website_doc = WebsiteModel.create(
                    name=name,
                    url=url,
                    domain=domain,
                    crawl_depth=crawl_depth,
                    max_links=max_links
                )

                # 插入数据库
                db.websites.insert_one(website_doc)
                success_count += 1

            except Exception as e:
                errors.append(f'第{row_num}行: {str(e)}')
                failed_count += 1

        # 返回导入结果
        result = {
            'success_count': success_count,
            'failed_count': failed_count,
            'total': success_count + failed_count,
            'errors': errors[:10]  # 只返回前10个错误
        }

        if success_count == 0:
            return error_response('所有网站导入失败', 400, result)
        elif failed_count > 0:
            return success_response(result, f'部分导入成功: 成功{success_count}个，失败{failed_count}个')
        else:
            return success_response(result, f'全部导入成功: {success_count}个网站')

    except Exception as e:
        return error_response(f'批量导入失败: {str(e)}', 500)


@websites_bp.route('/by-url', methods=['GET'])
def get_website_by_url():
    """根据URL查询网站ID"""
    try:
        # 获取查询参数
        url = request.args.get('url')

        if not url:
            return error_response('URL参数不能为空', 400)

        # 验证URL格式
        is_valid, msg = validate_url(url)
        if not is_valid:
            return error_response(msg, 400)

        # 查询数据库
        db = get_db()
        website = db.websites.find_one({'url': url})

        if not website:
            return error_response('未找到该URL对应的网站', 404)

        return success_response(WebsiteModel.to_dict(website))

    except Exception as e:
        return error_response(f'查询失败: {str(e)}', 500)
