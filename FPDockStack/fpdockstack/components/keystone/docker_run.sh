source ../docker_openrc.sh
. ../resource/functions.sh

image="$(getDockerBuildTarget keystone)"

mkdir /var/log/httpd /var/log/keystone /etc/keystone
docker run -itd \
    --privileged \
    -v /etc/hosts:/etc/hosts \
    -v /var/log/keystone:/var/log/keystone \
    -v /var/log/httpd:/var/log/httpd \
    -v /sys/fs/cgroup:/sys/fs/cgroup \
    --network host \
    --name keystone \
    ${image}
