. ../docker_openrc.sh
. ../resource/functions.sh

copyResourcesToHere

docker build -t $(getDockerBuildTarget rabbitmq) -f $(getDockerfile) ./
