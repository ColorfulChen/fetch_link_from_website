"""
定时任务定义
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
from datetime import datetime

from app.database import get_db
from app.models import CrawlTaskModel

logger = logging.getLogger(__name__)

# 全局调度器实例
scheduler = None


def crawl_job(schedule_id, website_id, strategy):
    """
    爬取任务执行函数

    Args:
        schedule_id: 调度ID
        website_id: 网站ID
        strategy: 爬取策略
    """
    try:
        logger.info(f"开始执行定时爬取任务 - 网站ID: {website_id}, 策略: {strategy}")

        db = get_db()

        # 检查是否有正在运行的任务
        running_task = db.crawl_tasks.find_one({
            'website_id': website_id,
            'status': 'running'
        })

        if running_task:
            logger.warning(f"网站 {website_id} 已有正在运行的任务，跳过本次执行")
            return

        # 获取网站信息
        website = db.websites.find_one({'_id': website_id})
        if not website:
            logger.error(f"网站不存在: {website_id}")
            return

        # 创建任务
        task_doc = CrawlTaskModel.create(
            website_id=website_id,
            strategy=strategy,
            task_type='scheduled'
        )
        result = db.crawl_tasks.insert_one(task_doc)
        task_id = result.inserted_id

        logger.info(f"创建爬取任务成功 - 任务ID: {task_id}")

        # 调用爬虫服务执行爬取
        try:
            from app.services.crawler_service import CrawlerService
            crawler = CrawlerService()
            depth = website.get('crawl_depth', 3)
            max_links = website.get('max_links', 1000)
            crawler.crawl(task_id, website_id, strategy, depth, max_links)
            logger.info(f"爬取任务执行成功 - 任务ID: {task_id}")
        except Exception as e:
            logger.error(f"爬取任务执行失败 - 任务ID: {task_id}, 错误: {str(e)}")

        # 更新调度的最后运行时间
        from app.models import ScheduleModel
        db.schedules.update_one(
            {'_id': schedule_id},
            ScheduleModel.update_run_time(last_run_time=datetime.utcnow())
        )

    except Exception as e:
        logger.error(f"执行定时爬取任务失败: {str(e)}")


def init_scheduler():
    """初始化调度器"""
    global scheduler

    if scheduler is None:
        scheduler = BackgroundScheduler(timezone='Asia/Shanghai')
        logger.info("调度器初始化成功")
    else:
        logger.info("调度器已存在，跳过初始化")

    return scheduler


def start_scheduler():
    """启动调度器"""
    global scheduler

    if scheduler is None:
        init_scheduler()

    # 从数据库加载所有激活的调度
    try:
        db = get_db()
        schedules = db.schedules.find({'is_active': True})

        for schedule in schedules:
            add_job_from_schedule(schedule)

        scheduler.start()
        logger.info("调度器启动成功")

    except Exception as e:
        logger.error(f"启动调度器失败: {str(e)}")
        raise


def stop_scheduler():
    """停止调度器"""
    global scheduler

    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("调度器已停止")


def add_job_from_schedule(schedule):
    """
    从调度配置添加任务

    Args:
        schedule: 调度配置文档
    """
    global scheduler

    if scheduler is None:
        init_scheduler()

    try:
        job_id = f"schedule_{str(schedule['_id'])}"

        # 检查任务是否已存在
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)

        # 添加任务
        scheduler.add_job(
            func=crawl_job,
            trigger=CronTrigger.from_crontab(schedule['cron_expression']),
            args=[schedule['_id'], schedule['website_id'], schedule['strategy']],
            id=job_id,
            name=schedule['name'],
            replace_existing=True
        )

        logger.info(f"添加定时任务: {schedule['name']} (Cron: {schedule['cron_expression']})")

    except Exception as e:
        logger.error(f"添加定时任务失败: {str(e)}")


def remove_job(schedule_id):
    """
    移除定时任务

    Args:
        schedule_id: 调度ID
    """
    global scheduler

    if scheduler is None:
        return

    try:
        job_id = f"schedule_{str(schedule_id)}"
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
            logger.info(f"移除定时任务: {job_id}")

    except Exception as e:
        logger.error(f"移除定时任务失败: {str(e)}")


def pause_job(schedule_id):
    """
    暂停定时任务

    Args:
        schedule_id: 调度ID
    """
    global scheduler

    if scheduler is None:
        return

    try:
        job_id = f"schedule_{str(schedule_id)}"
        if scheduler.get_job(job_id):
            scheduler.pause_job(job_id)
            logger.info(f"暂停定时任务: {job_id}")

    except Exception as e:
        logger.error(f"暂停定时任务失败: {str(e)}")


def resume_job(schedule_id):
    """
    恢复定时任务

    Args:
        schedule_id: 调度ID
    """
    global scheduler

    if scheduler is None:
        return

    try:
        job_id = f"schedule_{str(schedule_id)}"
        if scheduler.get_job(job_id):
            scheduler.resume_job(job_id)
            logger.info(f"恢复定时任务: {job_id}")

    except Exception as e:
        logger.error(f"恢复定时任务失败: {str(e)}")
