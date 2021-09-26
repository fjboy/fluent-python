. ../docker_openrc.sh
. ../resource/functions.sh

docker container exists neutron-dhcp-agent
if [[ $? -ne 0 ]]; then
    mkdir /var/log/neutron && chmod 777 /var/log/neutron

    docker run -itd \
        --privileged=true \
        -v /sys/fs/cgroup:/sys/fs/cgroup \
        -v /var/log/neutron:/var/log/neutron \
        -v /etc/localtime:/etc/localtime:ro \
        -v /etc/hosts:/etc/hosts:ro \
        --network host \
        --name neutron-dhcp-agent \
        $(getDockerBuildTarget neutron-dhcp-agent)

    # docker run -itd \
    #     --privileged=true \
    #     -v /sys/fs/cgroup:/sys/fs/cgroup \
    #     -v /var/log/neutron:/var/log/neutron \
    #     -v /etc/localtime:/etc/localtime:ro \
    #     -v /etc/hosts:/etc/hosts:ro \
    #     -v /var/run/openvswitch:/var/run/openvswitch \
    #     -v /usr/bin/touch:/usr/bin/touch \
    #     -v /usr/bin/ovs-vsctl:/usr/bin/ovs-vsctl \
    #     -v /usr/sbin/ip:/usr/sbin/ip \
    #     -v /usr/sbin/route:/usr/sbin/route \
    #     --network host \
    #     --name neutron-dhcp-agent \
    #     $(getDockerBuildTarget neutron-dhcp-agent)
fi

docker cp ./neutron neutron-dhcp-agent:/etc/

# ##########################

docker exec -it neutron-dhcp-agent yum install openstack-utils -y
if [[ $? -ne 0 ]]; then
    echo "ERROR" 'install openstack-utils failed'
    exit 1
fi

withContainer neutron-dhcp-agent

# [DEFAULT]
dockerExec openstack-config --set ${NEUTRON_CONF} DEFAULT debug True || exit 1
dockerExec openstack-config --set ${NEUTRON_CONF} DEFAULT transport_url $(getRabbitmqTransportUrl)
dockerExec openstack-config --set ${NEUTRON_CONF} DEFAULT osapi_compute_listen ${NEUTRON_HOST}
dockerExec openstack-config --set ${NEUTRON_CONF} DEFAULT my_ip $(getIPByHostName ${NEUTRON_HOST})
dockerExec openstack-config --set ${NEUTRON_CONF} DEFAULT osapi_compute_workers 8
dockerExec openstack-config --set ${NEUTRON_CONF} DEFAULT core_plugin ml2
dockerExec openstack-config --set ${NEUTRON_CONF} DEFAULT service_plugins router,qos ,port_forwarding
dockerExec openstack-config --set ${NEUTRON_CONF} DEFAULT bind_host ${NEUTRON_HOST}


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



# ############ openvswitch_agent.ini

# [DEFAULT]

dockerExec openstack-config --set ${NEUTRON_OVS_AGENT_CONF} agent extensions qos
dockerExec openstack-config --set ${NEUTRON_OVS_AGENT_CONF} agent tunnel_types vxlan
dockerExec openstack-config --set ${NEUTRON_OVS_AGENT_CONF} ovs integration_bridge
dockerExec openstack-config --set ${NEUTRON_OVS_AGENT_CONF} ovs integration_bridge br-int
dockerExec openstack-config --set ${NEUTRON_OVS_AGENT_CONF} ovs enable_tuneling True
dockerExec openstack-config --set ${NEUTRON_OVS_AGENT_CONF} ovs tunnel_bridge br-tun
dockerExec openstack-config --set ${NEUTRON_OVS_AGENT_CONF} ovs local_ip $(getIPByHostName ${NEUTRON_HOST})
dockerExec openstack-config --set ${NEUTRON_OVS_AGENT_CONF} ovs bridge_mappings physnet1:br-ex 
dockerExec openstack-config --set ${NEUTRON_OVS_AGENT_CONF} securitygroup firewall_driver neutron.agent.linux.iptables_firewall.OVSHybridIptablesFirewallDriver
dockerExec openstack-config --set ${NEUTRON_OVS_AGENT_CONF} securitygroup enable_security_group false
dockerExec openstack-config --set ${NEUTRON_OVS_AGENT_CONF} securitygroup enable_ipset false


# ############ dhcp_agent.ini

# [DEFAULT]

dockerExec openstack-config --set ${NEUTRON_DHCP_AGENT_CONF} DEFAULT dhcp_lease_duration -1
dockerExec openstack-config --set ${NEUTRON_DHCP_AGENT_CONF} DEFAULT interface_driver neutron.agent.linux.interface.OVSInterfaceDriver
dockerExec openstack-config --set ${NEUTRON_DHCP_AGENT_CONF} DEFAULT dhcp_driver neutron.agent.linux.dhcp.Dnsmasq
dockerExec openstack-config --set ${NEUTRON_DHCP_AGENT_CONF} DEFAULT dhcp_delete_namespaces True
dockerExec openstack-config --set ${NEUTRON_DHCP_AGENT_CONF} DEFAULT use_namespaces True
dockerExec openstack-config --set ${NEUTRON_DHCP_AGENT_CONF} DEFAULT dnsmasq_config_file /etc/neutron/dnsmasq-neutron.conf
dockerExec openstack-config --set ${NEUTRON_DHCP_AGENT_CONF} DEFAULT enable_isolated_metadata True

dockerExec touch /etc/neutron/dnsmasq-neutron.conf
dockerExec chmod 777 /etc/neutron/dnsmasq-neutron.conf

dockerExec systemctl enable openvswitch neutron-openvswitch-agent
# dockerExec systemctl start neutron-openvswitch-agent

# ########## ml2.ini

# [ml2]
dockerExec openstack-config --set ${NEUTRON_ML2_CONF} ml2 type_drivers vxlan,flat
dockerExec openstack-config --set ${NEUTRON_ML2_CONF} ml2 tenant_network_types vxlan
dockerExec openstack-config --set ${NEUTRON_ML2_CONF} ml2 mechanism_drivers openvswitch
dockerExec openstack-config --set ${NEUTRON_ML2_CONF} ml2 extension_drivers port_security,qos

# [ml2_type_vlan]
dockerExec openstack-config --set ${NEUTRON_ML2_CONF} ml2_type_flat flat_networks provider

# [ml2_type_vlan]
dockerExec openstack-config --set ${NEUTRON_ML2_CONF} ml2_type_vlan network_vlan_ranges physnet1:858:876

# [ml2_type_vxlan]
dockerExec openstack-config --set ${NEUTRON_ML2_CONF} ml2_type_vxlan vni_ranges 1:100000

# [securitygroup]
dockerExec openstack-config --set ${NEUTRON_ML2_CONF} securitygroup firewall_driver neutron.agent.linux.iptables_firewall.OVSHybridIptablesFirewallDriver
dockerExec openstack-config --set ${NEUTRON_ML2_CONF} securitygroup enable_security_group true
dockerExec openstack-config --set ${NEUTRON_ML2_CONF} securitygroup enable_ipset true

dockerExec ln -s /etc/neutron/plugins/ml2/ml2_conf.ini /etc/neutron/plugin.ini

dockerRestart

exitContainer
