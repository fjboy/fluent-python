. ../docker_openrc.sh
. ../resource/functions.sh

copyResourcesToHere

dockerFile=$(getDockerfile) ||exit 1

docker build -t $(getDockerBuildTarget memcached) -f ${dockerFile}  ./
