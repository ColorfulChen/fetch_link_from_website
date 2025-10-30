"""
截图代理 API
"""
from flask import send_file, request
import os

from . import screenshots_bp
from ..utils import error_response


@screenshots_bp.route('/<path:filepath>', methods=['GET'])
def get_screenshot(filepath):
    """
    代理返回截图图片

    Args:
        filepath: 截图文件的相对路径（相对于项目根目录）

    Returns:
        图片文件
    """
    try:
        # 构建完整路径
        full_path = os.path.join(os.getcwd(), filepath)

        # 检查文件是否存在
        if not os.path.exists(full_path):
            return error_response('截图文件不存在', 404)

        # 检查文件是否为图片（简单验证）
        if not full_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            return error_response('文件不是有效的图片格式', 400)

        # 返回图片文件
        return send_file(full_path, mimetype='image/png')

    except Exception as e:
        return error_response(f'获取截图失败: {str(e)}', 500)
