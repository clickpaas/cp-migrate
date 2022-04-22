#!/bin/python
# _*_coding: utf-8

from commands import getstatusoutput
import os
import time

SaveDir = "business_data"  # 自定义存储目录
CustomDomain = ""  # 客户自定义域名
ExternalDB = False  #是否使用外置数据库

# 不需要改动
DockerImage = ""
# 下面这些变量在运行时候会自动获取，一般不需要修改， 如果客户用了自定义的数据库，将下面地址填写对应的


MiddlePodReg = {
    "nginx": "nginx-controller",
    "mysql": "diamond-mysql",
    "mongo": "click-mongodb",
    "redis-gc": "redis-gcache",
    "redis-id": "redis-idgenerator-0",
    "zk": "zookeeper0-0",
}

Mysql = {
    "Host": "xxxxx",
    "Port": 3306,
    "User": "xxxx",
    "Passwd": "xxxxx"
}

Mongo = {
    "Host": "xxxx",
    "Port": "27017",
    "User": "xxxx",
    "Passwd": 27017,
}

RedisIdgenerator = {
    "Host": "xxxx",
    "Port": 16379
}

Zookeeper = {
    "Host": "dsadada",
    "Port": 2181
}


def check_error(code, cmd, err_msg):
    assert code == 0, "Execute {} failed, Reason: {}".format(cmd, err_msg)


def velero_delete_if_exist(namespace):
    cmd = "./velero delete backup {} -y".format(namespace)
    (code, ret) = getstatusoutput(cmd)
    check_error(code, cmd, ret)


# 备份namespace
def create_backup(namespace):
    cmd = "./velero backup create {} --include-namespaces {} --wait".format(namespace, namespace)
    (code, ret) = getstatusoutput(cmd)
    check_error(code, cmd, ret)


def wait_velero_backup_complete(namespace, timeout):
    cmd = "./velero backup get |grep {} |grep Completed".format(namespace)
    is_ok = False
    for i in range(timeout):
        (code, ret) = getstatusoutput(cmd)
        if code == 0 and ret != "":
            is_ok = True
            break
        time.sleep(60)
    assert is_ok, "Velero Backup {} Failed, You can use `kubectl log -f velero -n velero` to check it".format(namespace)
    print("Velero backup {} Completed").format(namespace)


# backup redis data
def backup_gcache():
    cmd = "kubectl cp redis-gcache-0:/data/redis/8300/appendonly.aof business_data/appendonly.aof"
    (code, ret) = getstatusoutput(cmd)
    check_error(code, cmd, ret)


def backup_nginx():
    #  获取nginx容器的名称
    cmd0 = "kubectl get pod |grep "+ MiddlePodReg.get("nginx") + " |awk '{print $1}'"
    (code, ret) = getstatusoutput(cmd0)
    check_error(code, cmd0, ret)
    nginx_pod_name = ret
    # 压缩nginx  配置文件
    cmd1 = 'kubectl  exec {} --  sh  -c "cd /etc/nginx && tar cf nginx.tar conf-site.d && mv nginx.tar /tmp/ "'.format(
        nginx_pod_name)
    (code, ret) = getstatusoutput(cmd1)
    check_error(code, cmd1, ret)

    # 拷贝nginx 配置文件
    cmd2 = 'kubectl cp {}:/tmp/nginx.tar {}/nginx.tar'.format(nginx_pod_name, SaveDir)
    (code, ret) = getstatusoutput(cmd2)
    check_error(code, cmd2, ret)

    # 删除 nginx 备份文件
    cmd3 = 'kubectl exec {} -- sh -c "rm /tmp/nginx.tar"'.format(nginx_pod_name)
    (code, ret) = getstatusoutput(cmd3)
    check_error(code, cmd3, ret)
    # 解压


def backup_diamond():
    save_dir = "./{}/diamond".format(SaveDir)
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
    cmd = 'docker run --network host -v {}:/data --env MYSQL_HOST="{}" --env MYSQL_PORT="{}" --env MYSQL_USER="{}" --env MYSQL_PASSWD="{}" ' \
          '--rm {} python /opt/mysql.py dump'. \
        format(SaveDir, Mysql.get("Host"), Mysql.get("Port"), Mysql.get("User"), Mysql.get("Passwd"), DockerImage)
    (code, ret) = getstatusoutput(cmd)
    check_error(code, cmd, ret)


def backup_idgenerator():
    save_dir = "./{}/idgenerator".format(SaveDir)
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
    cmd = 'docker run --network host --rm -v {}:/data --env REDIS_HOST="{}"  --env REDIS_PORT="{}" {} python /opt/idgenerator.py'. \
        format(SaveDir, RedisIdgenerator.get("Host"), RedisIdgenerator.get("Port"), DockerImage)
    (code, ret) = getstatusoutput(cmd)
    check_error(code, cmd, ret)


# zookeeper里面配置文件备份
def backup_zookeeper():
    save_dir = "./{}/zookeeper".format(SaveDir)
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
    cmd = 'docker run --network host --rm -v {}:/data --env ZK_HOST="{}" --env REDIS_PORT="{}"  {} python /opt/zookeeper.py'. \
        format(SaveDir, Zookeeper.get("Host"), Zookeeper.get("Port"), DockerImage)
    (code, ret) = getstatusoutput(cmd)
    check_error(code, cmd, ret)


def backup_mongo():
    save_dir = "./{}/mongo".format(SaveDir)
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
    cmd = 'docker run --network host --rm -v {}:/data --env MONGO_HOST="{}" --env MONGO_PASSWD="{}" --env MONGO_USER="{}" --env MONGO_PORT="{}" {} python /opt/mongo.py dump'.format(
        save_dir, Mongo.get("Host"), Mongo.get("Port"), Mongo.get("User"), Mongo.get("Passwd"), DockerImage)
    (code, ret) = getstatusoutput(cmd)
    check_error(code, cmd, ret)

# helper functions
def get_special_server_address(service):
    cmd = "kubectl get pods -owide|grep " + service + " |awk '{print $1}'"
    (code, ret) = getstatusoutput(cmd)
    check_error(code, cmd,ret)

def initial_environment():
    Mysql["Host"] = get_special_server_address("diamond-mysql")
    diamond_pod = get_pod_instance("diamond0-0")
    Mysql["User"] = get_env_from_pod("DB_USER", diamond_pod)
    Mysql["Passwd"] = get_env_from_pod("DB_PASSWORD", diamond_pod)
    Mysql["Port"] = get_env_from_pod("MYSQL_PORT", diamond_pod)

    mongo_pod = get_pod_instance(MiddlePodReg.get("mongo"))
    Mongo["Host"] = get_special_server_address("click-mongodb")
    Mongo["User"] = get_env_from_pod("MONGO_INITDB_ROOT_USERNAME", mongo_pod)
    Mongo["Passwd"] = get_env_from_pod("MONGO_INITDB_ROOT_PASSWORD", mongo_pod)

    RedisIdgenerator["Host"] = get_special_server_address("redis-idgenerator-0")
    Zookeeper["Host"] = get_special_server_address("zookeeper0-0")


# helper functions
def get_env_from_pod(env_name, pod_name):
    cmd = 'kubectl  exec {} --  sh  -c "echo ${}"'.format(pod_name, env_name)
    (code,ret) = getstatusoutput(cmd)
    check_error(code, cmd,ret)
    return ret


def get_pod_instance(pod_reg):
    cmd = "kubectl get pods |grep " + pod_reg + " |grep Runn |awk '{print $1}'"
    (code, pod) = getstatusoutput(cmd)
    check_error(code, cmd, pod)
    assert pod != "", "{} may not running, Plz check it"
    return pod


def Main():
    # 初始化环境，获取中间件对应的IP地址
    if ExternalDB == False:
        initial_environment()


    getstatusoutput("mkdir {}".format(SaveDir))
    namespace = ["ipaas-function", "default", "ipaas-runtime"]
    # k8s 备份
    print("\nReady Backup Kubernetes resource ............")
    map(lambda _: velero_delete_if_exist(_), namespace)  # 备份前先删除旧的备份
    map(lambda _: create_backup(_), namespace)  # 开始备份
    map(lambda _: wait_velero_backup_complete(_, 5 * 60), namespace)  # 等待备份完成
    # gcache备份
    print("\nReady Backup redis gcache resource ............")
    backup_gcache()
    # 备份nginx 配置
    backup_nginx()
    # 备份diamond
    backup_diamond()
    # 备份zookeeper
    backup_zookeeper()
    # 备份mongodb
    backup_mongo()
    # 备份idgenerator
    backup_idgenerator()


if __name__ == '__main__':
    Main()
