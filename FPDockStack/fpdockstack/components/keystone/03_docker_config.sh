source ../docker_openrc.sh
. ../resource/functions.sh

logInfo "Install openstack-utils ..."
docker exec -it keystone yum install -y openstack-utils

# config
docker exec -it keystone openstack-config --set ${KEYSTONE_CONF} DEFAULT debug true
docker exec -it keystone openstack-config --set ${KEYSTONE_CONF} DEFAULT log_dir /var/log/keystone

docker exec -it keystone openstack-config --set ${KEYSTONE_CONF} database connection mysql+pymysql://keystone:${KEYSTONE_DB_PASSWORD}@${KEYSTONE_HOST}/keystone

docker exec -it keystone openstack-config --set ${KEYSTONE_CONF} cache memcache_servers "${MEMCACHED_SERVERS}"
docker exec -it keystone openstack-config --set ${KEYSTONE_CONF} cache backend oslo_cache.memcache_pool
docker exec -it keystone openstack-config --set ${KEYSTONE_CONF} cache enabled true

docker exec -it keystone openstack-config --set ${KEYSTONE_CONF} token expiration 7000
docker exec -it keystone openstack-config --set ${KEYSTONE_CONF} token provider fernet
docker exec -it keystone openstack-config --set ${KEYSTONE_CONF} token allow_expire true

logInfo "keystone-manage db_sync ..."
# sync db
docker exec -it keystone su -s /bin/sh -c "keystone-manage db_sync" keystone

logInfo "bootstrap ..."
# init bootstrap
docker exec -it keystone keystone-manage bootstrap \
    --bootstrap-password ${ADMIN_PASSWORD} \
    --bootstrap-admin-url http://${KEYSTONE_HOST}:35357/v3/ \
    --bootstrap-internal-url http://${KEYSTONE_HOST}:35357/v3/ \
    --bootstrap-public-url http://${KEYSTONE_HOST}:5000/v3/ \
    --bootstrap-region-id RegionOne

# docker exec -it keystone systemctl restart httpd

openstack project create --domain default --description "Service Project" service


openstack project create --domain default --description "Demo Project" demo
openstack user create --domain default --password demo123 demo
openstack role create user
openstack role add --project demo --user demo user