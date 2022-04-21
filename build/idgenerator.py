#coding=utf-8
import redis
import json
import os
##取出各个redis中的keys,并求相同key的最大值
ENDPOINT = {
    "Host": os.getenv("REDIS_HOST"),
    "Port": os.getenv("REDIS_PORT"),
}
conns=[
    redis.Redis(host=ENDPOINT.get("Host"), port=int(ENDPOINT.get("Port")))
]
def getMap(conn1):
    keys1 = conn1.keys("*")
    mget1 = conn1.mget(keys1)
    map1={}
    #print(mget1)
    #print(len(keys1))
    for i in range(0,len(keys1)):
        k = keys1[i]
        v = mget1[i]
        if v==None:
            continue
        map1[k.decode('utf-8')] = v.decode('utf-8')
    return map1


map_list=[]
for i in conns:
    map_list.append(getMap(i))

max_value_map={}
key_list=[]
for i in range(0,len(map_list)):
    key_list.extend(map_list[i].items())

#set(key_list)去重
for k,v in set(key_list):
    max_value=0
    for i in range(0,len(map_list)):
        value=map_list[i].get(k,'0')
        int_value=int(value)
        if int_value>max_value:
            max_value = int_value
        max_value_map[k]=max_value
print(json.dumps(max_value_map))

#写入文件
filename = '/data/redis_id_commands.txt'
with open(filename, 'w') as file_object:
    for k,v in max_value_map.items():
      file_object.write("SET "+k+" "+str(v)+"\n")