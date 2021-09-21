# ##########################
export DB_HOST=ebm-vm-host-2

export CINDER_CONF=/etc/cinder/cinder.conf
export CINDER_DB_USER=cinder
export CINDER_DB_PASSWORD=cinder123
export RABBITMQ_USER=openstack
export RABBITMQ_PASSWORD=rabbitmq123
export RABBITMQ_SERVERS=${RABBITMQ_USER}:${RABBITMQ_PASSWORD}@ebm-vm-host-2:5672
export RABBITMQ_HOSTS=ebm-vm-host-2:5672

export MEMCACHED_SERVERS=ebm-vm-host-2:11211

# ##########################

docker cp cinder cinder:/etc/


# config DEFAULT

docker exec -it cinder openstack-config --set ${CINDER_CONF} DEFAULT debug True
docker exec -it cinder openstack-config --set ${CINDER_CONF} DEFAULT transport_url rabbit://${RABBITMQ_SERVERS}
docker exec -it cinder openstack-config --set ${CINDER_CONF} DEFAULT default_volume_type local
docker exec -it cinder openstack-config --set ${CINDER_CONF} DEFAULT my_ip ${CINDER_HOST}
docker exec -it cinder openstack-config --set ${CINDER_CONF} DEFAULT osapi_volume_listen ${CINDER_HOST}
docker exec -it cinder openstack-config --set ${CINDER_CONF} DEFAULT host ${CINDER_HOST}
docker exec -it cinder openstack-config --set ${CINDER_CONF} DEFAULT glance_api_servers http://${GLANCE_HOST}:9292
docker exec -it cinder openstack-config --set ${CINDER_CONF} DEFAULT image_cache_volume_types 

# config database
docker exec -it cinder openstack-config --set ${CINDER_CONF} database connection mysql+pymysql://${CINDER_DB_USER}:${CINDER_DB_PASSWORD}@${DB_HOST}/cinder

docker exec -it cinder openstack-config --set ${CINDER_CONF} keystone_authtoken auth_uri http://${KEYSTONE_HOST}:5000
docker exec -it cinder openstack-config --set ${CINDER_CONF} keystone_authtoken auth_url http://${KEYSTONE_HOST}:35357
docker exec -it cinder openstack-config --set ${CINDER_CONF} keystone_authtoken memcached_servers ${MEMCACHED_SERVERS}
docker exec -it cinder openstack-config --set ${CINDER_CONF} keystone_authtoken username ${CINDER_AUTH_USER}
docker exec -it cinder openstack-config --set ${CINDER_CONF} keystone_authtoken password ${CINDER_AUTH_PASSWORD}
docker exec -it cinder openstack-config --set ${CINDER_CONF} keystone_authtoken region_name RegionOne

docker exec -it cinder openstack-config --set ${CINDER_CONF} nova region_name RegionOne
docker exec -it cinder openstack-config --set ${CINDER_CONF} oslo_concurrency lock_path /var/lib/cinder/tmp
docker exec -it cinder openstack-config --set ${CINDER_CONF} oslo_messaging_rabbit rabbit_ha_queues True



export CINDER_CONF_REGISTRY=/etc/cinder/cinder-registry.conf



docker exec -it cinder su -s /bin/sh -c "cinder-manage db sync" cinder
