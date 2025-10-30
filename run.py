"""
Flask 应用启动入口
"""
import os
from app import create_app
from scheduler import init_scheduler, start_scheduler

# 创建 Flask 应用
app = create_app()

# 初始化并启动调度器
try:
    init_scheduler()
    start_scheduler()
    print("定时任务调度器已启动")
except Exception as e:
    print(f"启动调度器失败: {str(e)}")

if __name__ == '__main__':
    # 获取配置
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 9999))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    print(f"启动 Flask 应用...")
    print(f"访问地址: http://{host}:{port}")
    print(f"健康检查: http://{host}:{port}/api/health")

    # 启动应用
    app.run(host=host, port=port, debug=debug)
