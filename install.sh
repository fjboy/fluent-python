
function logInfo(){
    echo `date +'%F %T'` "INFO:" $@
}

function logError(){
    echo `date +'%F %T'` "ERROR:" $@
}

function cleanUp(){
    rm -rf ./build  ./dist ./*.egg-info
    rm -rf AUTHORS ChangeLog
}

COMPONENT=$1
if [[ -z "${COMPONENT}" ]]; then
    install_computents=(FPLib FPUtils FPHttpFS)
else
    install_computents=($1)
fi

osType=''
grep -i ubuntu /etc/os-release > /dev/null
if [[ $? -eq 0 ]]; then
    osType="ubuntu"
else
    grep -i centos /etc/os-release > /dev/null
    if [[ $? -eq 0 ]]; then
        osType="centos"
    fi
fi

if [[ -z "${osType}" ]]; then
    logError "OS is unknown"
    exit 1
fi

logInfo "OS is ${osType}"
logInfo "install python-dev if not exists"
case ${osType} in
    ubuntu)
	apt-cache show python-dev > /dev/null
    [ $? -ne 0 ] && sudo apt-get install python-dev 
    [ $? -ne 0 ] || exit 1

    apt-cache show python-zbar  > /dev/null
    [ $? -ne 0 ] && sudo apt-get install python-zbar
    [ $? -ne 0 ] || exit 1
    ;;
    centos)
        rpm -qa python-devel > /dev/null || yum install -y python-devel || yum install python-zbar || exit 1
        ;;
    *)
        ;;
esac

logInfo "install components: ${install_computents[*]}"
for component in ${install_computents[*]}
do
    cd ${component} 2> /dev/null
    if [[ $? -ne 0 ]]; then
        logError "component ${component} not exists."
        continue
    fi
    if [[ -f requirements.txt ]]; then
        logInfo "$component install requirements ..."
        pip3 install -r requirements.txt
    fi
    logInfo "$component make package ..."
    rm -rf dist
    python3 setup.py sdist > /dev/null || exit 1

    logInfo "$component install package ..."
    pip3 install dist/*.tar.gz --force-reinstall > /dev/null
    if [[ $? -eq 0 ]]; then
	    logInfo "$component install success"
    else
        logError "$component install failed"
    fi
    logInfo "$component clean up ..."
    cleanUp
    cd ../
done
