# 爬虫服务

需要编写两个函数

## get_all_links

`get_all_links` 用于递归调用

### 参数
- url: str 需要爬虫处理的 url 链接
- depth: int 需要爬虫处理的深度

### 输出
- links: list[str] 爬到的 links

### 处理

在函数内部递归调用直到 depth 为 0，最后将所有列表打平返回一个 links 列表

## crawler_link

`crawler_link` 用于 API 函数调用，获取链接并且计算参数与下载内容

### 参数
- url: str 需要爬虫的 url 链接
- depth: int 爬虫的深度
- exclude: list[str] default [] 需要排除的 url (用于增量更新策略)

### 输出
- links: Array<{
  link: str # 爬到的链接
  content_path: str # 下载内容存放的地址
  }>
- valid_rate: float
- precision_rate: float

### 处理

首先需要调用 `get_all_links` 函数获取所有的链接，排除 exclude 中的 urls，并且将链接下载并且保存到本地，计算两个 rate 指标，最后将结果输出。

注意
- 使用 config.py 中的配置根路径保存 content
- 下载保存路径文件夹要生成 uuid 避免重复文件夹重复