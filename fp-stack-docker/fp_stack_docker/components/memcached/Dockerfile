FROM centos:7

RUN cd /etc/yum.repos.d && mkdir backup && mv *.repo backup
COPY *.repo /etc/yum.repos.d/
RUN yum -y install memcached \
    && systemctl enable memcached.service \
    && yum clean all
EXPOSE 11211
ENTRYPOINT [ "/usr/bin/memcached" ]
