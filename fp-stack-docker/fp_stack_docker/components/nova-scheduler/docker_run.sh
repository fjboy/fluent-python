. ../docker_openrc.sh
. ../resource/functions.sh

# ################# nova api ##########################

docker container exists nova-scheduler
if [[ $? -ne 0 ]]; then
    mkdir /var/log/nova && chmod 777 /var/log/nova
    logInfo "start container"
    docker run -itd \
        --privileged=true \
        -v /etc/hosts:/etc/hosts \
        -v /sys/fs/cgroup:/sys/fs/cgroup \
        -v /var/log/nova:/var/log/nova \
        --network host \
        --name nova-scheduler \
        $(getDockerBuildTarget nova-scheduler)

    if [[ $? -ne 0 ]]; then
        logError "start nova-scheluder failed"
        exit 1
    fi
    docker cp ./nova    nova-scheduler:/etc/
fi


# ##########################
withContainer nova-scheduler
dockerExec rpm -q openstack-utils
if [[ $? -ne 0 ]]; then
    logInfo "install opesntack-utils"
    dockerExec yum install -y openstack-utils
    if [[ $? -ne 0 ]]; then
        logError 'install openstack-utils failed'
        exit 1
    fi
fi



# [DEFAULT]
dockerExec openstack-config --set ${NOVA_CONF} DEFAULT debug True || exit 1
dockerExec openstack-config --set ${NOVA_CONF} DEFAULT transport_url $(getRabbitmqTransportUrl)
dockerExec openstack-config --set ${NOVA_CONF} DEFAULT osapi_compute_listen ${NOVA_HOST}
dockerExec openstack-config --set ${NOVA_CONF} DEFAULT my_ip ${NOVA_HOST}
dockerExec openstack-config --set ${NOVA_CONF} DEFAULT osapi_compute_workers 8

# [VNC]
dockerExec openstack-config --set ${NOVA_CONF} vnc novncproxy_host ${NOVA_HOST}
dockerExec openstack-config --set ${NOVA_CONF} vnc vncserver_proxyclient_address ${NOVA_HOST}

# [database]
dockerExec openstack-config --set ${NOVA_CONF} database connection mysql+pymysql://${NOVA_DB_USER}:${NOVA_DB_PASSWORD}@${DB_HOST}/nova

# [placement_database]
dockerExec openstack-config --set ${NOVA_CONF} placement_database connection mysql+pymysql://${NOVA_DB_USER}:${NOVA_DB_PASSWORD}@${DB_HOST}/nova_api
# [placement]

dockerExec openstack-config --set ${NOVA_CONF} placement auth_uri http://${KEYSTONE_HOST}:5000
dockerExec openstack-config --set ${NOVA_CONF} placement auth_url http://${KEYSTONE_HOST}:35357
dockerExec openstack-config --set ${NOVA_CONF} placement username ${NOVA_PLACEMENT_AUTH_USER}
dockerExec openstack-config --set ${NOVA_CONF} placement password ${NOVA_PLACEMENT_AUTH_PASSWORD}
dockerExec openstack-config --set ${NOVA_CONF} placement os_region_name RegionOne

# [keystone_authtoken]
dockerExec openstack-config --set ${NOVA_CONF} keystone_authtoken auth_uri http://${KEYSTONE_HOST}:5000
dockerExec openstack-config --set ${NOVA_CONF} keystone_authtoken auth_url http://${KEYSTONE_HOST}:35357
dockerExec openstack-config --set ${NOVA_CONF} keystone_authtoken memcached_servers $(getMemcachedServers)
dockerExec openstack-config --set ${NOVA_CONF} keystone_authtoken username ${NOVA_AUTH_USER}
dockerExec openstack-config --set ${NOVA_CONF} keystone_authtoken password ${NOVA_AUTH_PASSWORD}
dockerExec openstack-config --set ${NOVA_CONF} keystone_authtoken region_name RegionOne

# [neutron]
dockerExec openstack-config --set ${NOVA_CONF} neutron url http://${NEUTRON_HOST}
dockerExec openstack-config --set ${NOVA_CONF} neutron username ${NEUTRON_AUTH_USER}
dockerExec openstack-config --set ${NOVA_CONF} neutron password ${NEUTRON_AUTH_PASSWORD}
dockerExec openstack-config --set ${NOVA_CONF} neutron auth_url http://${KEYSTONE_HOST}:35357
dockerExec openstack-config --set ${NOVA_CONF} neutron region_name RegionOne

# [api_database]
dockerExec openstack-config --set ${NOVA_CONF} api_database connection mysql+pymysql://${NOVA_DB_USER}:${NOVA_DB_PASSWORD}@${DB_HOST}/nova_api

# [cache]
dockerExec openstack-config --set ${NOVA_CONF} cache memcache_servers $(getMemcachedServers)

# [center_compute_api]
dockerExec openstack-config --set ${NOVA_CONF} center_compute_api os_region_name RegionOne
dockerExec openstack-config --set ${NOVA_CONF} center_compute_api auth_url http://${KEYSTONE_HOST}:35357/v3
dockerExec openstack-config --set ${NOVA_CONF} center_compute_api memcached_servers $(getMemcachedServers)
dockerExec openstack-config --set ${NOVA_CONF} center_compute_api username ${NOVA_CENTERCOMPUTE_AUTH_USER}
dockerExec openstack-config --set ${NOVA_CONF} center_compute_api password ${NOVA_CENTERCOMPUTE_AUTH_PASSWORD}

# [cinder]
dockerExec openstack-config --set ${NOVA_CONF} cinder os_region_name RegionOne

# [conductor]
dockerExec openstack-config --set ${NOVA_CONF} conductor workers 8


# [glance]
dockerExec openstack-config --set ${NOVA_CONF} glance api_servers  http://${GLANCE_HOST}:9292


# sync db
exitContainer
