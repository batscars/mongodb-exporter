FROM python:3.7.3-alpine
COPY . /workspace
WORKDIR /workspace
RUN pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --no-cache-dir
CMD ["python", "mongo_exporter.py"]
