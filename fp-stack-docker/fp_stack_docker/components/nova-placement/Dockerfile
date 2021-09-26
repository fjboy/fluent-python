FROM centos:7

COPY *.repo /etc/yum.repos.d/
RUN yum install -y openstack-nova-compute sysfsutils \
    && yum clean all
ENTRYPOINT [ "nova-compute" ]
