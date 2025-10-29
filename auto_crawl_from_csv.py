#!/usr/bin/env python
"""
自动爬取脚本 - 从CSV文件读取URL并自动创建爬取任务
"""
import argparse
import csv
import time
import sys
import requests
from typing import Optional, Dict, Any
from urllib.parse import quote


class CrawlAutomation:
    """爬取自动化类"""

    def __init__(self, api_base_url: str = "http://localhost:9999",
                 depth: int = 3, max_links: int = 1000, strategy: str = "incremental"):
        """
        初始化

        Args:
            api_base_url: API基础URL
            depth: 爬取深度
            max_links: 最大链接数
            strategy: 爬取策略 (incremental/full)
        """
        self.api_base_url = api_base_url.rstrip('/')
        self.depth = depth
        self.max_links = max_links
        self.strategy = strategy

        # 创建session并禁用代理
        self.session = requests.Session()
        self.session.trust_env = False  # 不使用环境变量中的代理设置
        self.session.proxies = {
            'http': None,
            'https': None
        }

    def get_website_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        根据URL查询网站ID

        Args:
            url: 网站URL

        Returns:
            网站信息字典，如果不存在返回None
        """
        try:
            encoded_url = quote(url, safe='')
            api_url = f"{self.api_base_url}/api/websites/by-url?url={encoded_url}"
            print(f"  → 查询网站信息: {url}")

            response = self.session.get(api_url, timeout=10)

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    website = result.get('data')
                    print(f"  ✓ 找到网站: {website['name']} (ID: {website['id']})")
                    return website
            elif response.status_code == 404:
                print(f"  ✗ 网站不存在: {url}")
                return None
            else:
                print(f"  ✗ 查询失败: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"  ✗ 查询异常: {str(e)}")
            return None

    def create_crawl_task(self, website_id: str) -> Optional[Dict[str, Any]]:
        """
        创建爬取任务

        Args:
            website_id: 网站ID

        Returns:
            任务信息字典，失败返回None
        """
        try:
            api_url = f"{self.api_base_url}/api/tasks/crawl"
            payload = {
                "website_id": website_id,
                "strategy": self.strategy,
                "depth": self.depth,
                "max_links": self.max_links
            }

            print(f"  → 创建爬取任务 (策略: {self.strategy}, 深度: {self.depth}, 最大链接: {self.max_links})")

            response = self.session.post(api_url, json=payload, timeout=10)

            if response.status_code in [200, 201, 202]:  # 202是异步任务创建成功
                result = response.json()
                if result.get('success'):
                    task = result.get('data')
                    print(f"  ✓ 任务创建成功 (ID: {task['id']})")
                    return task

            print(f"  ✗ 任务创建失败: {response.status_code} - {response.text}")
            return None

        except Exception as e:
            print(f"  ✗ 创建任务异常: {str(e)}")
            return None

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        查询任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务信息字典，失败返回None
        """
        try:
            api_url = f"{self.api_base_url}/api/tasks/{task_id}"
            response = self.session.get(api_url, timeout=10)

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return result.get('data')

            return None

        except Exception as e:
            print(f"  ✗ 查询任务状态异常: {str(e)}")
            return None

    def wait_for_task_completion(self, task_id: str, check_interval: int = 30) -> bool:
        """
        等待任务完成

        Args:
            task_id: 任务ID
            check_interval: 检查间隔(秒)

        Returns:
            任务是否成功完成
        """
        print(f"  → 等待任务完成 (每{check_interval}秒检查一次)")

        while True:
            task = self.get_task_status(task_id)

            if not task:
                print(f"  ✗ 无法获取任务状态")
                return False

            status = task.get('status')

            if status == 'completed':
                stats = task.get('statistics', {})
                print(f"  ✓ 任务完成!")
                print(f"    - 总链接: {stats.get('total_links', 0)}")
                print(f"    - 有效链接: {stats.get('valid_links', 0)}")
                print(f"    - 新增链接: {stats.get('new_links', 0)}")
                print(f"    - 有效率: {stats.get('valid_rate', 0):.2%}")
                return True

            elif status == 'failed':
                error_msg = task.get('error_message', '未知错误')
                print(f"  ✗ 任务失败: {error_msg}")
                return False

            elif status == 'cancelled':
                print(f"  ✗ 任务已取消")
                return False

            elif status in ['pending', 'running']:
                stats = task.get('statistics', {})
                print(f"  ⏳ 任务进行中 ({status}) - 已爬取: {stats.get('total_links', 0)} 个链接")
                time.sleep(check_interval)

            else:
                print(f"  ? 未知状态: {status}")
                time.sleep(check_interval)

    def process_url(self, url: str, index: int, total: int) -> bool:
        """
        处理单个URL

        Args:
            url: 网站URL
            index: 当前索引
            total: 总数量

        Returns:
            是否成功
        """
        print(f"\n{'='*60}")
        print(f"处理 [{index}/{total}]: {url}")
        print(f"{'='*60}")

        # 1. 查询网站ID
        website = self.get_website_by_url(url)
        if not website:
            print(f"⚠ 跳过此URL (网站不存在)")
            return False

        website_id = website['id']

        # 2. 创建爬取任务
        task = self.create_crawl_task(website_id)
        if not task:
            print(f"⚠ 跳过此URL (任务创建失败)")
            return False

        task_id = task['id']

        # 3. 等待任务完成
        success = self.wait_for_task_completion(task_id)

        return success

    def run(self, csv_file_path: str, check_interval: int = 30):
        """
        运行自动化流程

        Args:
            csv_file_path: CSV文件路径
            check_interval: 任务状态检查间隔(秒)
        """
        print(f"\n{'='*60}")
        print(f"开始自动爬取流程")
        print(f"{'='*60}")
        print(f"CSV文件: {csv_file_path}")
        print(f"API地址: {self.api_base_url}")
        print(f"爬取深度: {self.depth}")
        print(f"最大链接: {self.max_links}")
        print(f"爬取策略: {self.strategy}")
        print(f"检查间隔: {check_interval}秒")

        # 读取CSV文件
        urls = []
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    url = row.get('url', '').strip()
                    if url:
                        urls.append(url)
        except Exception as e:
            print(f"\n✗ 读取CSV文件失败: {str(e)}")
            sys.exit(1)

        if not urls:
            print(f"\n✗ CSV文件中没有找到URL")
            sys.exit(1)

        print(f"\n找到 {len(urls)} 个URL")

        # 统计信息
        success_count = 0
        failed_count = 0
        start_time = time.time()

        # 处理每个URL
        for i, url in enumerate(urls, 1):
            success = self.process_url(url, i, len(urls))
            if success:
                success_count += 1
            else:
                failed_count += 1

        # 输出总结
        elapsed_time = time.time() - start_time
        print(f"\n{'='*60}")
        print(f"自动爬取完成!")
        print(f"{'='*60}")
        print(f"总URL数: {len(urls)}")
        print(f"成功: {success_count}")
        print(f"失败: {failed_count}")
        print(f"耗时: {elapsed_time:.2f}秒 ({elapsed_time/60:.2f}分钟)")
        print(f"{'='*60}\n")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='从CSV文件自动创建和执行爬取任务',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s webside.csv
  %(prog)s webside.csv --depth 5 --max-links 2000
  %(prog)s webside.csv --strategy full --interval 60
  %(prog)s webside.csv --api http://localhost:5000
        """
    )

    parser.add_argument(
        'csv_file',
        help='CSV文件路径 (必须包含url列)'
    )

    parser.add_argument(
        '--api',
        default='http://localhost:9999',
        help='API基础URL (默认: http://localhost:9999)'
    )

    parser.add_argument(
        '--depth',
        type=int,
        default=3,
        help='爬取深度 (默认: 3)'
    )

    parser.add_argument(
        '--max-links',
        type=int,
        default=1000,
        help='最大链接数 (默认: 1000)'
    )

    parser.add_argument(
        '--strategy',
        choices=['incremental', 'full'],
        default='incremental',
        help='爬取策略 (默认: incremental)'
    )

    parser.add_argument(
        '--interval',
        type=int,
        default=30,
        help='任务状态检查间隔(秒) (默认: 30)'
    )

    args = parser.parse_args()

    # 创建自动化实例
    automation = CrawlAutomation(
        api_base_url=args.api,
        depth=args.depth,
        max_links=args.max_links,
        strategy=args.strategy
    )

    # 运行自动化流程
    try:
        automation.run(args.csv_file, args.interval)
    except KeyboardInterrupt:
        print("\n\n⚠ 用户中断执行")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 执行失败: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
