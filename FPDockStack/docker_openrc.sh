[docker]
build_file = Dockfile
build_target = zbw/centos7
build_yum_repo = centos7-163.repo

# build with centos7
export DOCKER_FILE=Dockerfile
export DOCKER_BUILD_TARGET=zbw/centos7
export DOCKER_BUILD_YUM_REPO=centos7-163.repo

export MARIADB_SERVER=mariadb-server1:11211
