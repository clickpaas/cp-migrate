#coding=utf-8
from kazoo.client import KazooClient
import json
import os

Zookeeper = {
    "Host": os.getenv("ZK_HOST"),
    "Port": os.getenv("ZK_PORT"),
}



zk = KazooClient(hosts='{}:{}'.format(Zookeeper.get("Host"), Zookeeper.get("Port")))
zk.start()    #与zookeeper连接


def walk_path(map, path):
    nodes = zk.get_children(path)
    for node in nodes:
        node_path = path + "/" + node
        data, stat = zk.get(node_path)
        if node_path=='/gcache/idgenerator':
            continue
        if node_path=='/gcache/clusters':
            continue
        # print("path=%s,value=%s"%(node_path,data.decode('utf-8')))
        map[node_path] = data.decode('utf-8')
        walk_path(map,node_path)

def idMap():
    path = "/idgenerator"
    nodes = zk.get_children(path)
    map = {}
    for node in nodes:
        node_path = path + "/" + node
        data, stat = zk.get(node_path)
        value = data.decode('utf-8')
        value_map = json.loads(value)
        value_map['servers']=["redis-idgenerator:16379"]
        map[node_path]=json.dumps(value_map,separators=(",", ":"))
    return map


gcache_map = {}
walk_path(gcache_map,'/gcache')
print(json.dumps(gcache_map))
filename = '/data/zk_gcache_commands.txt'
#./zkCli.sh -server $server create /gcache/clusters/common_cluster/172.x.x.x:8302 nodestate:alive
with open(filename, 'w') as file_object:
    file_object.write("create /gcache ''\n")
    file_object.write("create /gcache/clusters ''\n")
    file_object.write("create /gcache/clusters/common_cluster ''\n")
    file_object.write("create /gcache/businesses ''\n")
    file_object.write("create /gcache/routes/common_cluster '{}'\n")
    file_object.write("create /gcache/idgenerator ''\n")
    file_object.write("create /gcache/clusters/common_cluster/$gcache_node nodestate:alive\n")
    for k,v in gcache_map.items():
        file_object.write("create "+k+" "+v+"\n")

id_map = idMap()
print(json.dumps(id_map,separators=(",", ":")))
#老数据更新应当使用./zkCli.sh set /test x
filename = '/data/zk_id_commands.txt'
with open(filename, 'w') as file_object:
    file_object.write("create /idgenerator ''\n")
    for k,v in id_map.items():
        file_object.write("create "+k+" "+v+"\n")