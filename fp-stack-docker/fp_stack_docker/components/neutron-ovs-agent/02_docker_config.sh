. ../docker_openrc.sh
. ../resource/functions.sh

docker container exists neutron-ovs-agent 
if [[ $? -ne 0 ]]; then
    mkdir /var/log/neutron && chmod 777 /var/log/neutron
    docker run -itd \
        --privileged=true \
        -v /sys/fs/cgroup:/sys/fs/cgroup \
        -v /var/log/neutron:/var/log/neutron \
        -v /etc/localtime:/etc/localtime:ro \
        -v /etc/hosts:/etc/hosts:ro \
        --network host \
        --name neutron-ovs-agent \
        $(getDockerBuildTarget neutron-ovs-agent)
fi

docker cp ./neutron neutron-ovs-agent:/etc/

# ##########################

docker exec -it neutron-ovs-agent yum install openstack-utils -y
if [[ $? -ne 0 ]]; then
    echo "ERROR" 'install openstack-utils failed'
    exit 1
fi

withContainer neutron-ovs-agent

# [DEFAULT]
dockerExec openstack-config --set ${NEUTRON_CONF} DEFAULT debug True || exit 1
dockerExec openstack-config --set ${NEUTRON_CONF} DEFAULT transport_url $(getRabbitmqTransportUrl)
dockerExec openstack-config --set ${NEUTRON_CONF} DEFAULT osapi_compute_listen ${NEUTRON_HOST}
dockerExec openstack-config --set ${NEUTRON_CONF} DEFAULT my_ip $(getIPByHostName ${NEUTRON_HOST})
dockerExec openstack-config --set ${NEUTRON_CONF} DEFAULT osapi_compute_workers 8
dockerExec openstack-config --set ${NEUTRON_CONF} DEFAULT core_plugin ml2
dockerExec openstack-config --set ${NEUTRON_CONF} DEFAULT service_plugins router,qos ,port_forwarding
dockerExec openstack-config --set ${NEUTRON_CONF} DEFAULT bind_host $(getIPByHostName ${NEUTRON_HOST})


# [database]
dockerExec openstack-config --set ${NEUTRON_CONF} database connection mysql+pymysql://${NEUTRON_DB_USER}:${NEUTRON_DB_PASSWORD}@${DB_HOST}/neutron

# [keystone_authtoken]
dockerExec openstack-config --set ${NEUTRON_CONF} keystone_authtoken auth_uri http://${KEYSTONE_HOST}:5000
dockerExec openstack-config --set ${NEUTRON_CONF} keystone_authtoken auth_url http://${KEYSTONE_HOST}:35357
dockerExec openstack-config --set ${NEUTRON_CONF} keystone_authtoken memcached_servers $(getMemcachedServers)
dockerExec openstack-config --set ${NEUTRON_CONF} keystone_authtoken username ${NEUTRON_AUTH_USER}
dockerExec openstack-config --set ${NEUTRON_CONF} keystone_authtoken password ${NEUTRON_AUTH_PASSWORD}
dockerExec openstack-config --set ${NEUTRON_CONF} keystone_authtoken region_name RegionOne

# [nova]
dockerExec openstack-config --set ${NEUTRON_CONF} nova auth_url http://${KEYSTONE_HOST}:35357
dockerExec openstack-config --set ${NEUTRON_CONF} nova region_name RegionOne
dockerExec openstack-config --set ${NEUTRON_CONF} nova project_name service
dockerExec openstack-config --set ${NEUTRON_CONF} nova username ${NOVA_AUTH_USER}
dockerExec openstack-config --set ${NEUTRON_CONF} nova password ${NOVA_AUTH_PASSWORD}

# [PRODUCTINFO]
dockerExec openstack-config --set ${NEUTRON_CONF} PRODUCTINFO productversion  4.7.1


# ########## ml2.ini

# [ml2]
dockerExec openstack-config --set ${NEUTRON_ML2_CONF} ml2 type_drivers vxlan,flat
dockerExec openstack-config --set ${NEUTRON_ML2_CONF} ml2 tenant_network_types vxlan
dockerExec openstack-config --set ${NEUTRON_ML2_CONF} ml2 mechanism_drivers openvswitch
dockerExec openstack-config --set ${NEUTRON_ML2_CONF} ml2 extension_drivers port_security,qos
# [ml2_type_vlan]
dockerExec openstack-config --set ${NEUTRON_ML2_CONF} ml2_type_vlan network_vlan_ranges physnet1:858:876

# [ml2_type_vxlan]
dockerExec openstack-config --set ${NEUTRON_ML2_CONF} ml2_type_vxlan vni_ranges 1:100000

# [securitygroup]
dockerExec openstack-config --set ${NEUTRON_ML2_CONF} securitygroup firewall_driver neutron.agent.linux.iptables_firewall.OVSHybridIptablesFirewallDriver
dockerExec openstack-config --set ${NEUTRON_ML2_CONF} securitygroup enable_security_group true
dockerExec openstack-config --set ${NEUTRON_ML2_CONF} securitygroup enable_ipset true

dockerExec ln -s /etc/neutron/plugins/ml2/ml2_conf.ini /etc/neutron/plugin.ini

dockerExec systemctl restart neutron-openvswitch-agent

exitContainer
