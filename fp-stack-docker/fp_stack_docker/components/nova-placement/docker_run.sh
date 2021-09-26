. ../docker_openrc.sh
. ../resource/functions.sh


docker container exists nova-compute
if [[ $? -ne 0 ]]; then
    mkdir /var/log/nova && chmod 777 /var/log/nova
    mkdir /var/lib/nova && chmod 777 /var/lib/nova
    mkdir /var/lib/nova/instances && chmod 777 /var/lib/nova/instances

    logInfo "start container nova-placement"
    docker run -itd \
        --privileged --net=host --pid=host \
        -v /etc/passwd:/etc/passwd:ro \
        -v /etc/shadow:/etc/shadow:ro \
        -v /etc/group:/etc/group:ro \
        -v /etc/gshadow:/etc/gshadow:ro \
        -v /etc/localtime:/etc/localtime:ro \
        -v /etc/hosts:/etc/hosts:ro \
        -v /root/.ssh:/root/.ssh \
        -v /var/lib/nova:/var/lib/nova \
        -v /var/log/nova:/var/log/nova \
        -v /var/run/libvirt:/var/run/libvirt \
        -v /var/run/openvswitch:/var/run/openvswitch \
        -v /usr/bin/ovs-vsctl:/usr/bin/ovs-vsctl \
        -v /var/lib/nova/instances:/var/lib/nova/instances \
        --network ${DOCKER_RUN_NETWORK} \
        --name nova-compute \
        $(getDockerBuildTarget nova-compute)

    if [[ $? -ne 0 ]]; then
        logError "start nova-compute failed"
        exit 1
    fi
    docker cp ./nova    nova-compute:/etc/
fi

# ##########################
withContainer nova-compute
dockerExec rpm -q openstack-utils
if [[ $? -ne 0 ]]; then
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
dockerExec openstack-config --set ${NOVA_CONF} DEFAULT my_ip $(getIPByHostName ${NOVA_HOST})
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
dockerExec openstack-config --set ${NOVA_CONF} neutron url http://${NEUTRON_HOST}:9696
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

docker restart nova-conductor
