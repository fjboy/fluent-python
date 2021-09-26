source ../docker_openrc.sh
. ../resource/functions.sh

image="$(getDockerBuildTarget keystone)"

mkdir /var/log/httpd /var/log/keystone

docker run -itd \
    --privileged=true \
    -v /etc/hosts:/etc/hosts \
    -v /var/log/keystone:/var/log/keystone \
    -v /var/log/httpd:/var/log/httpd \
    -v /sys/fs/cgroup:/sys/fs/cgroup \
    --network host \
    --name keystone \
    ${image}
