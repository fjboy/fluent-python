# FPDockStack


```
[dockerfile]
mariadb = Dockerfile_centos7_mariadb
rabbitmq = Dockerfile_centos7_rabbitmq
memcached = Dockerfile_centos7_mariadb
```

## Usage

1. update hosts file first
2. run: ``` python3 fp_stack_docker/dockerstack.py install glance-api -d -v```
3. run: ``` python3 fp_stack_docker/dockerstack.py install glance-api -d -v --config```
3. run: ``` python3 fp_stack_docker/dockerstack.py stop glance-api```
3. run: ``` python3 fp_stack_docker/dockerstack.py stat glance-api```


Docker build issues:

1. issue1  cgroups: cannot find cgroup mount destination: unknown
   solution, run cmd:
   ```
   mkdir /sys/fs/cgroup/systemd
   mount -t cgroup -o none,name=systemd cgroup /sys/fs/cgroup/system
   ```

```

fpdockstack install xxx


