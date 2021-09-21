
readonly target=bclinux/memcached

PORT="11211"
USER="memcached"
MAXCONN="20000"
CACHESIZE="20480"
OPTIONS="-l $(hostname -i)"

docker run -itd \
    --privileged=true \
    -v /sys/fs/cgroup:/sys/fs/cgroup \
    -v /etc/hosts:/etc/hosts \
    --network host \
    --name memcached \
    ${target} \
    -p ${PORT} -u ${USER} -m ${CACHESIZE} -c ${MAXCONN} ${OPTIONS}
