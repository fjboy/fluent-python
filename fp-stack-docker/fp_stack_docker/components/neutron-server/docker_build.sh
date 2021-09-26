. ../docker_openrc.sh
. ../resource/functions.sh

copyResourcesToHere

dockerFile=$(getDockerfile) ||exit 1

docker build -t $(getDockerBuildTarget neutron-server) -f ${dockerFile}  ./
cleanUpBuild
