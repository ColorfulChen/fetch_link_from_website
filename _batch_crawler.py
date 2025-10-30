import argparse
import json
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import sleep, monotonic  # 新增：用于轮询与超时

import requests


def read_websites(json_path: str, only_active: bool = True) -> List[Dict[str, Any]]:
	"""
	读取网站配置列表，并规范化字段：
	- id: 从 _id.$oid 取值
	- crawl_depth, max_links: 原样透传
	- name, url: 可用于日志
	"""
	with open(json_path, "r", encoding="utf-8-sig") as f:
		data = json.load(f)

	websites = []
	for item in data:
		if only_active and item.get("status") != "active":
			continue
		_oid = item.get("_id", {}).get("$oid")
		if not _oid:
			continue
		websites.append(
			{
				"id": _oid,
				"name": item.get("name"),
				"url": item.get("url"),
				"crawl_depth": item.get("crawl_depth"),
				"max_links": item.get("max_links"),
			}
		)
	return websites


def create_task(
	session: requests.Session,
	base_url: str,
	website_id: str,
	strategy: str,
	depth: Optional[int] = None,
	max_links: Optional[int] = None,
	timeout: int = 15,
) -> Dict[str, Any]:
	"""
	调用 /api/tasks/crawl 创建单个任务。
	返回统一的结果字典，包含 success, status_code, message, data。
	"""
	url = f"{base_url.rstrip('/')}/api/tasks/crawl"
	payload: Dict[str, Any] = {
		"website_id": website_id,
		"strategy": strategy,
	}
	if isinstance(depth, int):
		payload["depth"] = depth
	if isinstance(max_links, int):
		payload["max_links"] = max_links

	try:
		resp = session.post(url, json=payload, timeout=timeout)
		status = resp.status_code
		ct = resp.headers.get("Content-Type", "")
		body = resp.json() if "application/json" in ct.lower() else {"raw": resp.text}

		# 成功：200/201/202；冲突：409（已有运行中的任务）
		if status in (200, 201, 202):
			return {
			 "success": True,
			 "status_code": status,
			 "message": body.get("message") or "任务创建成功",
			 "data": body.get("data"),
			}
		elif status == 409:
			return {
			 "success": False,
			 "status_code": status,
			 "message": body.get("message") or "已有运行中的任务，跳过",
			 "data": body.get("data"),
			}
		else:
			return {
			 "success": False,
			 "status_code": status,
			 "message": body.get("message") or f"请求失败: {status}",
			 "data": body.get("data"),
			}
	except requests.RequestException as e:
		return {
		 "success": False,
		 "status_code": -1,
		 "message": f"网络错误: {e}",
		 "data": None,
		}


def get_task_status(
	session: requests.Session,
	base_url: str,
	task_id: str,
	timeout: int = 15,
) -> Dict[str, Any]:
	"""
	查询任务状态：GET /api/tasks/{task_id}
	返回：{ success, status_code, status, data, message }
	"""
	url = f"{base_url.rstrip('/')}/api/tasks/{task_id}"
	try:
		resp = session.get(url, timeout=timeout)
		ct = resp.headers.get("Content-Type", "")
		body = resp.json() if "application/json" in ct.lower() else {}
		if resp.status_code == 200 and body.get("success", False):
			data = body.get("data") or {}
			return {
				"success": True,
				"status_code": 200,
				"status": data.get("status"),
				"data": data,
				"message": "OK",
			}
		return {
			"success": False,
			"status_code": resp.status_code,
			"status": None,
			"data": body.get("data"),
			"message": body.get("message") or "查询任务状态失败",
		}
	except requests.RequestException as e:
		return {
			"success": False,
			"status_code": -1,
			"status": None,
			"data": None,
			"message": f"网络错误: {e}",
		}


def wait_for_task_completion(
	session: requests.Session,
	base_url: str,
	task_id: str,
	poll_interval: int = 3,
	max_wait_seconds: int = 0,
) -> Dict[str, Any]:
	"""
	轮询任务直到结束或超时。
	返回：{ finished: bool, final_status: str|None, data, message }
	"""
	start = monotonic()
	terminal = {"completed", "failed", "cancelled"}
	while True:
		res = get_task_status(session, base_url, task_id)
		if res["success"]:
			st = res["status"]
			if st in terminal:
				return {
					"finished": True,
					"final_status": st,
					"data": res.get("data"),
					"message": f"任务结束: {st}",
				}
		else:
			# 查询失败也等待重试
			pass

		if max_wait_seconds and monotonic() - start >= max_wait_seconds:
			return {
				"finished": False,
				"final_status": None,
				"data": None,
				"message": "等待超时",
			}
		sleep(max(1, int(poll_interval)))


def main():
	parser = argparse.ArgumentParser(description="批量创建爬取任务（读取 JSON 并调用 /api/tasks/crawl）")
	parser.add_argument(
		"--json",
		default="website_matches.json",
		help="网站配置 JSON 文件路径",
	)
	parser.add_argument(
		"--base-url",
		default="http://127.0.0.1:9999",
		help="API 基础地址（例如 http://localhost:5000）",
	)
	parser.add_argument(
		"--strategy",
		choices=["incremental", "full"],
		default="full",
		help="爬取策略",
	)
	parser.add_argument(
		"--concurrency",
		type=int,
		default=1,
		help="并发数量（线程数）",
	)
	parser.add_argument(
		"--limit",
		type=int,
		default=1,
		help="最多处理的网站数，0 表示不限制",
	)
	# 新增：等待模式与参数
	parser.add_argument(
		"--wait",
		action="store_true",
		help="顺序执行：为每个网站创建任务后等待其完成，再执行下一个",
	)
	parser.add_argument(
		"--poll-interval",
		type=int,
		default=3,
		help="等待模式下的轮询间隔（秒）",
	)
	parser.add_argument(
		"--wait-timeout",
		type=int,
		default=0,
		help="等待模式下单个任务的最大等待时间（秒，0 表示不限制）",
	)
	args = parser.parse_args()

	websites = read_websites(args.json, only_active=True)
	if args.limit and args.limit > 0:
		websites = websites[: args.limit]

	if not websites:
		print("未找到可用网站（active），退出。")
		return

	print(f"准备创建任务：{len(websites)} 个网站，策略={args.strategy}，并发={args.concurrency}")

	ok, skipped, failed = 0, 0, 0
	results: List[Dict[str, Any]] = []

	if args.wait:
		print("顺序执行已开启：每个任务完成后再启动下一个。")
		with requests.Session() as session:
			finished_completed = finished_failed = finished_cancelled = finished_timeout = 0
			for site in websites:
				name = site.get("name") or site["id"]
				print(f"启动任务 -> {name}")
				res = create_task(
					session,
					args.base_url,
					site["id"],
					args.strategy,
					site.get("crawl_depth"),
					site.get("max_links"),
				)
				if res["success"]:
					ok += 1
					task_id = (res.get("data") or {}).get("id")
					print(f"[OK] {name}: {res['message']} (task_id={task_id})")
					if not task_id:
						print(f"[WARN] {name}: 未返回任务ID，无法等待，继续下一个。")
						continue
					wait_res = wait_for_task_completion(
						session,
						args.base_url,
						task_id,
						poll_interval=args.poll_interval,
						max_wait_seconds=args.wait_timeout,
					)
					if wait_res["finished"]:
						st = wait_res["final_status"]
						if st == "completed":
							finished_completed += 1
						elif st == "failed":
							finished_failed += 1
						elif st == "cancelled":
							finished_cancelled += 1
						print(f"[DONE] {name}: 状态={st}")
					else:
						finished_timeout += 1
						print(f"[TIMEOUT] {name}: {wait_res['message']}")
				else:
					if res.get("status_code") == 409:
						skipped += 1
						print(f"[SKIP] {name}: {res['message']}")
					else:
						failed += 1
						print(f"[FAIL] {name}: {res['message']}")

		print(
			f"\n创建汇总：成功={ok}, 跳过={skipped}, 失败={failed}, 总数={len(websites)}"
			f"\n完成汇总（等待模式）：completed={finished_completed}, failed={finished_failed}, cancelled={finished_cancelled}, timeout={finished_timeout}"
		)
		return

	# 非等待模式：保留并发提交的原有逻辑
	with requests.Session() as session:
		with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
			future_to_site = {
				executor.submit(
					create_task,
					session,
					args.base_url,
					site["id"],
					args.strategy,
					1,
					# site.get("crawl_depth"),
					site.get("max_links"),
				): site
				for site in websites
			}

			for future in as_completed(future_to_site):
				site = future_to_site[future]
				name = site.get("name") or site["id"]
				try:
					res = future.result()
					results.append(res)
					if res["success"]:
						ok += 1
						print(f"[OK] {name}: {res['message']}")
					else:
						# 409 视为跳过
						if res.get("status_code") == 409:
							skipped += 1
							print(f"[SKIP] {name}: {res['message']}")
						else:
							failed += 1
							print(f"[FAIL] {name}: {res['message']}")
				except Exception as e:
					failed += 1
					print(f"[ERROR] {name}: {e}")

	print(f"\n完成：成功={ok}, 跳过={skipped}, 失败={failed}, 总数={len(websites)}")


if __name__ == "__main__":
	main()

# 使用示例：
# python _batch_crawler.py ^
#   --json "c:\Users\orz0\Desktop\cert项目\fetch_link_from_website\website_matches.json" ^
#   --base-url "http://localhost:5000" ^
#   --strategy incremental ^
#   --concurrency 8 ^
#   --limit 50
