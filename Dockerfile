
# 使用Python 3.10 slim作为基础镜像
FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 9999
CMD ["python", "run.py"]

# 构建时设置镜像标签
# 构建命令: docker build -t fetch_link_from_website .
 # docker run -d -p 9999:9999 fetch_link_from_website
