FROM centos:7

RUN cd /etc/yum.repos.d && mkdir backup && mv *.repo backup
COPY *.repo /etc/yum.repos.d/
RUN rm -r /etc/localtime && ln -s /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
RUN yum install -y openstack-neutron openstack-neutron-ml2 openstack-neutron-openvswitch \
    && yum install -y openstack-utils \
    && yum clean all
RUN systemctl enable neutron-server

EXPOSE 9696
ENTRYPOINT [ "/usr/sbin/init" ]
# ENTRYPOINT [ "su", "-s", "bin/sh", "-c", "neutron-server", "neutron" ]
