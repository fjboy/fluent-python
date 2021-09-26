source ../docker_openrc.sh
. ../resource/functions.sh

mkdir /var/log/neutron && chmod 777 /var/log/neutron
docker run -itd \
    --privileged=true \
    -v /etc/hosts:/etc/hosts \
    -v /sys/fs/cgroup:/sys/fs/cgroup \
    -v /var/log/neutron:/var/log/neutron \
    --network host \
    --name neutron-server \
    $(getDockerBuildTarget neutron-server)
    ${image}
