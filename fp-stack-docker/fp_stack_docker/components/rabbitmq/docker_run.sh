. ../docker_openrc.sh
. ../resource/functions.sh

image=$(getDockerBuildTarget rabbitmq)

logInfo "use image ${image}"
mkdir -p /var/log/rabbitmq && chmod 777 /var/log/rabbitmq

docker run -itd \
    --privileged \
    --network ${DOCKER_RUN_NETWORK} \
    -v /etc/hosts:/etc/hosts \
    -v /var/log/rabbitmq:/var/log/rabbitmq \
    --name rabbitmq \
    ${image}

docker exec -it rabbitmq sh /entrypoint.sh init
sleep 1
docker exec -it rabbitmq rabbitmqctl add_user openstack rabbitmq123
sleep 1
docker exec -it rabbitmq rabbitmqctl set_permissions -p / openstack '.*' '.*' '.*'
sleep 1
docker exec -it rabbitmq rabbitmqctl set_user_tags openstack administrator
sleep 1
docker restart rabbitmq
