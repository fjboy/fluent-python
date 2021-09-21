. ../docker_openrc.sh
. ../resource/functions.sh

copyResourcesToHere

checkEnv || exit 1

docker build -t $(getDockerBuildTarget neutron-ovs-agent) -f ${DOCKER_FILE}  ./

cleanUpBuild
