# 网页链接爬虫系统

一个功能完善的网页链接爬虫系统，支持定时调度、数据持久化、增量/全量爬取策略，并提供友好的 Web 管理界面。

## 项目简介

本项目将简单的爬虫脚本升级为支持多网站管理、定时任务调度、数据可视化的完整 Web 服务系统。

### 核心特性

- 🕷️ **智能爬虫**: 支持递归爬取，自动提取网页中的所有链接资源
- 📊 **数据管理**: MongoDB 持久化存储，支持增量和全量两种爬取策略
- ⏰ **定时调度**: 基于 APScheduler 的任务调度系统，支持小时/天/月级定时任务
- 🎯 **任务控制**: 实时任务监控，支持取消和删除操作
- 📈 **数据统计**: 爬取统计、有效率分析、链接分类等
- 📤 **数据导出**: 支持 CSV、JSON、Excel 格式导出
- 🎨 **现代前端**: 基于 Vue 3 的响应式管理界面

## 技术栈

### 后端
- **Flask**: Web 框架
- **MongoDB**: 数据库
- **APScheduler**: 定时任务调度
- **Requests + BeautifulSoup**: 网页爬取和解析
- **Selenium**: 动态网页截图（可选）

### 前端
- **Vue 3**: 前端框架
- **Element Plus**: UI 组件库
- **TailwindCSS**: 样式框架
- **Vite**: 构建工具
- **TypeScript**: 类型支持

## 快速开始

### 环境要求

- Python 3.8+
- MongoDB 4.0+
- Node.js 16+ (前端开发)
- pnpm (前端包管理器)

### 安装步骤

#### 1. 克隆仓库

```bash
git clone <repository_url>
cd fetch_link_from_website
```

#### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置以下参数：

```ini
# MongoDB 配置
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB_NAME=crawler_db

# Flask 配置
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=True
```

#### 3. 安装后端依赖

```bash
pip install -r requirements.txt
```

#### 4. 启动后端服务

```bash
python run.py
```

服务将在 `http://localhost:9999` 启动。

#### 5. 前端开发（可选）

```bash
cd frontend
pnpm install
pnpm dev
```

前端开发服务器将在 `http://localhost:8848` 启动。

生产环境部署：

```bash
cd frontend
pnpm build
# 构建产物会自动复制到 web/ 目录
```

## 项目结构

```
.
├── app/                      # 后端应用
│   ├── __init__.py          # Flask 应用工厂
│   ├── config.py            # 全局配置
│   ├── database.py          # MongoDB 连接
│   ├── global_vars.py       # 全局变量管理
│   ├── models/              # 数据模型
│   │   ├── website.py       # 网站模型
│   │   ├── crawl_task.py    # 爬取任务模型
│   │   ├── crawled_link.py  # 爬取链接模型
│   │   └── ...
│   ├── services/            # 业务逻辑
│   │   └── crawler_service.py  # 爬虫服务
│   ├── api/                 # API 路由
│   │   ├── websites.py      # 网站管理
│   │   ├── tasks.py         # 任务管理
│   │   ├── schedules.py     # 调度管理
│   │   ├── export_api.py    # 数据导出
│   │   └── statistics.py    # 统计查询
│   └── utils/               # 工具函数
│       ├── logger.py        # 日志配置
│       └── response.py      # 统一响应
├── frontend/                # 前端应用
│   ├── src/
│   │   ├── api/            # API 接口
│   │   ├── views/          # 页面组件
│   │   ├── router/         # 路由配置
│   │   └── utils/          # 工具函数
│   └── vite.config.ts      # Vite 配置
├── scheduler/              # 调度任务
│   └── tasks.py           # 调度任务定义
├── docs/                  # 文档
│   └── api.md            # API 文档
├── logs/                 # 日志文件
├── exports/              # 导出文件
├── web/                  # 前端构建产物
├── run.py               # 应用启动入口
├── main.py              # 原始命令行工具
└── requirements.txt     # Python 依赖

```

## 核心功能

### 1. 网站管理

- 添加/编辑/删除网站
- 配置爬取深度和最大链接数
- 网站状态管理（启用/禁用）

### 2. 爬取任务

**两种爬取策略：**

- **增量模式 (incremental)**: 只爬取新链接，跳过已存在的链接，适合定期更新
- **全量模式 (full)**: 重新爬取所有链接，更新所有数据

**任务控制：**

- 手动启动爬取任务
- 实时查看任务状态和进度
- 强制取消运行中的任务
- 删除已完成/失败的任务
- 查看详细的任务日志

### 3. 定时调度

- 创建定时爬取任务（小时/天/月）
- 启用/禁用调度
- 查看调度执行历史

### 4. 数据统计

- 爬取链接统计
- 有效率和精准率分析
- 任务执行统计
- 网站活跃度分析

### 5. 数据导出

- 支持 CSV、JSON、Excel 格式
- 可选增量或全量导出
- 按网站和时间范围筛选

## API 接口

系统提供完整的 RESTful API，详细文档见 [docs/api.md](docs/api.md)。

### 主要接口

- `GET /api/health` - 健康检查
- `POST /api/websites` - 创建网站
- `GET /api/websites` - 获取网站列表
- `POST /api/tasks/crawl` - 启动爬取任务
- `GET /api/tasks` - 获取任务列表
- `POST /api/tasks/{id}/cancel` - 取消任务
- `DELETE /api/tasks/{id}` - 删除任务
- `POST /api/schedules` - 创建调度任务
- `GET /api/export/links` - 导出链接数据
- `GET /api/statistics` - 获取统计数据

## 命令行工具

项目保留了原始的命令行工具，可以单独使用：

```bash
# 爬取单个网站
python main.py <website_url>

# 示例
python main.py https://www.github.com
```

结果将保存在 `result/` 目录。

## 数据库

### 集合结构

- `websites`: 网站配置
- `crawl_tasks`: 爬取任务记录
- `crawled_links`: 爬取的链接
- `crawl_logs`: 爬取日志
- `schedules`: 调度配置

### 索引

系统启动时自动创建所有必要的索引：

- 唯一索引: `websites.url`, `(crawled_links.website_id, url)`
- 复合索引: `(website_id, started_at)`, `(task_id, created_at)`
- 普通索引: `website_id`, `status`, `created_at` 等

## 开发指南

### 添加新的 API 端点

1. 在 `app/models/` 中定义数据模型（如需要）
2. 在 `app/services/` 中实现业务逻辑
3. 在 `app/api/` 中创建路由和处理函数
4. 在 `app/__init__.py` 中注册新的蓝图
5. 在 `docs/api.md` 中添加 API 文档

### 前端开发

```bash
cd frontend

# 开发模式
pnpm dev

# 代码检查
pnpm lint

# 类型检查
pnpm typecheck

# 构建生产版本
pnpm build
```

### 添加调度任务

1. 在 `scheduler/tasks.py` 中定义任务函数
2. 在数据库 `schedules` 集合中创建调度配置
3. APScheduler 会自动加载并执行任务

## 配置说明

### 爬虫配置 (app/config.py)

```python
class Config:
    max_depth = 3          # 最大爬取深度
    max_links = 1000       # 最大链接数
    request_delay = 0.5    # 请求延迟(秒)
    request_timeout = 10   # 请求超时(秒)
    save_path = 'result'   # 结果保存路径
```

### MongoDB 配置

确保 MongoDB 服务正在运行，并在 `.env` 文件中配置正确的连接字符串。

## 部署

### 生产环境建议

1. **使用 Gunicorn 运行 Flask**:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 run:app
   ```

2. **使用 Nginx 反向代理**:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. **使用 systemd 管理服务**:
   创建 `/etc/systemd/system/crawler.service`

4. **配置日志轮转**:
   防止日志文件过大

## 故障排查

### 常见问题

1. **MongoDB 连接失败**
   - 检查 MongoDB 服务是否运行
   - 验证 `.env` 中的连接字符串

2. **前端无法连接后端**
   - 检查 CORS 配置
   - 验证后端服务是否正常启动

3. **爬虫请求失败**
   - 检查网络连接
   - 某些网站可能有反爬虫机制

4. **任务无法取消**
   - 任务会在下一个检查点停止
   - 查看任务日志了解详情

## 性能优化

- 使用 MongoDB 索引加速查询
- 合理配置爬虫延迟避免被封
- 定期清理旧的任务日志
- 使用 Redis 缓存（可选）

## 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 致谢

- Flask 框架
- MongoDB 数据库
- Vue.js 生态系统
- Element Plus UI 库
- BeautifulSoup 解析库

---

**注意**: 请遵守目标网站的 robots.txt 和使用条款，合理使用爬虫工具。
