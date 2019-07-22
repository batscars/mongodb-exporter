import prometheus_client
from prometheus_client import Gauge
from prometheus_client.core import CollectorRegistry
from flask import Response, Flask
import os
import hashlib
import pymongo
from pymongo import ReadPreference
# import logging
# logging.getLogger('werkzeug').setLevel(logging.ERROR)  # to disable request logging

app = Flask(__name__)


CONNETCT_POOL = dict()


def connect_mongo():
    host = os.getenv("MONGO_HOST", "192.168.2.1")
    port = os.getenv("MONGO_PORT", "22222")
    username = os.getenv("MONGO_USERNAME", "test")
    password = os.getenv("MONGO_PASSWORD", "test")
    db_name = os.getenv("DBNAME", "test")
    key = host + port + username + password + db_name
    key = hashlib.md5(key.encode("utf8")).hexdigest()
    global CONNETCT_POOL
    if key not in CONNETCT_POOL:
        CONNETCT_POOL[key] = pymongo.MongoClient(host=host, port=int(port))
    client = CONNETCT_POOL[key]
    db = client.get_database(db_name, read_preference=ReadPreference.SECONDARY_PREFERRED)
    db.authenticate(username, password)
    return db, host+":"+port, db_name


mongo_handler, db_host, db_name = connect_mongo()
REGISTRY = CollectorRegistry(auto_describe=False)
mongodb_data_size = Gauge("mongodb_data_size",
                          "The total size of the uncompressed data held in this database. (bytes)",
                          ["db_name", "db_instance"],
                          registry=REGISTRY)
mongodb_index_size = Gauge("mongodb_index_size",
                           "The total size of all indexes created on this database (bytes)",
                           ["db_name", "db_instance"],
                           registry=REGISTRY)
mongodb_storage_size = Gauge("mongodb_storage_size",
                             "The total amount of space allocated to collections in this database for document storage. (bytes)",
                             ["db_name", "db_instance"],
                             registry=REGISTRY)
mongodb_read_lantency = Gauge("mongodb_read_lantency",
                                "Read ops latency in microseconds",
                                ["db_name", "db_instance", "collection", "micros"],
                                registry=REGISTRY)
mongodb_read_lantency_sum = Gauge("mongodb_read_lantency_sum",
                                  "Total read ops latency in microseconds",
                                  ["db_name", "db_instance", "collection"],
                                  registry=REGISTRY)
mongodb_read_lantency_count = Gauge("mongodb_read_lantency_count",
                                    "Total read ops count",
                                    ["db_name", "db_instance", "collection"],
                                    registry=REGISTRY)


def get_db_stats():
    dbstats = mongo_handler.command("dbstats")
    data_size = dbstats.get("dataSize")
    index_size = dbstats.get("indexSize")
    storage_size = dbstats.get("storageSize")
    mongodb_data_size.labels(db_name, db_host).set(data_size)
    mongodb_index_size.labels(db_name, db_host).set(index_size)
    mongodb_storage_size.labels(db_name, db_host).set(storage_size)


def get_lantency_stats():
    collects = mongo_handler.list_collection_names(session=None)
    for collect in collects:
        collect_ = mongo_handler.get_collection(collect)
        result = list(collect_.aggregate([{"$collStats": {"latencyStats": {"histograms": True}}}]))[0]
        histogram = result.get("latencyStats").get("reads")
        sum_ = histogram.get("latency")
        count_ = histogram.get("ops")
        mongodb_read_lantency_sum.labels(db_name, db_host, collect).set(sum_)
        mongodb_read_lantency_count.labels(db_name, db_host, collect).set(count_)
        for hist in histogram.get("histogram"):
            mongodb_read_lantency.labels(db_name, db_host, collect, hist.get("micros")).set(hist.get("count"))


@app.route("/metrics", methods=["GET"])
def metrics():
    get_db_stats()
    get_lantency_stats()
    return Response(prometheus_client.generate_latest(REGISTRY), mimetype="text/plain")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
