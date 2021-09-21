
grant all privileges on *.* to 'root'@'localhost' identified by 'root123' with grant option;
grant all privileges on *.* to 'root'@'%' identified by 'root123' with grant option;


grant all privileges on *.* to 'root'@'controller60' identified by 'root123';


CREATE DATABASE IF NOT EXISTS keystone DEFAULT CHARACTER SET utf8;
GRANT ALL PRIVILEGES ON keystone.* TO 'keystone'@'localhost' IDENTIFIED BY 'keystone123' with grant option;
GRANT ALL PRIVILEGES ON keystone.* TO 'keystone'@'%' IDENTIFIED BY 'keystone123' with grant option;

FLUSH privileges;

create database IF NOT EXISTS cinder;



create database IF NOT EXISTS glance;
grant all privileges on glance.* to 'glance'@'localhost' identified by 'glance123' with grant option;
grant all privileges on glance.* to 'glance'@'%' identified by 'glance123' with grant option;


create database IF NOT EXISTS nova_api DEFAULT CHARACTER SET utf8;
create database IF NOT EXISTS nova DEFAULT CHARACTER SET utf8;


grant all privileges on nova.* to 'nova'@'%' identified by 'nova123' with grant option;
grant all privileges on nova.* to 'nova'@'localhost' identified by 'nova123' with grant option;

grant all privileges on nova_api.* to 'nova'@'%' identified by 'nova123' with grant option;
grant all privileges on nova_api.* to 'nova'@'localhost' identified by 'nova123' with grant option;

grant all privileges on nova_cell0.* to 'nova'@'%' identified by 'nova123' with grant option;
grant all privileges on nova_cell0.* to 'nova'@'localhost' identified by 'nova123' with grant option;


create database IF NOT EXISTS cinder DEFAULT CHARACTER SET utf8;
grant all privileges on cinder.* to 'cinder'@'%' identified by 'cinder123' with grant option;
grant all privileges on cinder.* to 'cinder'@'controller60' identified by 'cinder123' with grant option;



create database IF NOT EXISTS neutron2;
grant all privileges on neutron2.* to 'neutron'@'localhost' identified by 'neutron123' with grant option;
grant all privileges on neutron2.* to 'neutron'@'%' identified by 'neutron123' with grant option;




FLUSH privileges;
