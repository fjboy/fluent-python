FROM centos:7

RUN cd /etc/yum.repos.d && mkdir backup && mv *.repo backup
COPY *.repo /etc/yum.repos.d/
RUN rpm --rebuilddb \
    && yum -y install openstack-keystone python-keystone httpd mod_wsgi python-openstackclient python-memcached openstack-utils \
    && cp /usr/share/keystone/wsgi-keystone.conf /etc/httpd/conf.d/ \
    && yum clean all \
    && systemctl enable httpd
RUN sed -i 's|^#ServerName .*|ServerName 0.0.0.0|g' /etc/httpd/conf/httpd.conf
RUN keystone-manage credential_setup --keystone-user keystone --keystone-group keystone
RUN keystone-manage fernet_setup --keystone-user keystone --keystone-group keystone
EXPOSE 35357 5000
ENTRYPOINT [ "/usr/sbin/init" ]
