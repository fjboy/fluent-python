lFROM centos:7

RUN cd /etc/yum.repos.d && mkdir backup && mv *.repo backup
COPY *.repo /etc/yum.repos.d/
RUN rm -r /etc/localtime && ln -s /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
RUN yum install -y openstack-nova-api python-novaclient openstack-nova-placement-api openstack-nova-center-compute-api \
    && yum clean all
RUN systemctl enable openstack-nova-api

ENTRYPOINT [ "/usr/sbin/init" ]
