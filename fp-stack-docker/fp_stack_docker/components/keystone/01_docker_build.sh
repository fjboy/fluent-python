. ../docker_openrc.sh
. ../resource/functions.sh

copyResourcesToHere

docker build -t $(getDockerBuildTarget keystone) -f ${DOCKER_FILE} ./
