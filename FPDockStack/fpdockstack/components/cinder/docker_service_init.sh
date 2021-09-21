source ../docker_openrc.sh
. ../resource/functions.sh

docker exec -it mariadb mysql -uroot -proot123 -e "create database IF NOT EXISTS cinder;";
docker exec -it mariadb mysql -uroot -proot123 -e "grant all privileges on cinder.* to 'cinder'@'localhost' identified by 'cinder123' with grant option;";
docker exec -it mariadb mysql -uroot -proot123 -e "grant all privileges on cinder.* to 'cinder'@'%' identified by 'cinder123' with grant option;";


export CINDER_HOST=ebm-vm-host-2
export CINDER_AUTH_USER=cinder
export CINDER_AUTH_PASSWORD=cinder123


source /home/zbw/admin_openrc.sh

openstack user create cinder --password ${CINDER_AUTH_PASSWORD}
openstack role add --project service --user ${CINDER_AUTH_USER} admin

openstack service create --name cinderv2 --description 'OpenStack Block Storage' volumev2
openstack endpoint create --region RegionOne volumev2 public http://${CINDER_HOST}:8776/v2/%\(project_id\)s
openstack endpoint create --region RegionOne volumev2 internal http://${CINDER_HOST}:8776/v2/%\(project_id\)s
openstack endpoint create --region RegionOne volumev2 admin http://${CINDER_HOST}:8776/v2/%\(project_id\)s

openstack service create --name cinderv3 --description 'OpenStack Block Storage' volumev3
openstack endpoint create --region RegionOne volumev3 public http://${CINDER_HOST}:8776/v3/%\(project_id\)s
openstack endpoint create --region RegionOne volumev3 internal http://${CINDER_HOST}:8776/v3/%\(project_id\)s
openstack endpoint create --region RegionOne volumev3 admin http://${CINDER_HOST}:8776/v3/%\(project_id\)s
