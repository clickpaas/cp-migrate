# coding=utf-8
# This is a sample Python script.

from commands import getstatusoutput
import socket
import os
import time

VeleroLabel = "velero-minio"


# hostname get current hostname
def hostname():
    return socket.gethostname()


def check_error(code, cmd, err_msg):
    assert code == 0, "Execute {} failed, Reason: {}".format(cmd, err_msg)


def get_k8s_master():
    cmd = "kubectl get node -owide |grep master|awk '{print $1}'"
    (code, ret) = getstatusoutput(cmd)
    check_error(code, cmd, ret)
    master_list = filter(lambda _: _ == hostname(), ret.split("\n"))
    assert len(master_list) == 1, "{} exited 2, plz check it".format(hostname())
    return master_list[0]


def update_deployment(dpl, namespace, node):
    payload = '[{"op":"add", "path":"/spec/template/spec/nodeName", "value":"' + node + '"}]'
    cmd = "kubectl patch deployment {} -n {} --type=json -p='{}'".format(dpl, namespace, payload)
    (code, ret) = getstatusoutput(cmd)
    check_error(code, cmd, ret)
    print "Path Deployment: {}/{} to {} successfully".format(dpl, namespace, node)


def install_minio():
    cmd = "kubectl apply -f ./minio"
    (code, ret) = getstatusoutput(cmd)
    check_error(code, cmd, ret)


def install_velero(minio_server):
    cmd0 = './velero install --provider aws --plugins velero/velero-plugin-for-aws:v1.2.1    ' \
           '--bucket velero --secret-file credentials-velero --use-volume-snapshots=false ' \
           '--backup-location-config region=minio,s3ForcePathStyle="true",s3Url=http://{}:9000'.format(minio_server)
    print cmd0
    (code, ret) = getstatusoutput(cmd0)
    check_error(code, cmd0, ret)


def load_image():
    for img in os.listdir("./images"):
        cmd = "docker load -i ./images/{}".format(img)
        (code, ret) = getstatusoutput(cmd)
        check_error(code, cmd, ret)
        print("Load image {} successfully".format(img))


def wait_for_deployment_ok(dpl, namespace, timeout):
    cmd = "kubectl get deployment -n {NS} -owide |grep {DPL}|grep '1/1'".format(NS=namespace, DPL=dpl)
    is_ok = False
    for i in range(timeout):
        (code, ret) = getstatusoutput(cmd)
        if code == 0 and ret != "":
            is_ok = True
            break
        time.sleep(1)
    assert is_ok is True, "Deployment {}/{} may occur some error, check it".format(dpl, namespace)


def get_minio_server():
    cmd = "kubectl get service -n minio  |grep minio |awk '{print $3}'"
    (code, ret) = getstatusoutput(cmd)
    check_error(code, cmd, ret)
    return ret


def Main():
    # load all images
    load_image()

    # install minikube
    install_minio()
    update_deployment("minio", "minio", get_k8s_master())
    wait_for_deployment_ok("minio", "minio", 60)
    #
    # # install velero
    install_velero(get_minio_server())
    update_deployment("velero", "velero", get_k8s_master())
    wait_for_deployment_ok("velero", "velero", 60)


if __name__ == '__main__':
    Main()
