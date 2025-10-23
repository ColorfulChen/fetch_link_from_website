from pymongo import MongoClient
import sys

# IPv6 地址必须用方括号括起来
HOST = '158.247.241.214' 
PORT = 27017
USERNAME = 'admin'
PASSWORD = 'VRuAd2Nvmp4ELHh5'
AUTH_DB = 'admin' # 认证数据库
DB_NAME = 'crawler_db'    # 目标数据库

# 构建连接 URI
uri = f"mongodb://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}?authSource={AUTH_DB}"

try:
    # 创建 MongoClient 实例
    client = MongoClient(uri)
    
    # 触发连接和认证
    # 您可以执行一个简单的命令来测试连接，例如获取服务器信息
    client.server_info() 
    
    print(f"成功连接到 MongoDB (IPv6: {HOST})")
    
    # 现在您可以使用 client.mydb 来访问 'mydb' 数据库
    db = client[DB_NAME]
    print(f"可用的集合: {db.list_collection_names()}")

except Exception as e:
    print(f"连接失败: {e}", file=sys.stderr)

finally:
    # 确保关闭连接
    if 'client' in locals():
        client.close()