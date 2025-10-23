"""
MongoDB 数据库连接管理
"""
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import logging

logger = logging.getLogger(__name__)


class Database:
    """MongoDB 数据库连接管理类"""

    def __init__(self):
        self.client = None
        self.db = None

    def connect(self, uri=None, db_name=None):
        """
        连接到 MongoDB 数据库

        Args:
            uri: MongoDB 连接 URI，默认从环境变量读取
            db_name: 数据库名称，默认从环境变量读取
        """
        try:
            if uri is None:
                uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
            if db_name is None:
                db_name = os.getenv('MONGODB_DB_NAME', 'crawler_db')

            self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            # 测试连接
            self.client.admin.command('ping')
            self.db = self.client[db_name]

            logger.info(f"成功连接到 MongoDB 数据库: {db_name}")
            return self.db

        except ConnectionFailure as e:
            logger.error(f"无法连接到 MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"数据库连接错误: {e}")
            raise

    def disconnect(self):
        """关闭数据库连接"""
        if self.client:
            self.client.close()
            logger.info("MongoDB 连接已关闭")

    def get_collection(self, collection_name):
        """
        获取集合对象

        Args:
            collection_name: 集合名称

        Returns:
            Collection 对象
        """
        if self.db is None:
            raise Exception("数据库未连接，请先调用 connect() 方法")
        return self.db[collection_name]

    def create_indexes(self):
        """创建所有集合的索引"""
        try:
            # websites 集合索引
            websites = self.db.websites
            websites.create_index('url', unique=True)
            websites.create_index('domain')
            websites.create_index('status')

            # crawl_tasks 集合索引
            crawl_tasks = self.db.crawl_tasks
            crawl_tasks.create_index('website_id')
            crawl_tasks.create_index('status')
            crawl_tasks.create_index('started_at')
            crawl_tasks.create_index([('website_id', 1), ('started_at', -1)])

            # crawled_links 集合索引
            crawled_links = self.db.crawled_links
            crawled_links.create_index([('website_id', 1), ('url', 1)], unique=True)
            crawled_links.create_index('domain')
            crawled_links.create_index('last_crawled_at')
            crawled_links.create_index('link_type')

            # crawl_logs 集合索引
            crawl_logs = self.db.crawl_logs
            crawl_logs.create_index('task_id')
            crawl_logs.create_index('level')
            crawl_logs.create_index('created_at')
            crawl_logs.create_index([('task_id', 1), ('created_at', -1)])

            # schedules 集合索引
            schedules = self.db.schedules
            schedules.create_index('website_id')
            schedules.create_index('is_active')
            schedules.create_index('next_run_time')

            logger.info("数据库索引创建完成")

        except Exception as e:
            logger.error(f"创建索引失败: {e}")
            raise


# 全局数据库实例
db_instance = Database()


def get_db():
    """获取数据库实例"""
    if db_instance.db is None:
        db_instance.connect()
    return db_instance.db


def init_db():
    """初始化数据库（连接并创建索引）"""
    db_instance.connect()
    db_instance.create_indexes()
    return db_instance.db
