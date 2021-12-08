OPENSTACK_HOST=$1
LOCAL_SETTINGS=/etc/openstack-dashboard/local_settings

if [[ "${OPENSTACK_HOST}" != "" ]];then
    sed -i "s|^OPENSTACK_HOST.*|OPENSTACK_HOST = \"${OPENSTACK_HOST}\"|g" "${LOCAL_SETTINGS}"
    shift
fi

exec httpd -DFOREGROUND "$@"
