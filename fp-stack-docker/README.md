# FPDockStack


```
[dockerfile]
mariadb = Dockerfile_centos7_mariadb
rabbitmq = Dockerfile_centos7_rabbitmq
memcached = Dockerfile_centos7_mariadb

```

Docker build issues:

1. issue1  cgroups: cannot find cgroup mount destination: unknown
   solution, run cmd:
   ```
   mkdir /sys/fs/cgroup/systemd
   mount -t cgroup -o none,name=systemd cgroup /sys/fs/cgroup/system
   ```

```

fpdockstack install xxx


