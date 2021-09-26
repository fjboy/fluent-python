. ../docker_openrc.sh
. ../resource/functions.sh

docker container exists neutron-dhcp-agent
if [[ $? -ne 0 ]]; then
    mkdir /var/log/neutron && chmod 777 /var/log/neutron
    docker run -itd \
        --privileged=true \
        -v /sys/fs/cgroup:/sys/fs/cgroup \
        -v /var/log/neutron:/var/log/neutron \
        -v /etc/localtime:/etc/localtime:ro \
        -v /etc/hosts:/etc/hosts:ro \
        --network host \
        --name neutron-dhcp-agent \
        $(getDockerBuildTarget neutron-dhcp-agent)
fi

