FROM centos:7

RUN cd /etc/yum.repos.d && mkdir backup && mv *.repo backup
COPY *.repo /etc/yum.repos.d/
RUN rm -r /etc/localtime && ln -s /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
RUN yum -y install rabbitmq-server \
    && systemctl enable rabbitmq-server.service \
    && sed -i 's|^Wants=.*|Wants=network.target|g' /usr/lib/systemd/system/rabbitmq-server.service \
    && yum clean all
EXPOSE 5672
ENTRYPOINT [ "/usr/sbin/init" ]
