
echoFile(){
    local file=$1
    echo "===== $file ====="
    cat $file
}

init(){
   echo "INFO" "init rabbitmq"
   mkdir -p /etc/rabbitmq
   echo "RABBITMQ_NODE_IP_ADDRESS='$(hostname -i)'" > /etc/rabbitmq/rabbitmq-env.conf

   mkdir -p /etc/systemd/system/rabbitmq-server.service.d
   echo "
[Service]
LimitNOFILE = 100000
" > /etc/systemd/system/rabbitmq-server.service.d/limit.conf

   cp /etc/rabbitmq/rabbitmq.config /etc/rabbitmq/rabbitmq.config.backup
   echo '
% Template Path: rabbitmq/templates/rabbitmq.config
[
 {kernel,[
  {inet_dist_listen_min, 41055},
  {inet_dist_listen_max, 41055},
  {inet_default_connect_options, [{nodelay,true}]} ]},
 {rabbit,[
  {cluster_partition_handling, autoheal},
  {tcp_listen_options, [
binary,
   {packet, raw},
   {reuseaddr, true},
   {backlog, 4096},
   {nodelay, true},
   {exit_on_close, false},
   {keepalive, true}
  ]}
 ]},
 {rabbitmq_management,[
  {http_log_dir,"/tmp/rabbit-mgmt"},
  {rates_mode,none}
 ]}
].
% EOF
' > /etc/rabbitmq/rabbitmq.config

   echoFile /etc/rabbitmq/rabbitmq-env.conf
   echoFile /etc/systemd/system/rabbitmq-server.service.d/limit.conf
   echoFile /etc/rabbitmq/rabbitmq.config
}

main(){
   local action=$1
   if [[ -z ${action} ]]; then
      echo "Usage: $0 <init> "
      exit 1
   fi
   shift
   ${action} $@
}


main $@
