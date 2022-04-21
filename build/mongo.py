#!/bin/python

import os
import pymongo
import sys
from commands import getstatusoutput

Mongo = {
    "Host": os.getenv("MONGO_HOST"),
    "Passwd": os.getenv("MONGO_PASSWD"),
    "User": os.getenv("MONGO_USER"),
    "Port": os.getenv("MONGO_PORT")
}

BLACK_LIST = ["admin", "test", "config"]
INVALID_POSTFIX = "_bak"
DB_DIR = "/data"

def check_error(code, cmd, err_msg):
    assert code == 0, "Execute {} failed, Reason: {}".format(cmd, err_msg)


def get_mongo_client():
    client = pymongo.MongoClient(host=Mongo.get("Host"),
                                 port=int(Mongo.get("Port")),
                                 username=Mongo.get("User"),
                                 password=Mongo.get("Passwd"),
                                 authSource="admin")
    return client

def get_names_all_databases(client):
    assert isinstance(client, pymongo.MongoClient), "Expect MongoClient, But got {}".format(type(client))
    all_valid_db_name = filter(lambda _: _ not in BLACK_LIST and INVALID_POSTFIX not in _, client.list_database_names())
    return all_valid_db_name

# backup mongo
def dump_database(dbname):

    cmd = "mongodump  -h {} --port {} -u {} -p {}  --authenticationDatabase admin -d  {} -o /data".format(Mongo.get("Host"),
                                                                                                    Mongo.get("Port"),
                                                                                                    Mongo.get("User"),
                                                                                                    Mongo.get("Passwd"),
                                                                                                       dbname)
    (code, ret) = getstatusoutput(cmd)
    check_error(code, cmd,ret)

# restore mongo
def restore_database():
    cmd = "mongorestore -h {} --port {} -u {} -p {} --authenticationDatabase admin --drop  --dir  /data".format(Mongo.get("Host"),
                                                                                                                Mongo.get("Port"),
                                                                                                                Mongo.get("User"),
                                                                                                                Mongo.get("Passwd"))
    (code, ret) = getstatusoutput(cmd)
    check_error(code, cmd, ret)

def Main(op):
    (all_dbs, op_handler) = (["fake"], restore_database()) if op == "restore" else (get_names_all_databases(get_mongo_client()), dump_database)
    map(lambda _: op_handler(_), all_dbs)


if __name__ == '__main__':
    op = sys.argv[1]
    Main(op)