sudo mount -o remount,rw '/sys/fs/cgroup'
sudo  ln -s /sys/fs/cgroup/cpu,cpuacct /sys/fs/cgroup/cpuacct,cpu

docker run \
    --volume=/:/rootfs:ro --volume=/var/run:/var/run:rw \
    --volume=/sys:/sys:ro \
    --volume=/var/lib/docker/:/var/lib/docker:ro \
    --detach=true --privileged=true \
    --restart=always \
    --name=cadvisor --publish=8081:8080 \
    google/cadvisor:latest
