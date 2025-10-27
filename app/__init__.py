"""
Flask 应用初始化
"""
import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

from .database import init_db
from .utils import setup_logger

# 加载环境变量
load_dotenv()

# 初始化日志
logger = setup_logger('crawler', os.getenv(
    'LOG_DIR', 'logs'), os.getenv('LOG_LEVEL', 'INFO'))


def create_app():
    """创建 Flask 应用"""
    # 禁用默认静态文件夹，避免与自定义路由冲突
    app = Flask(__name__, static_folder=None)

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
        statistics_bp,
        screenshots_bp
    )

    app.register_blueprint(websites_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(schedules_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(statistics_bp)
    app.register_blueprint(screenshots_bp)

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
    @app.route('/api', methods=['GET'])
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
                'statistics': '/api/statistics',
                'screenshots': '/api/screenshots'
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

    # Vue 应用服务路由（必须放在最后，避免拦截 API 请求）
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_vue_app(path):
        """从web目录提供Vue.js应用"""
        logger.debug(f"请求路径: {path}")

        # 获取正确的web目录路径
        current_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))
        web_dir = os.path.join(current_dir, "web")

        # 检查路径是否存在
        if not os.path.exists(web_dir):
            logger.error(f"Web 目录不存在: {web_dir}")
            return jsonify({"status": "error", "message": "Web directory not found"}), 404

        # 构建完整文件路径
        file_path = os.path.join(web_dir, path) if path else os.path.join(web_dir, "index.html")

        # 如果是请求具体文件且文件存在，直接返回
        if path and os.path.isfile(file_path):
            logger.debug(f"提供文件: {file_path}")
            return send_from_directory(web_dir, path)

        # 否则返回 index.html（用于 Vue Router 的历史模式）
        logger.debug(f"返回 index.html")
        return send_from_directory(web_dir, "index.html")

    logger.info("Flask 应用创建成功")
    return app
