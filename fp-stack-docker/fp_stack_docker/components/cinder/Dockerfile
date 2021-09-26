FROM centos:7

RUN cd /etc/yum.repos.d && mkdir backup && mv *.repo backup
COPY *.repo /etc/yum.repos.d/
RUN rm -r /etc/localtime && ln -s /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
RUN rpm --rebuilddb \
    && yum -y install openstack-cinder python-pymemcache \
    && yum clean all
RUN systemctl enable openstack-cinder-api openstack-cinder-scheduler

EXPOSE 9292
ENTRYPOINT [ "/usr/sbin/init" ]
