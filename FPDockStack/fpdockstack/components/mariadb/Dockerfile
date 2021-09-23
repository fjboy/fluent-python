FROM centos:7

RUN cd /etc/yum.repos.d && mkdir backup && mv *.repo backup
COPY *.repo /etc/yum.repos.d/
RUN yum clean all \
    && yum install -y mariadb mariadb-server \
    && systemctl enable mariadb \
    && yum clean all
EXPOSE 3306
ENTRYPOINT [ "/usr/sbin/init" ]
