# API 文档

## 概述

这是网页链接爬虫系统的 RESTful API 文档。所有 API 都遵循统一的响应格式。

**基础 URL**: `http://localhost:5000`

**响应格式**:

成功响应：
```json
{
  "success": true,
  "message": "操作成功",
  "data": { ... }
}
```

错误响应：
```json
{
  "success": false,
  "message": "错误描述"
}
```

分页响应：
```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5
  }
}
```

---

## 目录

1. [系统信息 API](#系统信息-api)
2. [网站管理 API](#网站管理-api)
3. [任务管理 API](#任务管理-api)
4. [调度管理 API](#调度管理-api)
5. [数据导出 API](#数据导出-api)
6. [统计查询 API](#统计查询-api)

---

## 系统信息 API

### 1. 获取系统信息

获取 API 的基本信息和可用端点。

**请求**

```http
GET /api
```

**响应**

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

### 2. 健康检查

检查服务和数据库连接状态。

**请求**

```http
GET /api/health
```

**响应**

成功：
```json
{
  "status": "healthy",
  "database": "connected",
  "message": "服务运行正常"
}
```

失败：
```json
{
  "status": "unhealthy",
  "database": "disconnected",
  "message": "数据库连接失败: ..."
}
```

---

## 网站管理 API

### 1. 创建网站

添加一个新网站到系统中。

**请求**

```http
POST /api/websites
Content-Type: application/json
```

**请求体**

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| name | string | 是 | - | 网站名称 |
| url | string | 是 | - | 网站完整 URL（需要 http/https 协议） |
| crawl_depth | integer | 否 | 3 | 爬取深度 |
| max_links | integer | 否 | 1000 | 最大链接数限制 |

**请求示例**

```json
{
  "name": "百度",
  "url": "https://www.baidu.com",
  "crawl_depth": 3,
  "max_links": 1000
}
```

**响应**

```json
{
  "success": true,
  "message": "网站创建成功",
  "data": {
    "id": "507f1f77bcf86cd799439011",
    "name": "百度",
    "url": "https://www.baidu.com",
    "domain": "www.baidu.com",
    "status": "active",
    "crawl_depth": 3,
    "max_links": 1000,
    "created_at": "2025-10-22T10:00:00Z",
    "updated_at": "2025-10-22T10:00:00Z"
  }
}
```

**错误码**

- `400`: 参数验证失败（名称或 URL 为空、URL 格式无效）
- `409`: 该网站 URL 已存在
- `500`: 服务器内部错误

---

### 2. 获取网站列表

获取所有网站的列表（支持分页和过滤）。

**请求**

```http
GET /api/websites?status=active&page=1&page_size=20
```

**查询参数**

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| status | string | 否 | - | 状态过滤（active/inactive） |
| page | integer | 否 | 1 | 页码 |
| page_size | integer | 否 | 20 | 每页大小 |

**响应**

```json
{
  "success": true,
  "data": [
    {
      "id": "507f1f77bcf86cd799439011",
      "name": "百度",
      "url": "https://www.baidu.com",
      "domain": "www.baidu.com",
      "status": "active",
      "crawl_depth": 3,
      "max_links": 1000,
      "created_at": "2025-10-22T10:00:00Z",
      "updated_at": "2025-10-22T10:00:00Z"
    }
  ],
  "pagination": {
    "total": 50,
    "page": 1,
    "page_size": 20,
    "total_pages": 3
  }
}
```

---

### 3. 获取网站详情

获取指定网站的详细信息。

**请求**

```http
GET /api/websites/{website_id}
```

**路径参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| website_id | string | 是 | 网站 ID（ObjectId） |

**响应**

```json
{
  "success": true,
  "data": {
    "id": "507f1f77bcf86cd799439011",
    "name": "百度",
    "url": "https://www.baidu.com",
    "domain": "www.baidu.com",
    "status": "active",
    "crawl_depth": 3,
    "max_links": 1000,
    "created_at": "2025-10-22T10:00:00Z",
    "updated_at": "2025-10-22T10:00:00Z"
  }
}
```

**错误码**

- `400`: 网站 ID 格式无效
- `404`: 网站不存在
- `500`: 服务器内部错误

---

### 4. 更新网站

更新网站的配置信息。

**请求**

```http
PUT /api/websites/{website_id}
Content-Type: application/json
```

**路径参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| website_id | string | 是 | 网站 ID（ObjectId） |

**请求体**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| name | string | 否 | 网站名称 |
| status | string | 否 | 状态（active/inactive） |
| crawl_depth | integer | 否 | 爬取深度 |
| max_links | integer | 否 | 最大链接数限制 |

**请求示例**

```json
{
  "name": "百度搜索",
  "status": "inactive",
  "crawl_depth": 5,
  "max_links": 2000
}
```

**响应**

```json
{
  "success": true,
  "message": "网站更新成功",
  "data": {
    "id": "507f1f77bcf86cd799439011",
    "name": "百度搜索",
    "url": "https://www.baidu.com",
    "domain": "www.baidu.com",
    "status": "inactive",
    "crawl_depth": 5,
    "max_links": 2000,
    "created_at": "2025-10-22T10:00:00Z",
    "updated_at": "2025-10-22T11:00:00Z"
  }
}
```

**错误码**

- `400`: 网站 ID 格式无效或参数验证失败
- `404`: 网站不存在
- `500`: 服务器内部错误

---

### 5. 根据URL查询网站

根据完整的URL查询网站信息和ID。

**请求**

```http
GET /api/websites/by-url?url={website_url}
```

**查询参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| url | string | 是 | 网站完整URL（需要URL编码） |

**请求示例**

```bash
GET /api/websites/by-url?url=https%3A%2F%2Fwww.baidu.com
```

**响应**

```json
{
  "success": true,
  "data": {
    "id": "507f1f77bcf86cd799439011",
    "name": "百度",
    "url": "https://www.baidu.com",
    "domain": "www.baidu.com",
    "status": "active",
    "crawl_depth": 3,
    "max_links": 1000,
    "created_at": "2025-10-22T10:00:00Z",
    "updated_at": "2025-10-22T10:00:00Z"
  }
}
```

**错误码**

- `400`: URL参数为空或格式无效
- `404`: 未找到该URL对应的网站
- `500`: 服务器内部错误

**使用场景**

- 在批量导入前检查URL是否已存在
- 通过URL快速获取网站ID用于后续操作
- 验证URL是否已在系统中注册

---

### 6. 删除网站

删除指定的网站（不会删除相关的任务和链接数据）。

**请求**

```http
DELETE /api/websites/{website_id}
```

**路径参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| website_id | string | 是 | 网站 ID（ObjectId） |

**响应**

```json
{
  "success": true,
  "message": "网站删除成功"
}
```

**错误码**

- `400`: 网站 ID 格式无效
- `404`: 网站不存在
- `500`: 服务器内部错误

---

## 任务管理 API

### 1. 创建爬取任务

手动启动一个爬取任务（支持增量和全量两种策略）。

**请求**

```http
POST /api/tasks/crawl
Content-Type: application/json
```

**请求体**

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| website_id | string | 是 | - | 网站 ID（ObjectId） |
| strategy | string | 是 | - | 爬取策略（incremental/full） |
| depth | integer | 否 | 网站配置 | 爬取深度 |
| max_links | integer | 否 | 网站配置 | 最大链接数 |

**请求示例**

```json
{
  "website_id": "507f1f77bcf86cd799439011",
  "strategy": "incremental",
  "depth": 3,
  "max_links": 1000
}
```

**响应**

```json
{
  "success": true,
  "message": "爬取任务已创建并开始执行",
  "data": {
    "id": "507f1f77bcf86cd799439012",
    "website_id": "507f1f77bcf86cd799439011",
    "task_type": "manual",
    "strategy": "incremental",
    "status": "pending",
    "started_at": null,
    "completed_at": null,
    "statistics": {
      "total_links": 0,
      "valid_links": 0,
      "invalid_links": 0,
      "new_links": 0,
      "valid_rate": 0.0,
      "precision_rate": 0.0
    },
    "error_message": null
  }
}
```

**策略说明**

- **incremental（增量）**: 仅爬取新链接，跳过已存在的链接
- **full（全量）**: 重新爬取所有链接

**错误码**

- `400`: 参数验证失败（网站 ID 或策略为空、策略值不正确）
- `404`: 网站不存在
- `409`: 该网站已有正在运行的任务
- `500`: 服务器内部错误

---

### 2. 获取任务列表

获取爬取任务列表（支持分页和过滤）。

**请求**

```http
GET /api/tasks?website_id=xxx&status=completed&page=1&page_size=20
```

**查询参数**

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| website_id | string | 否 | - | 网站 ID 过滤 |
| status | string | 否 | - | 状态过滤（pending/running/completed/failed/cancelled） |
| page | integer | 否 | 1 | 页码 |
| page_size | integer | 否 | 20 | 每页大小 |

**响应**

```json
{
  "success": true,
  "data": [
    {
      "id": "507f1f77bcf86cd799439012",
      "website_id": "507f1f77bcf86cd799439011",
      "task_type": "manual",
      "strategy": "incremental",
      "status": "completed",
      "started_at": "2025-10-22T10:00:00Z",
      "completed_at": "2025-10-22T10:05:30Z",
      "statistics": {
        "total_links": 100,
        "valid_links": 85,
        "invalid_links": 15,
        "new_links": 50,
        "valid_rate": 0.85,
        "precision_rate": 0.95
      },
      "error_message": null
    }
  ],
  "pagination": {
    "total": 30,
    "page": 1,
    "page_size": 20,
    "total_pages": 2
  }
}
```

---

### 3. 获取任务详情

获取指定任务的详细信息。

**请求**

```http
GET /api/tasks/{task_id}
```

**路径参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| task_id | string | 是 | 任务 ID（ObjectId） |

**响应**

```json
{
  "success": true,
  "data": {
    "id": "507f1f77bcf86cd799439012",
    "website_id": "507f1f77bcf86cd799439011",
    "task_type": "manual",
    "strategy": "incremental",
    "status": "completed",
    "started_at": "2025-10-22T10:00:00Z",
    "completed_at": "2025-10-22T10:05:30Z",
    "statistics": {
      "total_links": 100,
      "valid_links": 85,
      "invalid_links": 15,
      "new_links": 50,
      "valid_rate": 0.85,
      "precision_rate": 0.95
    },
    "error_message": null
  }
}
```

**错误码**

- `400`: 任务 ID 格式无效
- `404`: 任务不存在
- `500`: 服务器内部错误

---

### 4. 获取任务日志

获取指定任务的执行日志。

**请求**

```http
GET /api/tasks/{task_id}/logs?level=INFO&page=1&page_size=50
```

**路径参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| task_id | string | 是 | 任务 ID（ObjectId） |

**查询参数**

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| level | string | 否 | - | 日志级别过滤（INFO/WARNING/ERROR） |
| page | integer | 否 | 1 | 页码 |
| page_size | integer | 否 | 50 | 每页大小 |

**响应**

```json
{
  "success": true,
  "data": [
    {
      "id": "507f1f77bcf86cd799439013",
      "task_id": "507f1f77bcf86cd799439012",
      "level": "INFO",
      "message": "开始爬取任务 - 策略: incremental",
      "details": {},
      "created_at": "2025-10-22T10:00:00Z"
    },
    {
      "id": "507f1f77bcf86cd799439014",
      "task_id": "507f1f77bcf86cd799439012",
      "level": "INFO",
      "message": "增量模式：排除 500 个已存在链接",
      "details": {},
      "created_at": "2025-10-22T10:00:01Z"
    },
    {
      "id": "507f1f77bcf86cd799439015",
      "task_id": "507f1f77bcf86cd799439012",
      "level": "INFO",
      "message": "爬取任务完成 - 总链接: 100, 新增: 50",
      "details": {},
      "created_at": "2025-10-22T10:05:30Z"
    }
  ],
  "pagination": {
    "total": 15,
    "page": 1,
    "page_size": 50,
    "total_pages": 1
  }
}
```

**错误码**

- `400`: 任务 ID 格式无效
- `500`: 服务器内部错误

---

### 5. 取消运行中的任务

强制取消正在运行的爬取任务。

**请求**

```http
POST /api/tasks/{task_id}/cancel
```

**路径参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| task_id | string | 是 | 任务 ID（ObjectId） |

**响应**

```json
{
  "success": true,
  "message": "任务已强制取消",
  "data": {
    "task_id": "507f1f77bcf86cd799439012",
    "status": "cancelled"
  }
}
```

**说明**

- 只能取消状态为 `running` 的任务
- 取消操作是强制的，任务状态会立即更新为 `cancelled`
- 后台线程会在下一个检查点检测到取消信号并停止执行
- 已经完成的数据保存操作不会回滚

**错误码**

- `400`: 任务 ID 格式无效或任务状态不允许取消
- `404`: 任务不存在
- `500`: 服务器内部错误

---

### 6. 删除任务

删除指定的爬取任务及其相关日志。

**请求**

```http
DELETE /api/tasks/{task_id}
```

**路径参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| task_id | string | 是 | 任务 ID（ObjectId） |

**响应**

```json
{
  "success": true,
  "message": "任务及相关数据已删除",
  "data": {
    "task_id": "507f1f77bcf86cd799439012"
  }
}
```

**说明**

- 不能删除状态为 `running` 的任务，必须先取消任务
- 删除任务会同时删除该任务的所有日志记录
- 已爬取的链接数据不会被删除

**错误码**

- `400`: 任务 ID 格式无效
- `404`: 任务不存在
- `409`: 任务正在运行，无法删除
- `500`: 服务器内部错误

---

## 调度管理 API

### 1. 创建调度任务

创建一个定时爬取任务。

**请求**

```http
POST /api/schedules
Content-Type: application/json
```

**请求体**

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| website_id | string | 是 | - | 网站 ID（ObjectId） |
| name | string | 是 | - | 调度任务名称 |
| schedule_type | string | 是 | - | 调度类型（hourly/daily/monthly） |
| strategy | string | 否 | incremental | 爬取策略（incremental/full） |
| hour | integer | 否 | 2 | 小时（用于 daily 和 monthly） |
| day | integer | 否 | 1 | 日期（用于 monthly，1-31） |

**请求示例**

```json
{
  "website_id": "507f1f77bcf86cd799439011",
  "name": "百度每日增量爬取",
  "schedule_type": "daily",
  "strategy": "incremental",
  "hour": 2
}
```

**响应**

```json
{
  "success": true,
  "message": "调度任务创建成功",
  "data": {
    "id": "507f1f77bcf86cd799439016",
    "website_id": "507f1f77bcf86cd799439011",
    "name": "百度每日增量爬取",
    "schedule_type": "daily",
    "cron_expression": "0 2 * * *",
    "strategy": "incremental",
    "is_active": true,
    "next_run_time": null,
    "last_run_time": null,
    "created_at": "2025-10-22T10:00:00Z"
  }
}
```

**调度类型说明**

- **hourly**: 每小时执行（cron: `0 * * * *`）
- **daily**: 每天指定时间执行（cron: `0 {hour} * * *`）
- **monthly**: 每月指定日期和时间执行（cron: `0 {hour} {day} * *`）

**错误码**

- `400`: 参数验证失败
- `404`: 网站不存在
- `500`: 服务器内部错误

---

### 2. 获取调度列表

获取所有调度任务列表。

**请求**

```http
GET /api/schedules?website_id=xxx
```

**查询参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| website_id | string | 否 | 网站 ID 过滤 |

**响应**

```json
{
  "success": true,
  "data": [
    {
      "id": "507f1f77bcf86cd799439016",
      "website_id": "507f1f77bcf86cd799439011",
      "name": "百度每日增量爬取",
      "schedule_type": "daily",
      "cron_expression": "0 2 * * *",
      "strategy": "incremental",
      "is_active": true,
      "next_run_time": "2025-10-23T02:00:00Z",
      "last_run_time": "2025-10-22T02:00:00Z",
      "created_at": "2025-10-22T10:00:00Z"
    }
  ]
}
```

---

### 3. 更新调度状态

启用或禁用调度任务。

**请求**

```http
PATCH /api/schedules/{schedule_id}
Content-Type: application/json
```

**路径参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| schedule_id | string | 是 | 调度 ID（ObjectId） |

**请求体**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| is_active | boolean | 是 | 是否激活 |

**请求示例**

```json
{
  "is_active": false
}
```

**响应**

```json
{
  "success": true,
  "message": "调度更新成功",
  "data": {
    "id": "507f1f77bcf86cd799439016",
    "website_id": "507f1f77bcf86cd799439011",
    "name": "百度每日增量爬取",
    "schedule_type": "daily",
    "cron_expression": "0 2 * * *",
    "strategy": "incremental",
    "is_active": false,
    "next_run_time": "2025-10-23T02:00:00Z",
    "last_run_time": "2025-10-22T02:00:00Z",
    "created_at": "2025-10-22T10:00:00Z"
  }
}
```

**错误码**

- `400`: 调度 ID 格式无效
- `404`: 调度不存在
- `500`: 服务器内部错误

---

### 4. 删除调度

删除指定的调度任务。

**请求**

```http
DELETE /api/schedules/{schedule_id}
```

**路径参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| schedule_id | string | 是 | 调度 ID（ObjectId） |

**响应**

```json
{
  "success": true,
  "message": "调度删除成功"
}
```

**错误码**

- `400`: 调度 ID 格式无效
- `404`: 调度不存在
- `500`: 服务器内部错误

---

## 数据导出 API

### 1. 导出爬取数据

导出指定网站的爬取数据（支持 CSV 和 JSON 格式）。

**请求**

```http
POST /api/export
Content-Type: application/json
```

**请求体**

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| website_id | string | 是 | - | 网站 ID（ObjectId） |
| export_type | string | 是 | - | 导出类型（incremental/full） |
| format | string | 否 | csv | 导出格式（csv/json） |
| since_date | string | 否 | - | 起始日期（ISO 8601 格式，仅用于增量导出） |
| filters | object | 否 | {} | 过滤条件 |
| filters.link_type | string | 否 | - | 链接类型（valid/invalid） |
| filters.domain | string | 否 | - | 域名过滤 |

**请求示例**

```json
{
  "website_id": "507f1f77bcf86cd799439011",
  "export_type": "incremental",
  "format": "csv",
  "since_date": "2025-10-20T00:00:00Z",
  "filters": {
    "link_type": "valid"
  }
}
```

**响应**

```json
{
  "success": true,
  "message": "数据导出成功",
  "data": {
    "download_url": "/api/export/download/export_507f1f77bcf86cd799439011_20251022_100000.csv",
    "file_name": "export_507f1f77bcf86cd799439011_20251022_100000.csv",
    "total_records": 850,
    "file_size": "125.43 KB"
  }
}
```

**导出类型说明**

- **incremental（增量）**: 导出指定日期之后的新增链接
- **full（全量）**: 导出所有链接

**导出格式说明**

- **csv**: CSV 格式（包含字段：url, domain, link_type, status_code, last_crawled_at）
- **json**: JSON 格式（包含完整的文档信息）

**错误码**

- `400`: 参数验证失败
- `500`: 服务器内部错误

---

### 2. 下载导出文件

下载已生成的导出文件。

**请求**

```http
GET /api/export/download/{filename}
```

**路径参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| filename | string | 是 | 文件名 |

**响应**

文件下载（application/octet-stream）

**错误码**

- `404`: 文件不存在
- `500`: 服务器内部错误

---

## 统计查询 API

### 1. 获取统计数据

获取指定网站的爬取统计数据。

**请求**

```http
GET /api/statistics?website_id=xxx&date_from=2025-10-01&date_to=2025-10-22
```

**查询参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| website_id | string | 是 | 网站 ID（ObjectId） |
| date_from | string | 否 | 开始日期（ISO 8601 格式） |
| date_to | string | 否 | 结束日期（ISO 8601 格式） |

**响应**

```json
{
  "success": true,
  "data": {
    "website": {
      "id": "507f1f77bcf86cd799439011",
      "name": "百度"
    },
    "period": {
      "from": "2025-10-01",
      "to": "2025-10-22"
    },
    "summary": {
      "total_tasks": 30,
      "completed_tasks": 28,
      "failed_tasks": 2,
      "total_links_crawled": 2500,
      "new_links_found": 1200,
      "avg_valid_rate": 0.8571,
      "avg_precision_rate": 0.9429
    }
  }
}
```

**统计指标说明**

- **total_tasks**: 总任务数
- **completed_tasks**: 已完成任务数
- **failed_tasks**: 失败任务数
- **total_links_crawled**: 爬取的总链接数
- **new_links_found**: 新增链接数（增量任务）
- **avg_valid_rate**: 重要链接占比（有效链接 / 总链接）
- **avg_precision_rate**: 平均精准率（成功下载 / 有效链接）

**错误码**

- `400`: 参数验证失败（网站 ID 格式无效或为空）
- `404`: 网站不存在
- `500`: 服务器内部错误

---

## 错误码汇总

| 状态码 | 描述 |
|-------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 202 | 已接受（异步任务） |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 409 | 资源冲突（如 URL 已存在、任务已运行） |
| 500 | 服务器内部错误 |

---

## 使用示例

### 完整工作流程示例

#### 1. 添加网站

```bash
curl -X POST http://localhost:5000/api/websites \
  -H "Content-Type: application/json" \
  -d '{
    "name": "百度",
    "url": "https://www.baidu.com",
    "crawl_depth": 3,
    "max_links": 1000
  }'
```

#### 2. 创建爬取任务（增量）

```bash
curl -X POST http://localhost:5000/api/tasks/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "website_id": "507f1f77bcf86cd799439011",
    "strategy": "incremental"
  }'
```

#### 3. 查看任务状态

```bash
curl http://localhost:5000/api/tasks/507f1f77bcf86cd799439012
```

#### 4. 查看任务日志

```bash
curl http://localhost:5000/api/tasks/507f1f77bcf86cd799439012/logs
```

#### 5. 创建定时任务（每天凌晨 2 点）

```bash
curl -X POST http://localhost:5000/api/schedules \
  -H "Content-Type: application/json" \
  -d '{
    "website_id": "507f1f77bcf86cd799439011",
    "name": "百度每日增量爬取",
    "schedule_type": "daily",
    "strategy": "incremental",
    "hour": 2
  }'
```

#### 6. 导出数据

```bash
curl -X POST http://localhost:5000/api/export \
  -H "Content-Type: application/json" \
  -d '{
    "website_id": "507f1f77bcf86cd799439011",
    "export_type": "incremental",
    "format": "csv",
    "since_date": "2025-10-20T00:00:00Z"
  }'
```

#### 7. 下载导出文件

```bash
curl -O http://localhost:5000/api/export/download/export_507f1f77bcf86cd799439011_20251022_100000.csv
```

#### 8. 查看统计数据

```bash
curl "http://localhost:5000/api/statistics?website_id=507f1f77bcf86cd799439011&date_from=2025-10-01&date_to=2025-10-22"
```

---

## 注意事项

1. **ObjectId 格式**: 所有 ID 参数都使用 MongoDB 的 ObjectId 格式（24 位十六进制字符串）

2. **时间格式**: 所有时间字段使用 ISO 8601 格式（例如：`2025-10-22T10:00:00Z`）

3. **异步任务**: 爬取任务是异步执行的，创建任务后立即返回 202 状态码，需要通过查询任务详情接口获取执行结果

4. **并发限制**: 同一网站同时只能有一个正在运行的爬取任务

5. **分页**: 列表接口都支持分页，建议使用合理的 `page_size` 参数避免一次加载过多数据

6. **日志查询**: 任务日志支持按级别过滤，建议根据需要选择合适的日志级别

7. **文件下载**: 导出的文件会保存在服务器的 `exports` 目录中，可以通过下载接口获取

8. **调度器**: 调度任务在应用启动时自动加载，修改调度配置后需要重启应用才能生效

---

## 版本历史

### v1.0.0 (2025-10-22)

- 初始版本发布
- 实现网站管理 API
- 实现任务管理 API（支持增量和全量策略）
- 实现调度管理 API
- 实现数据导出 API（支持 CSV 和 JSON 格式）
- 实现统计查询 API
- 集成 MongoDB 数据库
- 实现 APScheduler 定时任务调度

---

## 联系方式

如有问题或建议，请通过以下方式联系：

- 项目仓库: [GitHub](https://github.com/your-repo)
- 问题反馈: [Issues](https://github.com/your-repo/issues)

---

**文档生成时间**: 2025-10-24

**API 版本**: v1.0.0
