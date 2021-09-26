. ../resource/functions.sh

source ../docker_openrc.sh

docker exec -it mariadb mysql -uroot -proot123 -e "create database IF NOT EXISTS nova;"
docker exec -it mariadb mysql -uroot -proot123 -e "grant all privileges on nova.* to 'nova'@'localhost' identified by 'nova123' with grant option;"
docker exec -it mariadb mysql -uroot -proot123 -e "grant all privileges on nova.* to 'nova'@'%' identified by 'nova123' with grant option;"

docker exec -it mariadb mysql -uroot -proot123 -e "create database IF NOT EXISTS nova_api;"
docker exec -it mariadb mysql -uroot -proot123 -e "grant all privileges on nova_api.* to 'nova'@'localhost' identified by 'nova123' with grant option;"
docker exec -it mariadb mysql -uroot -proot123 -e "grant all privileges on nova_api.* to 'nova'@'%' identified by 'nova123' with grant option;"

docker exec -it mariadb mysql -uroot -proot123 -e "create database IF NOT EXISTS nova_cell0;"
docker exec -it mariadb mysql -uroot -proot123 -e "grant all privileges on nova_cell0.* to 'nova'@'localhost' identified by 'nova123' with grant option;"
docker exec -it mariadb mysql -uroot -proot123 -e "grant all privileges on nova_cell0.* to 'nova'@'%' identified by 'nova123' with grant option;"

export NOVA_HOST=ebm-vm-host-2
export NOVA_AUTH_USER=nova
export NOVA_AUTH_PASSWORD=nova123


source /admin_openrc.sh

# nova api
openstack user create ${NOVA_AUTH_USER} --password ${NOVA_AUTH_PASSWORD}
openstack role add --project service --user ${NOVA_AUTH_USER} admin

openstack service create --name nova --description 'OpenStack Compute' compute
openstack endpoint create --region RegionOne compute public http://${NOVA_HOST}:8774/v2.1
openstack endpoint create --region RegionOne compute internal http://${NOVA_HOST}:8774/v2.1
openstack endpoint create --region RegionOne compute admin http://${NOVA_HOST}:8774/v2.1


# placement
openstack user create --domain default --password ${NOVA_PLACEMENT_AUTH_PASSWORD} ${NOVA_PLACEMENT_AUTH_USER}
openstack role add --project service --user ${NOVA_PLACEMENT_AUTH_USER} admin
openstack service create --name placement --description 'OpenStack Placement' placement
openstack endpoint create --region RegionOne placement public http://${NOVA_HOST}:8778
openstack endpoint create --region RegionOne placement admin http://${NOVA_HOST}:8778
openstack endpoint create --region RegionOne placement internal http://${NOVA_HOST}:8778

# nova center compute api
openstack service create --name centercompute --description 'OpenStack Center Compute API' centercompute
openstack endpoint create --region RegionOne centercompute public http://${NOVA_HOST}:8780/v1
openstack endpoint create --region RegionOne centercompute admin http://${NOVA_HOST}:8780/v1
openstack endpoint create --region RegionOne centercompute internal http://${NOVA_HOST}:8780/v1


openstack user create --domain default --password=${CENTERCOMPUTE_AUTH_PASSWORD} ${NOVA_CENTERCOMPUTE_AUTH_USER}
openstack role add --project service --user ${NOVA_CENTERCOMPUTE_AUTH_USER} admin


# ################# nova api ##########################
image=bclinux/nova-api

mkdir /var/log/nova && chmod 777 /var/log/nova
docker run -itd \
    --privileged=true \
    -v /etc/hosts:/etc/hosts \
    -v /sys/fs/cgroup:/sys/fs/cgroup \
    -v /var/log/nova:/var/log/nova \
    --network host \
    --name nova-api \
    ${image}

docker cp ./nova    nova-api:/etc/

# ##########################

image=bclinux/nova-scheduler

mkdir /var/log/nova && chmod 777 /var/log/nova
docker run -itd \
    --privileged=true \
    -v /etc/hosts:/etc/hosts \
    -v /sys/fs/cgroup:/sys/fs/cgroup \
    -v /var/log/nova:/var/log/nova \
    --network host \
    --name nova-scheduler \
    ${image}

docker cp ./nova    nova-api:/etc/


# ##########################



docker exec -it nova-api yum install openstack-utils -y
if [[ $? -ne 0 ]]; then
    echo "ERROR" 'install openstack-utils failed'
    exit 1
fi

docker exec -it nova-api yum install -y openstack-utils
# [DEFAULT]
docker exec -it nova-api openstack-config --set ${NOVA_CONF} DEFAULT debug True
docker exec -it nova-api openstack-config --set ${NOVA_CONF} DEFAULT transport_url rabbit://${RABBITMQ_SERVERS}
docker exec -it nova-api openstack-config --set ${NOVA_CONF} DEFAULT osapi_compute_listen ${NOVA_HOST}
docker exec -it nova-api openstack-config --set ${NOVA_CONF} DEFAULT my_ip ${NOVA_HOST}
docker exec -it nova-api openstack-config --set ${NOVA_CONF} DEFAULT osapi_compute_workers 8

# [VNC]
docker exec -it nova-api openstack-config --set ${NOVA_CONF} vnc novncproxy_host ${NOVA_HOST}
docker exec -it nova-api openstack-config --set ${NOVA_CONF} vnc vncserver_proxyclient_address ${NOVA_HOST}

# [database]
docker exec -it nova-api openstack-config --set ${NOVA_CONF} database connection mysql+pymysql://${NOVA_DB_USER}:${NOVA_DB_PASSWORD}@${DB_HOST}/nova

# [placement_database]
docker exec -it nova-api openstack-config --set ${NOVA_CONF} placement_database connection mysql+pymysql://${NOVA_DB_USER}:${NOVA_DB_PASSWORD}@${DB_HOST}/nova_api
# [placement]

docker exec -it nova-api openstack-config --set ${NOVA_CONF} placement auth_uri http://${KEYSTONE_HOST}:5000
docker exec -it nova-api openstack-config --set ${NOVA_CONF} placement auth_url http://${KEYSTONE_HOST}:35357
docker exec -it nova-api openstack-config --set ${NOVA_CONF} placement username ${NOVA_PLACEMENT_AUTH_USER}
docker exec -it nova-api openstack-config --set ${NOVA_CONF} placement password ${NOVA_PLACEMENT_AUTH_PASSWORD}
docker exec -it nova-api openstack-config --set ${NOVA_CONF} placement os_region_name RegionOne

# [keystone_authtoken]
docker exec -it nova-api openstack-config --set ${NOVA_CONF} keystone_authtoken auth_uri http://${KEYSTONE_HOST}:5000
docker exec -it nova-api openstack-config --set ${NOVA_CONF} keystone_authtoken auth_url http://${KEYSTONE_HOST}:35357
docker exec -it nova-api openstack-config --set ${NOVA_CONF} keystone_authtoken memcached_servers ${MEMCACHED_SERVERS}
docker exec -it nova-api openstack-config --set ${NOVA_CONF} keystone_authtoken username ${NOVA_AUTH_USER}
docker exec -it nova-api openstack-config --set ${NOVA_CONF} keystone_authtoken password ${NOVA_AUTH_PASSWORD}
docker exec -it nova-api openstack-config --set ${NOVA_CONF} keystone_authtoken region_name RegionOne

# [neutron]
docker exec -it nova-api openstack-config --set ${NOVA_CONF} neutron url http://${NEUTRON_HOST}:9696
docker exec -it nova-api openstack-config --set ${NOVA_CONF} neutron username ${NEUTRON_AUTH_USER}
docker exec -it nova-api openstack-config --set ${NOVA_CONF} neutron password ${NEUTRON_AUTH_PASSWORD}
docker exec -it nova-api openstack-config --set ${NOVA_CONF} neutron auth_url http://${KEYSTONE_HOST}:35357
docker exec -it nova-api openstack-config --set ${NOVA_CONF} neutron region_name RegionOne

# [api_database]
docker exec -it nova-api openstack-config --set ${NOVA_CONF} api_database connection mysql+pymysql://${NOVA_DB_USER}:${NOVA_DB_PASSWORD}@${DB_HOST}/nova_api

# [cache]
docker exec -it nova-api openstack-config --set ${NOVA_CONF} cache memcache_servers ${MEMCACHED_SERVERS}

# [center_compute_api]
docker exec -it nova-api openstack-config --set ${NOVA_CONF} center_compute_api os_region_name RegionOne
docker exec -it nova-api openstack-config --set ${NOVA_CONF} center_compute_api auth_url http://${KEYSTONE_HOST}:35357/v3
docker exec -it nova-api openstack-config --set ${NOVA_CONF} center_compute_api memcached_servers ${MEMCACHED_SERVERS}
docker exec -it nova-api openstack-config --set ${NOVA_CONF} center_compute_api username ${NOVA_CENTERCOMPUTE_AUTH_USER}
docker exec -it nova-api openstack-config --set ${NOVA_CONF} center_compute_api password ${NOVA_CENTERCOMPUTE_AUTH_PASSWORD}

# [cinder]
docker exec -it nova-api openstack-config --set ${NOVA_CONF} cinder os_region_name RegionOne

# [conductor]
docker exec -it nova-api openstack-config --set ${NOVA_CONF} conductor workers 8


# [glance]
docker exec -it nova-api openstack-config --set ${NOVA_CONF} glance api_servers  http://${GLANCE_HOST}:9292


# sync db

docker exec -it nova-api su -s /bin/sh -c "nova-manage api_db sync" nova
docker exec -it nova-api su -s /bin/sh -c "nova-manage cell_v2 map_cell0" nova
docker exec -it nova-api su -s /bin/sh -c "nova-manage cell_v2 create_cell --name=cell1 --verbose" nova
docker exec -it nova-api su -s /bin/sh -c "nova-manage db sync" nova
