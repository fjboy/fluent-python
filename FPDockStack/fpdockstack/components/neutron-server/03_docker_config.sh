source ../docker_openrc.sh
. ../resource/functions.sh

logInfo "config ..."
# [DEFAULT]
docker exec -it neutron-server openstack-config --set ${NEUTRON_CONF} DEFAULT debug True || exit 1
docker exec -it neutron-server openstack-config --set ${NEUTRON_CONF} DEFAULT transport_url $(getRabbitmqTransportUrl)
docker exec -it neutron-server openstack-config --set ${NEUTRON_CONF} DEFAULT osapi_compute_listen ${NOVA_HOST}
docker exec -it neutron-server openstack-config --set ${NEUTRON_CONF} DEFAULT my_ip ${NOVA_HOST}
docker exec -it neutron-server openstack-config --set ${NEUTRON_CONF} DEFAULT osapi_compute_workers 8
docker exec -it neutron-server openstack-config --set ${NEUTRON_CONF} DEFAULT core_plugin ml2
docker exec -it neutron-server openstack-config --set ${NEUTRON_CONF} DEFAULT service_plugins router,qos ,port_forwarding
docker exec -it neutron-server openstack-config --set ${NEUTRON_CONF} DEFAULT bind_host $(getIPByHostName ${NEUTRON_HOST})


# [database]
docker exec -it neutron-server openstack-config --set ${NEUTRON_CONF} database connection mysql+pymysql://${NEUTRON_DB_USER}:${NEUTRON_DB_PASSWORD}@${DB_HOST}/neutron

# [keystone_authtoken]
docker exec -it neutron-server openstack-config --set ${NEUTRON_CONF} keystone_authtoken auth_uri http://${KEYSTONE_HOST}:5000
docker exec -it neutron-server openstack-config --set ${NEUTRON_CONF} keystone_authtoken auth_url http://${KEYSTONE_HOST}:35357
docker exec -it neutron-server openstack-config --set ${NEUTRON_CONF} keystone_authtoken memcached_servers ${MEMCACHED_SERVERS}
docker exec -it neutron-server openstack-config --set ${NEUTRON_CONF} keystone_authtoken username ${NEUTRON_AUTH_USER}
docker exec -it neutron-server openstack-config --set ${NEUTRON_CONF} keystone_authtoken password ${NEUTRON_AUTH_PASSWORD}
docker exec -it neutron-server openstack-config --set ${NEUTRON_CONF} keystone_authtoken region_name RegionOne

# [nova]
docker exec -it neutron-server openstack-config --set ${NEUTRON_CONF} nova auth_url http://${KEYSTONE_HOST}:35357
docker exec -it neutron-server openstack-config --set ${NEUTRON_CONF} nova region_name RegionOne
docker exec -it neutron-server openstack-config --set ${NEUTRON_CONF} nova project_name service
docker exec -it neutron-server openstack-config --set ${NEUTRON_CONF} nova username ${NOVA_AUTH_USER}
docker exec -it neutron-server openstack-config --set ${NEUTRON_CONF} nova password ${NOVA_AUTH_PASSWORD}

# [PRODUCTINFO]
docker exec -it neutron-server openstack-config --set ${NEUTRON_CONF} PRODUCTINFO productversion  4.7.1


# ############### ml2.ini


# [ml2]
docker exec -it neutron-server openstack-config --set ${NEUTRON_ML2_CONF} ml2 type_drivers vxlan,flat
docker exec -it neutron-server openstack-config --set ${NEUTRON_ML2_CONF} ml2 tenant_network_types vxlan
docker exec -it neutron-server openstack-config --set ${NEUTRON_ML2_CONF} ml2 mechanism_drivers openvswitch
docker exec -it neutron-server openstack-config --set ${NEUTRON_ML2_CONF} ml2 extension_drivers port_security,qos
# [ml2_type_vlan]
docker exec -it neutron-server openstack-config --set ${NEUTRON_ML2_CONF} ml2_type_vlan network_vlan_ranges physnet1:858:876

# [ml2_type_vxlan]
docker exec -it neutron-server openstack-config --set ${NEUTRON_ML2_CONF} ml2_type_vxlan vni_ranges 1:100000

# [securitygroup]
docker exec -it neutron-server openstack-config --set ${NEUTRON_ML2_CONF} securitygroup firewall_driver neutron.agent.linux.iptables_firewall.OVSHybridIptablesFirewallDriver
docker exec -it neutron-server openstack-config --set ${NEUTRON_ML2_CONF} securitygroup enable_security_group true
docker exec -it neutron-server openstack-config --set ${NEUTRON_ML2_CONF} securitygroup enable_ipset true



docker exec -it neutron-server ln -s /etc/neutron/plugins/ml2/ml2_conf.ini /etc/neutron/plugin.ini

logInfo "sync db ..."
docker exec -it neutron-server neutron-db-manage \
    --config-file /etc/neutron/neutron.conf \
    --config-file /etc/neutron/plugins/ml2/ml2_conf.ini upgrade head
