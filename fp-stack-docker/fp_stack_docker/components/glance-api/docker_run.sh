source ../docker_openrc.sh
. ../resource/functions.sh


docker exec -it mariadb mysql -uroot -proot123 -e "create database IF NOT EXISTS glance;"
docker exec -it mariadb mysql -uroot -proot123 -e "grant all privileges on glance.* to 'glance'@'localhost' identified by 'glance123' with grant option;"
docker exec -it mariadb mysql -uroot -proot123 -e "grant all privileges on glance.* to 'glance'@'%' identified by 'glance123' with grant option;"



source admin_openrc.sh
openstack user create glance --password ${GLANCE_AUTH_PASSWORD}
openstack role add --project service --user ${GLANCE_AUTH_USER} admin

logInfo "add glance endpoint ..."

openstack service create --name glance --description 'OpenStack Image service' image
openstack endpoint create --region RegionOne image public http://${GLANCE_HOST}:9292
openstack endpoint create --region RegionOne image internal http://${GLANCE_HOST}:9292
openstack endpoint create --region RegionOne image admin http://${GLANCE_HOST}:9292




if [[ $? -ne 0 ]];then
    logError "add glance endpoint failed"
    exit 1
fi

target=bclinux/glance



mkdir -p /var/log/glance
mkdir -p /var/lib/glance/images && chmod 777 -R /var/lib/glance
docker run -itd \
    --privileged=true \
    -v /etc/hosts:/etc/hosts \
    -v /sys/fs/cgroup:/sys/fs/cgroup \
    -v /var/log/glance:/var/log/glance \
    -v /var/lib/glance/images:/var/lib/glance/images \
    --network host \
    --name glance \
    ${target}

