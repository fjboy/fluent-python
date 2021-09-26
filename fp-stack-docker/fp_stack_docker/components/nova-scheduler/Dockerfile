FROM centos:7

COPY *.repo /etc/yum.repos.d/
RUN rm -r /etc/localtime && ln -s /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
RUN yum install -y openstack-nova-scheduler \
    && yum clean all
RUN systemctl enable openstack-nova-scheduler

ENTRYPOINT [ "/usr/sbin/init" ]
