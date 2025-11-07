"""
数据验证与通用解析工具
"""
import re
from urllib.parse import urlparse
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime, timezone


def validate_url(url: str) -> tuple[bool, str]:
    """
    验证 URL 格式

    Args:
        url: 待验证的 URL

    Returns:
        (是否有效, 错误消息)
    """
    if not url:
        return False, "URL 不能为空"

    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            return False, "URL 格式无效"
        if result.scheme not in ['http', 'https']:
            return False, "URL 协议必须是 http 或 https"
        return True, ""
    except Exception as e:
        return False, f"URL 验证失败: {str(e)}"


def validate_domain(domain: str) -> tuple[bool, str]:
    """
    验证域名格式

    Args:
        domain: 待验证的域名

    Returns:
        (是否有效, 错误消息)
    """
    if not domain:
        return False, "域名不能为空"

    # 简单的域名格式验证
    pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    if not re.match(pattern, domain):
        return False, "域名格式无效"

    return True, ""


def validate_object_id(id_str: str) -> tuple[bool, str]:
    """
    验证 ObjectId 格式

    Args:
        id_str: 待验证的 ID 字符串

    Returns:
        (是否有效, 错误消息)
    """
    if not id_str:
        return False, "ID 不能为空"

    try:
        ObjectId(id_str)
        return True, ""
    except InvalidId:
        return False, "ID 格式无效"


def validate_pagination(page: int, page_size: int) -> tuple[bool, str]:
    """
    验证分页参数

    Args:
        page: 页码
        page_size: 每页大小

    Returns:
        (是否有效, 错误消息)
    """
    if page < 1:
        return False, "页码必须大于 0"
    if page_size < 1 or page_size > 100:
        return False, "每页大小必须在 1-100 之间"

    return True, ""


def validate_strategy(strategy: str) -> tuple[bool, str]:
    """
    验证爬取策略

    Args:
        strategy: 策略名称

    Returns:
        (是否有效, 错误消息)
    """
    if strategy not in ['incremental', 'full']:
        return False, "策略必须是 incremental 或 full"

    return True, ""


def validate_schedule_type(schedule_type: str) -> tuple[bool, str]:
    """
    验证调度类型

    Args:
        schedule_type: 调度类型

    Returns:
        (是否有效, 错误消息)
    """
    if schedule_type not in ['hourly', 'daily', 'monthly']:
        return False, "调度类型必须是 hourly、daily 或 monthly"

    return True, ""


def parse_iso_datetime(value: str) -> datetime:
    """
    解析 ISO-8601 日期时间字符串，兼容带 Z 结尾（UTC）的情况，并统一返回“无时区”的 UTC 时间。

    支持示例：
    - 2025-11-06T00:00:00Z
    - 2025-11-06T00:00:00.123Z
    - 2025-11-06T08:00:00+08:00
    - 2025-11-06T00:00:00

    行为：
    - 若字符串包含时区信息（Z 或 ±HH:MM），将先转换为 UTC，再去掉 tzinfo 返回“naive”时间，便于与数据库中无时区时间比较。
    - 若无时区信息，直接按本地“naive”时间解析（保持兼容现有存储）。

    Raises:
        ValueError: 当字符串格式无效时抛出。
    """
    if not isinstance(value, str) or not value.strip():
        raise ValueError("空的日期时间字符串")

    s = value.strip()

    # 将结尾的 Z 标记为 UTC 偏移，便于 fromisoformat 解析
    if s.endswith('Z'):
        s = s[:-1] + '+00:00'

    dt = datetime.fromisoformat(s)

    # 若解析出了时区信息，统一转为 UTC 并去掉 tzinfo，返回 naive UTC
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)

    return dt
