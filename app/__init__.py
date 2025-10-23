"""
Flask 应用初始化
"""
import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from .database import init_db
from .utils import setup_logger

# 加载环境变量
load_dotenv()

# 初始化日志
logger = setup_logger('crawler', os.getenv('LOG_DIR', 'logs'), os.getenv('LOG_LEVEL', 'INFO'))


def create_app():
    """创建 Flask 应用"""
    app = Flask(__name__)

    # 加载配置
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    # 启用 CORS
    CORS(app)

    # 初始化数据库
    with app.app_context():
        try:
            init_db()
            logger.info("数据库初始化成功")
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")

    # 注册蓝图
    from .api import (
        websites_bp,
        tasks_bp,
        schedules_bp,
        export_bp,
        statistics_bp
    )

    app.register_blueprint(websites_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(schedules_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(statistics_bp)

    # 健康检查接口
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """健康检查"""
        from .database import get_db
        try:
            db = get_db()
            # 简单的 ping 测试
            db.command('ping')
            return jsonify({
                'status': 'healthy',
                'database': 'connected',
                'message': '服务运行正常'
            }), 200
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'database': 'disconnected',
                'message': f'数据库连接失败: {str(e)}'
            }), 500

    # 根路由
    @app.route('/', methods=['GET'])
    def index():
        """根路由"""
        return jsonify({
            'message': '网页链接爬虫系统 API',
            'version': '1.0.0',
            'endpoints': {
                'health': '/api/health',
                'websites': '/api/websites',
                'tasks': '/api/tasks',
                'schedules': '/api/schedules',
                'export': '/api/export',
                'statistics': '/api/statistics'
            }
        }), 200

    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'success': False, 'message': '接口不存在'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"服务器内部错误: {str(error)}")
        return jsonify({'success': False, 'message': '服务器内部错误'}), 500

    logger.info("Flask 应用创建成功")
    return app
