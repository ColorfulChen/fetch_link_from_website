# API 测试文档

## 测试环境

- **服务器地址**: http://localhost:5000
- **测试工具**: curl / Postman
- **爬取深度**: 2（为缩短测试时间）
- **最大链接数**: 100（为缩短测试时间）
- **测试日期**: 2025-10-24

## 测试说明

本文档包含所有 API 接口的测试用例，按照实际使用流程组织测试步骤。每个测试用例包含：
- 测试目的
- 请求命令
- 预期结果
- 实际结果记录区

**注意**: 为了缩短测试时间，所有爬取任务的深度设置为 2，最大链接数设置为 100。

---

## 测试流程

```
1. 系统健康检查
   ↓
2. 创建网站
   ↓
3. 启动爬取任务（全量）
   ↓
4. 查询任务状态和日志
   ↓
5. 启动爬取任务（增量）
   ↓
6. 创建定时调度
   ↓
7. 数据导出
   ↓
8. 查看统计数据
   ↓
9. 更新/删除操作
```

---

## 第一部分：系统信息 API 测试

### 测试 1.1：获取系统信息

**测试目的**: 验证 API 服务是否正常运行

**请求命令**:
```bash
curl -X GET http://localhost:5000/api
```

**预期结果**:
```json
{
  "message": "网页链接爬虫系统 API",
  "version": "1.0.0",
  "endpoints": {
    "health": "/api/health",
    "websites": "/api/websites",
    "tasks": "/api/tasks",
    "schedules": "/api/schedules",
    "export": "/api/export",
    "statistics": "/api/statistics"
  }
}
```

**实际结果**:
```
[ ] 通过
[ ] 失败
记录：______________________________________
```

---

### 测试 1.2：健康检查

**测试目的**: 验证服务和数据库连接状态

**请求命令**:
```bash
curl -X GET http://localhost:5000/api/health
```

**预期结果**:
```json
{
  "status": "healthy",
  "database": "connected",
  "message": "服务运行正常"
}
```

**实际结果**:
```
[ ] 通过
[ ] 失败
记录：______________________________________
```

---

## 第二部分：网站管理 API 测试

### 测试 2.1：创建网站（成功）

**测试目的**: 创建一个测试网站

**请求命令**:
```bash
curl -X POST http://localhost:5000/api/websites \
  -H "Content-Type: application/json" \
  -d '{
    "name": "百度测试",
    "url": "https://www.baidu.com",
    "crawl_depth": 2,
    "max_links": 100
  }'
```

**预期结果**:
- HTTP 状态码: 201
- 返回创建的网站信息
- 包含 `id` 字段

**实际结果**:
```
[ ] 通过
[ ] 失败
网站ID：______________________________________
记录：______________________________________
```

---

### 测试 2.2：创建网站（URL 重复）

**测试目的**: 验证重复 URL 检测

**请求命令**:
```bash
curl -X POST http://localhost:5000/api/websites \
  -H "Content-Type: application/json" \
  -d '{
    "name": "百度测试2",
    "url": "https://www.baidu.com",
    "crawl_depth": 2,
    "max_links": 100
  }'
```

**预期结果**:
- HTTP 状态码: 409
- 错误消息: "该网站URL已存在"

**实际结果**:
```
[ ] 通过
[ ] 失败
记录：______________________________________
```

---

### 测试 2.3：创建网站（参数验证）

**测试目的**: 验证必填字段验证

**请求命令**:
```bash
curl -X POST http://localhost:5000/api/websites \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.example.com"
  }'
```

**预期结果**:
- HTTP 状态码: 400
- 错误消息: "网站名称不能为空"

**实际结果**:
```
[ ] 通过
[ ] 失败
记录：______________________________________
```

---

### 测试 2.4：获取网站列表

**测试目的**: 验证网站列表查询功能

**请求命令**:
```bash
curl -X GET "http://localhost:5000/api/websites?page=1&page_size=10"
```

**预期结果**:
- HTTP 状态码: 200
- 返回网站列表
- 包含分页信息

**实际结果**:
```
[ ] 通过
[ ] 失败
网站数量：______________________________________
记录：______________________________________
```

---

### 测试 2.5：获取网站列表（按状态过滤）

**测试目的**: 验证状态过滤功能

**请求命令**:
```bash
curl -X GET "http://localhost:5000/api/websites?status=active&page=1&page_size=10"
```

**预期结果**:
- HTTP 状态码: 200
- 返回状态为 active 的网站

**实际结果**:
```
[ ] 通过
[ ] 失败
记录：______________________________________
```

---

### 测试 2.6：获取网站详情

**测试目的**: 验证获取单个网站详细信息

**请求命令**:
```bash
# 替换 {website_id} 为实际的网站 ID
curl -X GET http://localhost:5000/api/websites/{website_id}
```

**预期结果**:
- HTTP 状态码: 200
- 返回网站详细信息

**实际结果**:
```
[ ] 通过
[ ] 失败
记录：______________________________________
```

---

### 测试 2.7：更新网站

**测试目的**: 验证网站信息更新功能

**请求命令**:
```bash
# 替换 {website_id} 为实际的网站 ID
curl -X PUT http://localhost:5000/api/websites/{website_id} \
  -H "Content-Type: application/json" \
  -d '{
    "name": "百度测试（已更新）",
    "crawl_depth": 2,
    "max_links": 150
  }'
```

**预期结果**:
- HTTP 状态码: 200
- 返回更新后的网站信息
- 字段已更新

**实际结果**:
```
[ ] 通过
[ ] 失败
记录：______________________________________
```

---

### 测试 2.8：更新网站状态

**测试目的**: 验证网站状态更新

**请求命令**:
```bash
# 替换 {website_id} 为实际的网站 ID
curl -X PUT http://localhost:5000/api/websites/{website_id} \
  -H "Content-Type: application/json" \
  -d '{
    "status": "inactive"
  }'
```

**预期结果**:
- HTTP 状态码: 200
- 网站状态变为 inactive

**实际结果**:
```
[ ] 通过
[ ] 失败
记录：______________________________________
```

---

## 第三部分：任务管理 API 测试

### 测试 3.1：创建爬取任务（全量策略）

**测试目的**: 测试全量爬取功能

**请求命令**:
```bash
# 替换 {website_id} 为实际的网站 ID
curl -X POST http://localhost:5000/api/tasks/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "website_id": "{website_id}",
    "strategy": "full",
    "depth": 2,
    "max_links": 100
  }'
```

**预期结果**:
- HTTP 状态码: 202
- 返回任务信息
- 任务状态为 pending
- 任务在后台执行

**实际结果**:
```
[ ] 通过
[ ] 失败
任务ID：______________________________________
记录：______________________________________
```

**等待时间**: 等待 30-60 秒让任务完成

---

### 测试 3.2：查询任务详情

**测试目的**: 验证任务状态查询

**请求命令**:
```bash
# 替换 {task_id} 为实际的任务 ID
curl -X GET http://localhost:5000/api/tasks/{task_id}
```

**预期结果**:
- HTTP 状态码: 200
- 任务状态为 completed（如果已完成）
- 包含统计信息（total_links, valid_links, etc.）

**实际结果**:
```
[ ] 通过
[ ] 失败
任务状态：______________________________________
总链接数：______________________________________
有效链接数：______________________________________
新增链接数：______________________________________
记录：______________________________________
```

---

### 测试 3.3：查询任务列表

**测试目的**: 验证任务列表查询功能

**请求命令**:
```bash
curl -X GET "http://localhost:5000/api/tasks?page=1&page_size=10"
```

**预期结果**:
- HTTP 状态码: 200
- 返回任务列表
- 包含分页信息

**实际结果**:
```
[ ] 通过
[ ] 失败
任务数量：______________________________________
记录：______________________________________
```

---

### 测试 3.4：按网站过滤任务

**测试目的**: 验证任务按网站过滤

**请求命令**:
```bash
# 替换 {website_id} 为实际的网站 ID
curl -X GET "http://localhost:5000/api/tasks?website_id={website_id}&page=1&page_size=10"
```

**预期结果**:
- HTTP 状态码: 200
- 返回指定网站的任务

**实际结果**:
```
[ ] 通过
[ ] 失败
记录：______________________________________
```

---

### 测试 3.5：按状态过滤任务

**测试目的**: 验证任务按状态过滤

**请求命令**:
```bash
curl -X GET "http://localhost:5000/api/tasks?status=completed&page=1&page_size=10"
```

**预期结果**:
- HTTP 状态码: 200
- 返回已完成的任务

**实际结果**:
```
[ ] 通过
[ ] 失败
记录：______________________________________
```

---

### 测试 3.6：查询任务日志

**测试目的**: 验证任务日志查询

**请求命令**:
```bash
# 替换 {task_id} 为实际的任务 ID
curl -X GET "http://localhost:5000/api/tasks/{task_id}/logs?page=1&page_size=50"
```

**预期结果**:
- HTTP 状态码: 200
- 返回任务日志列表
- 包含不同级别的日志（INFO, WARNING, ERROR）

**实际结果**:
```
[ ] 通过
[ ] 失败
日志条数：______________________________________
记录：______________________________________
```

---

### 测试 3.7：按日志级别过滤

**测试目的**: 验证日志级别过滤

**请求命令**:
```bash
# 替换 {task_id} 为实际的任务 ID
curl -X GET "http://localhost:5000/api/tasks/{task_id}/logs?level=INFO"
```

**预期结果**:
- HTTP 状态码: 200
- 仅返回 INFO 级别的日志

**实际结果**:
```
[ ] 通过
[ ] 失败
记录：______________________________________
```

---

### 测试 3.8：创建爬取任务（增量策略）

**测试目的**: 测试增量爬取功能

**请求命令**:
```bash
# 替换 {website_id} 为实际的网站 ID
curl -X POST http://localhost:5000/api/tasks/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "website_id": "{website_id}",
    "strategy": "incremental",
    "depth": 2,
    "max_links": 100
  }'
```

**预期结果**:
- HTTP 状态码: 202
- 返回任务信息
- 任务在后台执行
- 增量模式应该排除已爬取的链接

**实际结果**:
```
[ ] 通过
[ ] 失败
任务ID：______________________________________
记录：______________________________________
```

**等待时间**: 等待 30-60 秒让任务完成

---

### 测试 3.9：验证增量爬取效果

**测试目的**: 验证增量爬取排除了已存在链接

**请求命令**:
```bash
# 替换 {task_id} 为增量任务的 ID
curl -X GET http://localhost:5000/api/tasks/{task_id}
```

**预期结果**:
- HTTP 状态码: 200
- new_links 应该小于 total_links
- 日志中应包含 "排除 X 个已存在链接"

**实际结果**:
```
[ ] 通过
[ ] 失败
新增链接数：______________________________________
总链接数：______________________________________
记录：______________________________________
```

---

### 测试 3.10：并发任务限制

**测试目的**: 验证同一网站不能同时运行多个任务

**请求命令**:
```bash
# 先启动一个任务，然后立即启动第二个任务
# 替换 {website_id} 为实际的网站 ID
curl -X POST http://localhost:5000/api/tasks/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "website_id": "{website_id}",
    "strategy": "full",
    "depth": 2,
    "max_links": 100
  }'

# 立即执行第二个请求
curl -X POST http://localhost:5000/api/tasks/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "website_id": "{website_id}",
    "strategy": "full",
    "depth": 2,
    "max_links": 100
  }'
```

**预期结果**:
- 第一个请求: HTTP 状态码 202
- 第二个请求: HTTP 状态码 409
- 错误消息: "该网站已有正在运行的任务"

**实际结果**:
```
[ ] 通过
[ ] 失败
记录：______________________________________
```

---

## 第四部分：调度管理 API 测试

### 测试 4.1：创建每小时调度

**测试目的**: 测试创建小时级调度任务

**请求命令**:
```bash
# 替换 {website_id} 为实际的网站 ID
curl -X POST http://localhost:5000/api/schedules \
  -H "Content-Type: application/json" \
  -d '{
    "website_id": "{website_id}",
    "name": "每小时增量爬取",
    "schedule_type": "hourly",
    "strategy": "incremental"
  }'
```

**预期结果**:
- HTTP 状态码: 201
- 返回调度信息
- cron_expression 为 "0 * * * *"
- is_active 为 true

**实际结果**:
```
[ ] 通过
[ ] 失败
调度ID：______________________________________
Cron表达式：______________________________________
记录：______________________________________
```

---

### 测试 4.2：创建每天调度

**测试目的**: 测试创建天级调度任务

**请求命令**:
```bash
# 替换 {website_id} 为实际的网站 ID
curl -X POST http://localhost:5000/api/schedules \
  -H "Content-Type: application/json" \
  -d '{
    "website_id": "{website_id}",
    "name": "每天凌晨2点增量爬取",
    "schedule_type": "daily",
    "strategy": "incremental",
    "hour": 2
  }'
```

**预期结果**:
- HTTP 状态码: 201
- cron_expression 为 "0 2 * * *"

**实际结果**:
```
[ ] 通过
[ ] 失败
调度ID：______________________________________
记录：______________________________________
```

---

### 测试 4.3：创建每月调度

**测试目的**: 测试创建月级调度任务

**请求命令**:
```bash
# 替换 {website_id} 为实际的网站 ID
curl -X POST http://localhost:5000/api/schedules \
  -H "Content-Type: application/json" \
  -d '{
    "website_id": "{website_id}",
    "name": "每月1号全量爬取",
    "schedule_type": "monthly",
    "strategy": "full",
    "hour": 0,
    "day": 1
  }'
```

**预期结果**:
- HTTP 状态码: 201
- cron_expression 为 "0 0 1 * *"

**实际结果**:
```
[ ] 通过
[ ] 失败
调度ID：______________________________________
记录：______________________________________
```

---

### 测试 4.4：获取调度列表

**测试目的**: 验证调度列表查询

**请求命令**:
```bash
curl -X GET http://localhost:5000/api/schedules
```

**预期结果**:
- HTTP 状态码: 200
- 返回所有调度任务

**实际结果**:
```
[ ] 通过
[ ] 失败
调度数量：______________________________________
记录：______________________________________
```

---

### 测试 4.5：按网站过滤调度

**测试目的**: 验证按网站过滤调度

**请求命令**:
```bash
# 替换 {website_id} 为实际的网站 ID
curl -X GET "http://localhost:5000/api/schedules?website_id={website_id}"
```

**预期结果**:
- HTTP 状态码: 200
- 返回指定网站的调度

**实际结果**:
```
[ ] 通过
[ ] 失败
记录：______________________________________
```

---

### 测试 4.6：禁用调度

**测试目的**: 测试禁用调度功能

**请求命令**:
```bash
# 替换 {schedule_id} 为实际的调度 ID
curl -X PATCH http://localhost:5000/api/schedules/{schedule_id} \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": false
  }'
```

**预期结果**:
- HTTP 状态码: 200
- is_active 变为 false

**实际结果**:
```
[ ] 通过
[ ] 失败
记录：______________________________________
```

---

### 测试 4.7：启用调度

**测试目的**: 测试启用调度功能

**请求命令**:
```bash
# 替换 {schedule_id} 为实际的调度 ID
curl -X PATCH http://localhost:5000/api/schedules/{schedule_id} \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": true
  }'
```

**预期结果**:
- HTTP 状态码: 200
- is_active 变为 true

**实际结果**:
```
[ ] 通过
[ ] 失败
记录：______________________________________
```

---

### 测试 4.8：删除调度

**测试目的**: 测试删除调度功能

**请求命令**:
```bash
# 替换 {schedule_id} 为实际的调度 ID
curl -X DELETE http://localhost:5000/api/schedules/{schedule_id}
```

**预期结果**:
- HTTP 状态码: 200
- 调度被删除

**实际结果**:
```
[ ] 通过
[ ] 失败
记录：______________________________________
```

---

## 第五部分：数据导出 API 测试

### 测试 5.1：全量导出（CSV 格式）

**测试目的**: 测试全量数据导出为 CSV

**请求命令**:
```bash
# 替换 {website_id} 为实际的网站 ID
curl -X POST http://localhost:5000/api/export \
  -H "Content-Type: application/json" \
  -d '{
    "website_id": "{website_id}",
    "export_type": "full",
    "format": "csv"
  }'
```

**预期结果**:
- HTTP 状态码: 200
- 返回下载 URL 和文件信息
- 文件格式为 CSV

**实际结果**:
```
[ ] 通过
[ ] 失败
文件名：______________________________________
记录数：______________________________________
文件大小：______________________________________
记录：______________________________________
```

---

### 测试 5.2：全量导出（JSON 格式）

**测试目的**: 测试全量数据导出为 JSON

**请求命令**:
```bash
# 替换 {website_id} 为实际的网站 ID
curl -X POST http://localhost:5000/api/export \
  -H "Content-Type: application/json" \
  -d '{
    "website_id": "{website_id}",
    "export_type": "full",
    "format": "json"
  }'
```

**预期结果**:
- HTTP 状态码: 200
- 文件格式为 JSON

**实际结果**:
```
[ ] 通过
[ ] 失败
文件名：______________________________________
记录：______________________________________
```

---

### 测试 5.3：增量导出

**测试目的**: 测试增量数据导出

**请求命令**:
```bash
# 替换 {website_id} 为实际的网站 ID
curl -X POST http://localhost:5000/api/export \
  -H "Content-Type: application/json" \
  -d '{
    "website_id": "{website_id}",
    "export_type": "incremental",
    "format": "csv",
    "since_date": "2025-10-20T00:00:00Z"
  }'
```

**预期结果**:
- HTTP 状态码: 200
- 仅导出指定日期之后的数据

**实际结果**:
```
[ ] 通过
[ ] 失败
记录数：______________________________________
记录：______________________________________
```

---

### 测试 5.4：按链接类型过滤导出

**测试目的**: 测试按链接类型过滤导出

**请求命令**:
```bash
# 替换 {website_id} 为实际的网站 ID
curl -X POST http://localhost:5000/api/export \
  -H "Content-Type: application/json" \
  -d '{
    "website_id": "{website_id}",
    "export_type": "full",
    "format": "csv",
    "filters": {
      "link_type": "valid"
    }
  }'
```

**预期结果**:
- HTTP 状态码: 200
- 仅导出有效链接

**实际结果**:
```
[ ] 通过
[ ] 失败
记录数：______________________________________
记录：______________________________________
```

---

### 测试 5.5：下载导出文件

**测试目的**: 测试文件下载功能

**请求命令**:
```bash
# 替换 {filename} 为实际的文件名
curl -O http://localhost:5000/api/export/download/{filename}
```

**预期结果**:
- HTTP 状态码: 200
- 文件成功下载

**实际结果**:
```
[ ] 通过
[ ] 失败
文件大小：______________________________________
记录：______________________________________
```

---

### 测试 5.6：下载不存在的文件

**测试目的**: 测试错误处理

**请求命令**:
```bash
curl -X GET http://localhost:5000/api/export/download/nonexistent_file.csv
```

**预期结果**:
- HTTP 状态码: 404
- 错误消息: "文件不存在"

**实际结果**:
```
[ ] 通过
[ ] 失败
记录：______________________________________
```

---

## 第六部分：统计查询 API 测试

### 测试 6.1：获取统计数据（无日期范围）

**测试目的**: 测试获取所有时间的统计数据

**请求命令**:
```bash
# 替换 {website_id} 为实际的网站 ID
curl -X GET "http://localhost:5000/api/statistics?website_id={website_id}"
```

**预期结果**:
- HTTP 状态码: 200
- 返回统计数据摘要
- 包含任务数、链接数、有效率等

**实际结果**:
```
[ ] 通过
[ ] 失败
总任务数：______________________________________
已完成任务数：______________________________________
总链接数：______________________________________
新增链接数：______________________________________
重要链接占比：______________________________________
平均精准率：______________________________________
记录：______________________________________
```

---

### 测试 6.2：获取统计数据（指定日期范围）

**测试目的**: 测试按日期范围查询统计数据

**请求命令**:
```bash
# 替换 {website_id} 为实际的网站 ID
curl -X GET "http://localhost:5000/api/statistics?website_id={website_id}&date_from=2025-10-01T00:00:00Z&date_to=2025-10-24T23:59:59Z"
```

**预期结果**:
- HTTP 状态码: 200
- 返回指定日期范围内的统计数据

**实际结果**:
```
[ ] 通过
[ ] 失败
记录：______________________________________
```

---

### 测试 6.3：统计数据验证（网站不存在）

**测试目的**: 测试不存在的网站

**请求命令**:
```bash
curl -X GET "http://localhost:5000/api/statistics?website_id=507f1f77bcf86cd799439999"
```

**预期结果**:
- HTTP 状态码: 404
- 错误消息: "网站不存在"

**实际结果**:
```
[ ] 通过
[ ] 失败
记录：______________________________________
```

---

## 第七部分：删除操作测试

### 测试 7.1：删除网站

**测试目的**: 测试删除网站功能

**请求命令**:
```bash
# 替换 {website_id} 为实际的网站 ID
curl -X DELETE http://localhost:5000/api/websites/{website_id}
```

**预期结果**:
- HTTP 状态码: 200
- 网站被删除
- 相关数据保留（任务、链接）

**实际结果**:
```
[ ] 通过
[ ] 失败
记录：______________________________________
```

---

### 测试 7.2：删除不存在的网站

**测试目的**: 测试删除不存在的网站

**请求命令**:
```bash
curl -X DELETE http://localhost:5000/api/websites/507f1f77bcf86cd799439999
```

**预期结果**:
- HTTP 状态码: 404
- 错误消息: "网站不存在"

**实际结果**:
```
[ ] 通过
[ ] 失败
记录：______________________________________
```

---

## 测试脚本

为了方便测试，以下是一个完整的测试脚本，可以按顺序执行所有测试：

```bash
#!/bin/bash

# 配置
BASE_URL="http://localhost:5000"
WEBSITE_ID=""
TASK_ID=""
SCHEDULE_ID=""

echo "=========================================="
echo "网页链接爬虫系统 API 测试脚本"
echo "=========================================="
echo ""

# 1. 健康检查
echo "1. 测试健康检查..."
curl -X GET $BASE_URL/api/health
echo -e "\n"

# 2. 创建网站
echo "2. 创建测试网站..."
RESPONSE=$(curl -s -X POST $BASE_URL/api/websites \
  -H "Content-Type: application/json" \
  -d '{
    "name": "百度测试",
    "url": "https://www.baidu.com",
    "crawl_depth": 2,
    "max_links": 100
  }')
echo $RESPONSE
WEBSITE_ID=$(echo $RESPONSE | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
echo "网站ID: $WEBSITE_ID"
echo -e "\n"

# 3. 获取网站列表
echo "3. 获取网站列表..."
curl -s -X GET "$BASE_URL/api/websites?page=1&page_size=10"
echo -e "\n"

# 4. 创建全量爬取任务
echo "4. 创建全量爬取任务（深度=2）..."
RESPONSE=$(curl -s -X POST $BASE_URL/api/tasks/crawl \
  -H "Content-Type: application/json" \
  -d "{
    \"website_id\": \"$WEBSITE_ID\",
    \"strategy\": \"full\",
    \"depth\": 2,
    \"max_links\": 100
  }")
echo $RESPONSE
TASK_ID=$(echo $RESPONSE | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
echo "任务ID: $TASK_ID"
echo -e "\n"

# 5. 等待任务完成
echo "5. 等待任务完成（60秒）..."
sleep 60
echo -e "\n"

# 6. 查询任务详情
echo "6. 查询任务详情..."
curl -s -X GET "$BASE_URL/api/tasks/$TASK_ID"
echo -e "\n"

# 7. 查询任务日志
echo "7. 查询任务日志..."
curl -s -X GET "$BASE_URL/api/tasks/$TASK_ID/logs?page=1&page_size=10"
echo -e "\n"

# 8. 创建增量爬取任务
echo "8. 创建增量爬取任务（深度=2）..."
RESPONSE=$(curl -s -X POST $BASE_URL/api/tasks/crawl \
  -H "Content-Type: application/json" \
  -d "{
    \"website_id\": \"$WEBSITE_ID\",
    \"strategy\": \"incremental\",
    \"depth\": 2,
    \"max_links\": 100
  }")
echo $RESPONSE
echo -e "\n"

# 9. 创建调度任务
echo "9. 创建每日调度任务..."
RESPONSE=$(curl -s -X POST $BASE_URL/api/schedules \
  -H "Content-Type: application/json" \
  -d "{
    \"website_id\": \"$WEBSITE_ID\",
    \"name\": \"每日增量爬取\",
    \"schedule_type\": \"daily\",
    \"strategy\": \"incremental\",
    \"hour\": 2
  }")
echo $RESPONSE
SCHEDULE_ID=$(echo $RESPONSE | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
echo "调度ID: $SCHEDULE_ID"
echo -e "\n"

# 10. 获取调度列表
echo "10. 获取调度列表..."
curl -s -X GET "$BASE_URL/api/schedules?website_id=$WEBSITE_ID"
echo -e "\n"

# 11. 导出数据
echo "11. 导出数据（CSV格式）..."
curl -s -X POST $BASE_URL/api/export \
  -H "Content-Type: application/json" \
  -d "{
    \"website_id\": \"$WEBSITE_ID\",
    \"export_type\": \"full\",
    \"format\": \"csv\"
  }"
echo -e "\n"

# 12. 获取统计数据
echo "12. 获取统计数据..."
curl -s -X GET "$BASE_URL/api/statistics?website_id=$WEBSITE_ID"
echo -e "\n"

echo "=========================================="
echo "测试完成！"
echo "=========================================="
echo ""
echo "保存的ID："
echo "  网站ID: $WEBSITE_ID"
echo "  任务ID: $TASK_ID"
echo "  调度ID: $SCHEDULE_ID"
```

保存为 `run_tests.sh`，然后执行：

```bash
chmod +x run_tests.sh
./run_tests.sh
```

---

## 测试结果总结

### 测试环境信息

- 测试日期: _______________
- 测试人员: _______________
- 服务器版本: _______________
- 数据库版本: _______________

### 测试统计

| 测试分类 | 总数 | 通过 | 失败 | 通过率 |
|---------|------|------|------|--------|
| 系统信息 API | 2 | ___ | ___ | ___% |
| 网站管理 API | 8 | ___ | ___ | ___% |
| 任务管理 API | 10 | ___ | ___ | ___% |
| 调度管理 API | 8 | ___ | ___ | ___% |
| 数据导出 API | 6 | ___ | ___ | ___% |
| 统计查询 API | 3 | ___ | ___ | ___% |
| 删除操作 | 2 | ___ | ___ | ___% |
| **总计** | **39** | ___ | ___ | ___% |

### 主要问题记录

1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

### 性能数据

- 平均任务执行时间（深度=2）: _______________ 秒
- 平均爬取链接数（深度=2）: _______________ 个
- 重要链接占比: _______________%
- 平均精准率: _______________%

### 建议和改进

1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

---

## 附录：常见问题

### Q1: 任务一直是 pending 状态？
A: 检查后台线程是否正常启动，查看服务器日志。

### Q2: 爬取任务执行时间过长？
A: 调整 depth 和 max_links 参数，减少爬取范围。

### Q3: 增量爬取没有跳过已存在链接？
A: 检查数据库中是否有该网站的历史数据，查看任务日志。

### Q4: 导出文件为空？
A: 检查是否有爬取数据，查看 export_type 和 filters 参数。

### Q5: 调度任务没有自动执行？
A: 检查调度器是否启动，is_active 是否为 true，cron 表达式是否正确。

---

**测试完成日期**: _______________

**测试人员签名**: _______________
