FROM centos:7

RUN cd /etc/yum.repos.d && mkdir backup && mv *.repo backup
COPY ../yum.repos.d/*.repo /etc/yum.repos.d/
COPY entrypoint.sh /
RUN yum clean all && yum install -y httpd openstack-dashboard && yum clean all 
RUN sed -i "s|ALLOWED_HOSTS *=.*|ALLOWED_HOSTS = ['*', ]|g" /etc/openstack-dashboard/local_settings \
    && sed -i "s|.*ServerName.*:.*|ServerName localhost:80|g" /etc/httpd/conf/httpd.conf \
    && chmod u+x /entrypoint.sh
EXPOSE 80
ENTRYPOINT [ "sh", "/entrypoint.sh" ]
