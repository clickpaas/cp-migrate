#!/bin/python

import os
import sys
from commands import getstatusoutput

Mysql = {
    "Host": os.getenv("MYSQL_HOST"),
    "Port": os.getenv("MYSQL_PORT"),
    "User": os.getenv("MYSQL_USER"),
    "Passwd": os.getenv("MYSQL_PASSWD"),
}


def check_error(code, cmd, err_msg):
    assert code == 0, "Execute {} failed, Reason: {}".format(cmd, err_msg)






def dump_database(dbname):
    """
    dump db from mysql, it will return None if it execute successfully, else panic
    :param client: the client instance that connnect to mysql
    :param dbname: the db name that should be dumped
    :param target: the path of that save dump file
    :return:
    """

    cmd = 'mysqldump -h {} --port {} -u {} --password="{}" --databases {} > /data/{}.sql'.format(Mysql.get("Host"),
                                                                                   Mysql.get("Port"),
                                                                                   Mysql.get("User"),
                                                                                   Mysql.get("Passwd"),
                                                                                   dbname, dbname)
    print(cmd)
    (code,ret) = getstatusoutput(cmd)
    check_error(code, cmd, ret)


def restore_database(dbname):
    """
    restore dbs into mysql, it will return None if execute successfully, else panic
    :param client:  the client instance that connected to mysql
    :param dbname:
    :param source:
    :return:
    """
    cmd = 'mysql -h {} --port {} -u {} --password="{}" -e "source /data/{}.sql"'.format(Mysql.get("Host"),
                                                                                   Mysql.get("Port"),
                                                                                   Mysql.get("User"),
                                                                                   Mysql.get("Passwd"), dbname)
    (code, ret) = getstatusoutput(cmd)
    check_error(code, cmd, ret)



def Main(op):
    target = "/data/mysql"
    dbs_need_dumped = ["diamond", "im", "lts", "nacos"]
    op_handler = dump_database if op == "dump" else restore_database
    map(lambda _: op_handler(_), dbs_need_dumped)


if __name__ == '__main__':
    op = sys.argv[1]
    Main(op)