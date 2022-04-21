FROM alpine

RUN  apk add python2 curl vim bash mongodb-tools mysql-client

RUN curl https://bootstrap.pypa.io/pip/2.7/get-pip.py -o get-pip.py && python get-pip.py
RUN pip install kazoo redis pymongo

ADD idgenerator.py /opt/
ADD mysql.py /opt/
ADD zookeeper.py /opt/
ADD mongo.py /opt/