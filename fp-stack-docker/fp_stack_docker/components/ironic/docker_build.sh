. ../docker_openrc.sh
. ../resource/functions.sh

copyResourcesToHere

docker build -t $(getDockerBuildTarget ironic) -f $(getDockerfile) ./



# export IRONIC_ADMINPASS=ironic123
# openstack user create --password ${IRONIC_ADMINPASS} ironic
# openstack role add --project service --user ${IRONIC_AUTH_USER} admin
# openstack service create --name ironic --description "Ironic baremetal provisioning service" baremetal
# openstack endpoint create --region RegionOne baremetal public http://ironic-ha-vip:6385 
# openstack endpoint create --region RegionOne baremetal internal http://ironic-ha-vip:6385
# openstack endpoint create --region RegionOne baremetal admin http://ironic-ha-vip:6385
