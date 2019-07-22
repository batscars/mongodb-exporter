##### Description
MongoDB stats exporter without create mongodb user with monitoring permission

##### Build Docker Image
```
docker build -f Dockerfile -t mongdb-exporter-python .
```

##### Run MongoDB Exporter
```
docker run -d \
	--name mongodb_exporter_python \
	--log-opt max-size=200m \
	--log-opt max-file=3 \
	-p 5000:5000 \
    -e MONGO_HOST= \
	-e MONGO_PORT= \
	-e MONGO_USERNAME= \
	-e MONGO_PASSWORD= \
	-e DBNAME= \
	--restart=always \
	mongodb-exporter-python
```

##### Configure Prometheus
```
# add to prometheus.yml: scrape_configs
- job_name: "mongodb-exporter"
    static_configs:
      - targets: ["host_ip:5000"] # change host_ip
# restart prometheus
docker restart prometheus
```

##### Metrics Exported
```
"mongodb_data_size": "The total size of the uncompressed data held in this database. (bytes)"
"mongodb_index_size": "The total size of all indexes created on this database (bytes)"
"mongodb_storage_size": "The total amount of space allocated to collections in this database for document storage. (bytes)"
"mongodb_read_lantency": "Read ops latency in microseconds"
"mongodb_read_lantency_sum": "Total read ops latency in microseconds"
"mongodb_read_lantency_count": "Total read ops count",
```
