target=bclinux/ironic

mkdir -p /var/log/ironic
docker run -itd \
    --privileged=true \
    -v /etc/hosts:/etc/hosts \
    -v /sys/fs/cgroup:/sys/fs/cgroup \
    -v /var/log/ironic:/var/log/ironic \
    --network host \
    --name glance \
    ${target}
