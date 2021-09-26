source ../docker_openrc.sh
. ../resource/functions.sh

# ##########################

docker cp glance glance:/etc/
docker exec -it glance yum install -y openstack-utils
docker exec -it glance openstack-config --set ${GLANCE_CONF_API} DEFAULT bind_host ${GLANCE_HOST}
docker exec -it glance openstack-config --set ${GLANCE_CONF_API} DEFAULT registry_host ${GLANCE_HOST}

docker exec -it glance openstack-config --set ${GLANCE_CONF_API} database connection mysql+pymysql://${GLANCE_DB_USER}:${GLANCE_DB_PASSWORD}@${DB_HOST}/glance

# config
docker exec -it glance openstack-config --set ${GLANCE_CONF_API} keystone_authtoken auth_uri http://${KEYSTONE_HOST}:5000
docker exec -it glance openstack-config --set ${GLANCE_CONF_API} keystone_authtoken auth_url http://${KEYSTONE_HOST}:35357
docker exec -it glance openstack-config --set ${GLANCE_CONF_API} keystone_authtoken memcached_servers ${MEMCACHED_SERVERS}
docker exec -it glance openstack-config --set ${GLANCE_CONF_API} keystone_authtoken username ${GLANCE_AUTH_USER}
docker exec -it glance openstack-config --set ${GLANCE_CONF_API} keystone_authtoken password ${GLANCE_AUTH_PASSWORD}
docker exec -it glance openstack-config --set ${GLANCE_CONF_API} keystone_authtoken region_name RegionOne

docker exec -it glance openstack-config --set ${GLANCE_CONF_API} cinder os_region_name RegionOne

docker exec -it glance openstack-config --set ${GLANCE_CONF_API} glance_store stores file,http
docker exec -it glance openstack-config --set ${GLANCE_CONF_API} glance_store default_store file


docker exec -it glance openstack-config --set ${GLANCE_CONF_REGISTRY} DEFAULT bind_host ${GLANCE_HOST}
docker exec -it glance openstack-config --set ${GLANCE_CONF_REGISTRY} DEFAULT workers 4
docker exec -it glance openstack-config --set ${GLANCE_CONF_REGISTRY} database connection mysql+pymysql://${GLANCE_DB_USER}:${GLANCE_DB_PASSWORD}@${DB_HOST}/glance

docker exec -it glance openstack-config --set ${GLANCE_CONF_REGISTRY} keystone_authtoken auth_uri http://${KEYSTONE_HOST}:5000
docker exec -it glance openstack-config --set ${GLANCE_CONF_REGISTRY} keystone_authtoken auth_url http://${KEYSTONE_HOST}:35357
docker exec -it glance openstack-config --set ${GLANCE_CONF_REGISTRY} keystone_authtoken memcached_servers ${MEMCACHED_SERVERS}
docker exec -it glance openstack-config --set ${GLANCE_CONF_REGISTRY} keystone_authtoken username ${GLANCE_AUTH_USER}
docker exec -it glance openstack-config --set ${GLANCE_CONF_REGISTRY} keystone_authtoken password ${GLANCE_AUTH_PASSWORD}
docker exec -it glance openstack-config --set ${GLANCE_CONF_REGISTRY} keystone_authtoken region_name RegionOne

if [[ $? -ne 0 ]];then
    logError "config error"
    exit 1
fi

docker exec -it glance su -s /bin/sh -c "glance-manage db_sync" glance

docker exec -it glance systemctl start openstack-glance-api.service openstack-glance-registry.service

glance image-create --progress --container-format bare --disk-format qcow2 --name cirros < cirros.qcow2