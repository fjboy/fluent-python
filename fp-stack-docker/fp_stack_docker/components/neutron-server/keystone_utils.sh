#!/usr/bin/env bash

set -u

initDatabase(){
    local rootPassword=$1
    local keystonePassword=$2
    mysql -p${rootPassword} -e "create database IF NOT EXISTS keystone;" |exit 1
    for name in $(hostname) '%'
    do
        mysql -p${rootPassword} -e "grant all privileges on keystone.* to 'keystone'@'${name}' identified by '${keystonePassword}' with grant option;" || exit 1
    done
    mysql -p${rootPassword} -e "FLUSH PRIVILEGES;" |exit 1

    echo "INFO: init keystone database success"
}

initConfig(){
    local dbHost=$1
    local dbPassword=$2
    local memcacheServers=$3
    local confPath=/etc/keystone/keystone.conf

    openstack-config --set ${confPath} DEFAULT debug true
    openstack-config --set ${confPath} DEFAULT log_dir /var/log/keystone

    openstack-config --set ${confPath} database connection mysql+pymysql://keystone:${dbPassword}@${dbHost}/keystone

    openstack-config --set ${confPath} cache memcache_servers "${memcacheServers}"
    openstack-config --set ${confPath} cache backend oslo_cache.memcache_pool
    openstack-config --set ${confPath} cache enabled true

    openstack-config --set ${confPath} token expiration 7000
    openstack-config --set ${confPath} token provider fernet
    openstack-config --set ${confPath} token allow_expire true
}

syncDB(){
    su -s /bin/sh -c "keystone-manage db_sync" keystone
}


initService(){
    local keystoneHost=$1
    local keystonePassword=$2
    keystone-manage bootstrap --bootstrap-password ${keystonePassword} \
        --bootstrap-admin-url http://${keystoneHost}:35357/v3/ \
        --bootstrap-internal-url http://${keystoneHost}:35357/v3/ \
        --bootstrap-public-url http://${keystoneHost}:5000/v3/ \
        --bootstrap-region-id RegionOne
}

main(){
    local func=$1
    shift
    ${func} $@
}

main $@
