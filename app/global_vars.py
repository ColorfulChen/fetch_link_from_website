"""
全局变量和资源管理
"""

# 全局浏览器实例（延迟初始化）
driver = None


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
