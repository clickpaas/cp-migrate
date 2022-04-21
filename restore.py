
#!/bin/python
# _*_coding: utf-8

from commands import getstatusoutput
import os


SaveDir = "business_data"  # 自定义存储目录
DefaultRestoreNS = ["ipaas-function", "default", "ipaas-runtime"]
DockerImage = ""

Mysql = {
    "Host": "xxxxx",
    "Port": 3306,
    "User": "xxxx",
    "Passwd": "xxxxx"
}

Mongo = {
    "Host": "xxxx",
    "Port": "xxxx",
    "User": "xxxx",
    "Passwd": "xxxx",
}

RedisIdgenerator = {
    "Host": "xxxx",
    "Port": 12345
}

Zookeeper = {
    "Host": "dsadada",
    "Port": "12223"
}


def get_pod_instance(pod_reg):
    cmd = "kubectl get pods |grep " + pod_reg + " |grep Runn |awk '{print $1}'"
    (code, pod) = getstatusoutput(cmd)
    check_error(code, cmd, pod)
    assert pod != "", "{} may not running, Plz check it"
    return pod


def check_error(code, cmd, err_msg):
    assert code == 0, "Execute {} failed, Reason: {}".format(cmd, err_msg)


def wait_pod_running(pod, timeout):
    cmd = "kubectl get pods -owide |grep Running| grep {}".format(pod)
    is_ok = False
    for i in range(timeout):
        (code,ret) = getstatusoutput(cmd)
        if code == 0 and ret != "":
            is_ok = True
            break
    assert is_ok, "Pod {} is not running ,plz check it and make sure that it in running state, then continue"



def restore_kubernetes(namespace):
    cmd = "./velero restore create --from-backup {}".format(namespace)
    (code, ret) = getstatusoutput(cmd)
    check_error(code, cmd, ret)


def restore_mysql():
    save_dir = "./{}/diamond".format(SaveDir)
    assert os.path.exists(save_dir), "Path {} is not existed".format(save_dir)

    cmd = 'docker run --network host -v {}:/data --env MYSQL_HOST="{}" --env MYSQL_PORT="{}" --env MYSQL_USER="{}" --env MYSQL_PASSWD="{}" ' \
          '--rm {} python /opt/mysql.py restore'. \
        format(SaveDir, Mysql.get("Host"), Mysql.get("Port"), Mysql.get("User"), Mysql.get("Passwd"), DockerImage)
    (code, ret) = getstatusoutput(cmd)
    check_error(code, cmd, ret)



def restore_zookeeper():
    zk_pod = get_pod_instance("zookeeper0-0")

    cp_cmd = 'kubectl cp ./{}/zookeeper/zk_gcache_commands.sh {}:/tmp/'.format(SaveDir, zk_pod)
    (code, ret) = getstatusoutput(cp_cmd)
    check_error(code, cp_cmd, ret)

    cp_cmd = 'kubectl cp ./{}/zookeeper/zk_id_commands.sh {}:/tmp/'.format(SaveDir, zk_pod)
    (code, ret) = getstatusoutput(cp_cmd)
    check_error(code, cp_cmd, ret)

    exec_cmd1 = 'kubectl exec {} -- sh -c "/root/zookeeper-3.4.10/bin/zkCli.sh < /tmp/zk_id_commands.sh"'.format(zk_pod)
    (code, ret) = getstatusoutput(exec_cmd1)
    check_error(code, exec_cmd1, ret)

    exec_cmd2 = 'kubectl exec {} -- sh -c "/root/zookeeper-3.4.10/bin/zkCli.sh < /tmp/zk_gcache_commands.sh"'.format(zk_pod)
    (code, ret) = getstatusoutput(exec_cmd2)
    check_error(code, exec_cmd2, ret)


def restore_nginx():
    # get nginx pod
    nginx_pod = get_pod_instance("nginx-controller")

    cmd1 = "kubectl cp ./{}/nginx.tar {}:/etc/nginx/nginx.tar".format(SaveDir, nginx_pod)
    (code, ret) = getstatusoutput(cmd1)
    check_error(code, cmd1, ret)

    cmd2 = 'kubectl exec {} -- sh -c "cd /etc/nginx/ && tar xf nginx.tar && rm nginx.tar"'.format(nginx_pod)
    (code, ret) = getstatusoutput(cmd2)
    check_error(code, cmd2, ret)


def restore_mongo():
    save_dir = "./{}/mongo".format(SaveDir)
    assert os.path.exists(save_dir), "Path is not exist {}".format(save_dir)
    cmd = 'docker run --network host --rm -v {}:/data --env MONGO_HOST="{}" --env MONGO_PASSWD="{}" --env MONGO_USER="{}" --env MONGO_PORT="{}" {} python /opt/mongo.py restore'.format(
        save_dir, Mongo.get("Host"), Mongo.get("Port"), Mongo.get("User"), Mongo.get("Passwd"), DockerImage)
    (code, ret) = getstatusoutput(cmd)
    check_error(code, cmd, ret)

def restore_idgenerator():
    pod = get_pod_instance("redis-idgenerator-0")

    cmd1 = "kubectl cp ./{}/redis-idgenerator/redis_id_commands.txt {}:/tmp/redis_id_commands.txt".format(SaveDir, pod)
    (code, ret) = getstatusoutput(cmd1)
    check_error(code, cmd1, ret)

    cmd2 = 'kubectl exec {} -- sh -c "cat /tmp/redis_id_commands.txt |redis-cli -p 16379 "'
    (code, ret) = getstatusoutput(cmd2)
    check_error(code, cmd2, ret)




def restore_gcache():
    gcache_pod = get_pod_instance("redis-gcache")
    cmd = "kubectl cp ./{}/appendonly.aof {}:/data/redis/8300/appendonly.aof".format(SaveDir,gcache_pod)
    (code, ret) = getstatusoutput(cmd)
    check_error(code, cmd, ret)



# def scale_2_zero(namespace):
#     cmd_list_dpl = "kubectl get deployment -n " + namespace + "|grep -v NAME |awk '{print $1}'"
#     (code, ret) = getstatusoutput(cmd_list_dpl)
#     check_error(code, cmd_list_dpl, ret)
#     for dpl in ret.split("\n"):
#         scale_cmd = "kubectl -n " + namespace + " scale --replicas=0 deployment " + dpl
#         (code, ret) = getstatusoutput(scale_cmd)
#         check_error(code, scale_cmd, ret)


# helper functions
def get_special_server_address(service):
    cmd = "kubectl get pods -owide|grep " + service + " |awk '{print $1}'"
    (code, ret) = getstatusoutput(cmd)
    check_error(code, cmd,ret)

def initial_environment():
    Mysql["Host"] = get_special_server_address("diamond-mysql")
    Mongo["Host"] = get_special_server_address("click-mongodb")
    RedisIdgenerator["Host"] = get_special_server_address("redis-idgenerator-0")
    Zookeeper["Host"] = get_special_server_address("zookeeper0-0")


def Main():
    all_necessary_pod = ["diamond-mysql", "nginx-controller", "click-mongo", "redis-gcache", "redis-idgenera", "zookeeper0-0"]

    map(lambda _: restore_kubernetes(_), DefaultRestoreNS)    # 所有的kubernetes  还原
    #  等待所有中间件都处于running 状态，然后再继续,等待20分钟
    print("Waiting Mysql/Mongo/Redis/zookeeper is running for 20 min")
    map(lambda _: wait_pod_running(_, 20 * 60), all_necessary_pod)
    # 还原nginx
    restore_nginx()# ok
    # 还原zookeeper
    restore_zookeeper()# ok
    # 还原mongo
    restore_mongo() #ok
    # 还原mysql
    restore_mysql()  # ok
    # 还原redis-gcache
    restore_gcache() # ok
    # 还原redis_idgenerator
    restore_idgenerator() # ok

if __name__ == '__main__':
    Main()
