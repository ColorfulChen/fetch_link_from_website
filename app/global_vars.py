"""
全局变量和资源管理
"""

# 全局浏览器实例（延迟初始化）
driver = None

# 任务停止标志字典 {task_id: should_stop}
stop_flags = {}


def init_driver():
    """初始化无头浏览器（Selenium/Chrome）"""
    global driver
    if driver is not None:
        return driver
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        opts = Options()
        # 现代无头模式
        opts.add_argument('--headless=new')
        opts.add_argument('--disable-gpu')
        opts.add_argument('--no-sandbox')
        opts.add_argument('--window-size=1280,1024')
        driver = webdriver.Chrome(options=opts)
        driver.set_page_load_timeout(12)
        print("浏览器初始化成功")
        return driver
    except Exception as e:
        print(f"初始化截图浏览器失败: {e}")
        driver = None
        return None


def cleanup_driver():
    """清理浏览器实例"""
    global driver
    try:
        if driver:
            driver.quit()
            print("浏览器已清理")
    except Exception as e:
        print(f"清理浏览器时出错: {e}")
    driver = None


def get_driver():
    """获取浏览器实例（如果未初始化则自动初始化）"""
    global driver
    if driver is None:
        return init_driver()
    return driver


def set_stop_flag(task_id):
    """设置任务停止标志"""
    global stop_flags
    stop_flags[str(task_id)] = True


def clear_stop_flag(task_id):
    """清除任务停止标志"""
    global stop_flags
    task_key = str(task_id)
    if task_key in stop_flags:
        del stop_flags[task_key]


def should_stop(task_id):
    """检查任务是否应该停止"""
    global stop_flags
    return stop_flags.get(str(task_id), False)
