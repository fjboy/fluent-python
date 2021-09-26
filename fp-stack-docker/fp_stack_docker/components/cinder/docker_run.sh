. ../resource/functions.sh

source ../docker_openrc.sh


docker cp create_cinder_catalog.sh keystone:/
docker exec -it keystone sh create_cinder_catalog.sh

makeBuildEnv
makeRunEnv

readonly image=bclinux/cinder

mkdir /var/log/cinder && chmod 777 /var/log/cinder
docker run -itd \
    --privileged=true \
    -v /etc/hosts:/etc/hosts \
    -v /sys/fs/cgroup:/sys/fs/cgroup \
    -v /var/log/cinder:/var/log/cinder \
    --network host \
    --name cinder \
    ${image}



# sync db
docker exec -it keystone su -s /bin/sh -c "keystone-manage db_sync" keystone

# init bootstrap
docker exec -it keystone keystone-manage bootstrap \
    --bootstrap-password ${ADMIN_PASSWORD} \
    --bootstrap-admin-url http://${KEYSTONE_HOST}:35357/v3/ \
    --bootstrap-internal-url http://${KEYSTONE_HOST}:35357/v3/ \
    --bootstrap-public-url http://${KEYSTONE_HOST}:5000/v3/ \
    --bootstrap-region-id RegionOne

docker restart keystone


openstack project create --domain default --description "Service Project" service
openstack region create DefaultOp

openstack project create --domain default --description "Demo Project" demo