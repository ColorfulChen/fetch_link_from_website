"""
统一响应格式工具
"""
from typing import Any, Optional, Dict
from flask import jsonify


def success_response(data: Any = None, message: str = "success", status_code: int = 200):
    """
    成功响应

    Args:
        data: 响应数据
        message: 响应消息
        status_code: HTTP 状态码

    Returns:
        Flask Response 对象
    """
    response = {
        'success': True,
        'message': message,
        'data': data
    }
    return jsonify(response), status_code


def error_response(message: str, status_code: int = 400, errors: Optional[Dict] = None):
    """
    错误响应

    Args:
        message: 错误消息
        status_code: HTTP 状态码
        errors: 详细错误信息

    Returns:
        Flask Response 对象
    """
    response = {
        'success': False,
        'message': message
    }
    if errors:
        response['errors'] = errors

    return jsonify(response), status_code


def paginate_response(data: list, total: int, page: int = 1,
                     page_size: int = 20, status_code: int = 200):
    """
    分页响应

    Args:
        data: 数据列表
        total: 总记录数
        page: 当前页码
        page_size: 每页大小
        status_code: HTTP 状态码

    Returns:
        Flask Response 对象
    """
    response = {
        'success': True,
        'data': data,
        'pagination': {
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }
    }
    return jsonify(response), status_code
