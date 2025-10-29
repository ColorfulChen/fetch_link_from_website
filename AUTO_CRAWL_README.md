# 自动爬取脚本使用说明

## 功能概述

`auto_crawl_from_csv.py` 是一个自动化爬取脚本，可以从CSV文件读取URL列表，自动查询网站ID、创建爬取任务并监控任务执行状态，直到所有任务完成。

## 工作流程

对于CSV文件中的每个URL，脚本会执行以下步骤：

1. **查询网站ID**: 使用 `GET /api/websites/by-url` 接口根据URL查询网站信息
2. **创建爬取任务**: 使用 `POST /api/tasks/crawl` 接口创建爬取任务
3. **监控任务状态**: 每隔指定时间（默认30秒）使用 `GET /api/tasks/{task_id}` 接口查询任务状态
4. **等待任务完成**: 当任务状态变为 `completed` 或 `failed` 时，处理下一个URL
5. **循环处理**: 重复以上步骤，直到所有URL处理完毕

## CSV文件格式

CSV文件必须包含 `url` 列，示例：

```csv
url
https://www.who.int
https://www.cdc.gov
https://www.example.com
```

## 使用方法

### 基本使用

```bash
python auto_crawl_from_csv.py webside.csv
```

### 指定参数

```bash
# 指定爬取深度和最大链接数
python auto_crawl_from_csv.py webside.csv --depth 5 --max-links 2000

# 使用全量爬取策略
python auto_crawl_from_csv.py webside.csv --strategy full

# 修改状态检查间隔为60秒
python auto_crawl_from_csv.py webside.csv --interval 60

# 指定API地址
python auto_crawl_from_csv.py webside.csv --api http://localhost:5000

# 组合使用
python auto_crawl_from_csv.py webside.csv \
  --depth 4 \
  --max-links 3000 \
  --strategy full \
  --interval 45 \
  --api http://localhost:9999
```

### 使脚本可执行（Linux/Mac）

```bash
chmod +x auto_crawl_from_csv.py
./auto_crawl_from_csv.py webside.csv
```

## 命令行参数

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `csv_file` | 是 | - | CSV文件路径（必须包含url列） |
| `--api` | 否 | http://localhost:9999 | API基础URL |
| `--depth` | 否 | 3 | 爬取深度 |
| `--max-links` | 否 | 1000 | 最大链接数 |
| `--strategy` | 否 | incremental | 爬取策略（incremental/full） |
| `--interval` | 否 | 30 | 任务状态检查间隔（秒） |

### 爬取策略说明

- **incremental（增量）**: 只爬取新链接，跳过已存在的链接
- **full（全量）**: 重新爬取所有链接，更新数据库中的数据

## 输出示例

```
============================================================
开始自动爬取流程
============================================================
CSV文件: webside.csv
API地址: http://localhost:9999
爬取深度: 3
最大链接: 1000
爬取策略: incremental
检查间隔: 30秒

找到 2 个URL

============================================================
处理 [1/2]: https://www.who.int
============================================================
  → 查询网站信息: https://www.who.int
  ✓ 找到网站: WHO (ID: 507f1f77bcf86cd799439011)
  → 创建爬取任务 (策略: incremental, 深度: 3, 最大链接: 1000)
  ✓ 任务创建成功 (ID: 507f1f77bcf86cd799439012)
  → 等待任务完成 (每30秒检查一次)
  ⏳ 任务进行中 (running) - 已爬取: 45 个链接
  ⏳ 任务进行中 (running) - 已爬取: 120 个链接
  ✓ 任务完成!
    - 总链接: 256
    - 有效链接: 230
    - 新增链接: 180
    - 有效率: 89.84%

============================================================
处理 [2/2]: https://www.cdc.gov
============================================================
  → 查询网站信息: https://www.cdc.gov
  ✓ 找到网站: CDC (ID: 507f1f77bcf86cd799439013)
  → 创建爬取任务 (策略: incremental, 深度: 3, 最大链接: 1000)
  ✓ 任务创建成功 (ID: 507f1f77bcf86cd799439014)
  → 等待任务完成 (每30秒检查一次)
  ⏳ 任务进行中 (running) - 已爬取: 68 个链接
  ✓ 任务完成!
    - 总链接: 189
    - 有效链接: 175
    - 新增链接: 120
    - 有效率: 92.59%

============================================================
自动爬取完成!
============================================================
总URL数: 2
成功: 2
失败: 0
耗时: 325.67秒 (5.43分钟)
============================================================
```

## 前置条件

1. **网站必须已存在**: URL必须已经通过网站管理界面或API添加到系统中
   - 如果URL不存在，脚本会跳过该URL
   - 可以先使用批量导入功能导入网站

2. **Flask应用运行中**: 确保后端API服务正在运行
   ```bash
   python run.py
   ```

3. **Python依赖**: 确保已安装 `requests` 库
   ```bash
   pip install requests
   ```

## 错误处理

### URL不存在

如果CSV中的URL在系统中不存在，脚本会显示警告并跳过：

```
  ✗ 网站不存在: https://example.com
⚠ 跳过此URL (网站不存在)
```

**解决方法**: 先使用批量导入功能将网站添加到系统中。

### 任务创建失败

如果该网站已有正在运行的任务，会返回409冲突错误：

```
  ✗ 任务创建失败: 409 - 该网站已有正在运行的任务
⚠ 跳过此URL (任务创建失败)
```

**解决方法**: 等待现有任务完成或取消现有任务。

### 任务执行失败

如果任务执行过程中失败：

```
  ✗ 任务失败: 网络连接超时
```

脚本会继续处理下一个URL。

## 注意事项

1. **串行执行**: 脚本串行处理每个URL，一次只运行一个任务
2. **时间消耗**: 爬取任务可能需要较长时间，具体取决于网站规模和网络状况
3. **网络代理**: 脚本自动禁用HTTP/HTTPS代理以避免连接问题
4. **中断恢复**: 如果脚本被中断（Ctrl+C），需要手动重新运行
5. **日志记录**: 所有爬取日志都会保存在数据库中，可通过任务详情查看

## 高级用法

### 结合批量导入使用

1. 先批量导入网站：
   ```bash
   curl -X POST http://localhost:9999/api/websites/batch-import \
     -F "file=@websites.csv"
   ```

2. 然后自动爬取：
   ```bash
   python auto_crawl_from_csv.py websites.csv
   ```

### 定时执行

使用 cron 定时执行脚本（Linux/Mac）：

```bash
# 每天凌晨2点执行
0 2 * * * cd /path/to/project && python auto_crawl_from_csv.py webside.csv
```

使用 Windows 任务计划程序定时执行。

### 后台运行

```bash
# 后台运行并输出日志
nohup python auto_crawl_from_csv.py webside.csv > crawl.log 2>&1 &

# 查看日志
tail -f crawl.log
```

## 故障排查

### 无法连接到API

**问题**: `Connection refused` 或 `Connection timeout`

**解决方法**:
- 确认Flask应用正在运行
- 检查API地址和端口是否正确
- 尝试使用 `curl http://localhost:9999/api/health` 测试连接

### CSV文件读取失败

**问题**: `读取CSV文件失败` 或 `CSV文件中没有找到URL`

**解决方法**:
- 确认CSV文件存在且有读取权限
- 确认CSV文件包含 `url` 列（注意大小写）
- 检查CSV文件编码（应为UTF-8）

### 任务一直处于pending状态

**问题**: 任务创建后一直显示 `pending`，没有开始执行

**解决方法**:
- 检查后端日志，查看是否有错误
- 确认数据库连接正常
- 尝试手动通过界面创建任务测试

## 完整示例

```bash
# 1. 确保后端服务运行
python run.py

# 2. 准备CSV文件 (webside.csv)
cat > webside.csv << EOF
url
https://www.who.int
https://www.cdc.gov
EOF

# 3. 运行自动爬取脚本
python auto_crawl_from_csv.py webside.csv \
  --depth 4 \
  --max-links 2000 \
  --strategy incremental \
  --interval 30

# 4. 查看结果
# 通过前端界面或API查看爬取结果
```

## 相关文档

- [API文档](docs/api.md) - 完整的API接口说明
- [批量导入说明](BATCH_IMPORT.md) - 批量导入网站功能
- [CLAUDE.md](CLAUDE.md) - 项目架构和开发指南

## 技术支持

如有问题，请查看：
- 项目日志文件: `logs/crawler.log`
- 任务执行日志: 通过任务详情API查看
- 数据库记录: 查看MongoDB中的相关集合
