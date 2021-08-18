# ToolKitsLight
some simple tools 

## FPUtils 工具

- [X] md5sum 计算器
- [X] 二维码生成/识别器
- [X] 时间转换器
- [X] 随机密码生成器
- [X] 壁纸下载器-bingimg
- [ ] 端口扫描
- [ ] 批量文件同步工具


### 1.批量执行命令和拷贝文件

把远程主机信息保存到文件中，例如：
```
root@LAPTOP-BFO405GC:~# cat hosts.txt
root@197.168.137.100 password=root123
root@controller      password=root123
```
批量执行命令
```
root@LAPTOP-BFO405GC:~# fp-utils ssh-cmd hosts.txt pwd
2021-06-13 22:54:31,794 INFO fluentclient.fluentcore.sshpass:135 run cmd on 2 hosts, worker is 2
===== 197.168.137.100 =====
/root
===== controller =====
/root
2021-06-13 22:54:35,065 INFO fluentclient.fluentcore.sshpass:106 Spend 3.27 seconds total
```

批量拷贝文件到远程主机的 `/tmp` 目录
```
root@LAPTOP-BFO405GC:~# fp-utils scp-put hello.jpg hosts.txt --remote /tmp/
2021-06-13 23:13:40,255 INFO fluentclient.commands.sshpass:172 upload to 2 hosts, worker is 2
===== 197.168.137.100 =====
success
===== controller =====
success
2021-06-13 23:13:42,082 INFO fluentclient.commands.sshpass:106 Spend 1.83 seconds total
```
结果
```
root@LAPTOP-BFO405GC:~# fluent-utils ssh-cmd hosts.txt 'ls -l /tmp/*.jpg'
2021-06-13 23:16:09,591 INFO fluentclient.commands.sshpass:134 run cmd on 2 hosts, worker is 2
===== 197.168.137.100 =====
-rw-r--r--. 1 root root 334 Jun 13 23:13 /tmp/hello.jpg
===== controller =====
-rw-r--r--. 1 root root 334 Jun 13 23:13 /tmp/hello.jpg
2021-06-13 23:16:12,889 INFO fluentclient.commands.sshpass:106 Spend 3.30 seconds total
```
从远程主机下载文件

例如，从远程主机下载文件`/tmp/hello.jpg`，并保存到`remote_files`目录：
```
root@LAPTOP-BFO405GC:~# fp-utils scp-get hosts.txt --remote /tmp/hello.jpg  --local remote_files
2021-06-13 23:37:52,604 INFO fluentclient.commands.sshpass:154 download files from 2 hosts, worker is 2
===== 197.168.137.100 =====
success
===== controller =====
success
2021-06-13 23:38:01,969 INFO fluentclient.commands.sshpass:106 Spend 9.36 seconds total
```
结果
```
root@LAPTOP-BFO405GC:~# ll remote_files/*/*.jpg
-rw-r--r-- 1 root root 334 Jun 13 23:38 remote_files/197.168.137.100/hello.jpg
-rw-r--r-- 1 root root 334 Jun 13 23:37 remote_files/controller/hello.jpg
```

## 2. 二维码

二维码生成、解析

例如，生成字符串“hello word!”的二维码
```
root@LAPTOP-BFO405GC:~# fp-utils-ext qrcode-parse 'hello word!'
█▀▀▀▀▀█ ▀█▄▄▀ █▀▀▀▀▀█
█ ███ █ ▀█ ▄█ █ ███ █
█ ▀▀▀ █ ▄█▄██ █ ▀▀▀ █
▀▀▀▀▀▀▀ ▀ ▀ █ ▀▀▀▀▀▀▀
█ █ ▄▄▀▀▄▀ ▄ ▄▄▀▄▄▀ █
▄▄█▄▄▄▀▄▀▀▀█▀▄ ▄█▄▀ ▀
▀▀ ▀▀ ▀▀█▄▀▀▀  ▄██▄▀▄
█▀▀▀▀▀█ ▀█▄ ▄█  ▀█▀▄█
█ ███ █  █▀  █ ▀██▄▀
█ ▀▀▀ █ ▀▀▄█▀▀▀███▀▀▀
▀▀▀▀▀▀▀ ▀ ▀▀▀▀   ▀  ▀
```
默认输出字符串格式的二维码，使用`-o`选项保存为图片
```
root@LAPTOP-BFO405GC:~# fluent-utils qrcode-parse 'hello word!' -o hello.jpg 
root@LAPTOP-BFO405GC:~# ll hello.jpg 
-rw-r--r-- 1 root root 334 Jun 13 22:01 hello.jpg
```
解析二维码

```
root@LAPTOP-BFO405GC:~# fp-utils-ext qrcode-dump hello.jpg 
hello word!
```

## 3. 文件反向读取

反向读取文件

例如，
```
root@LAPTOP-BFO405GC:~# echo -e "hello\nword" > test.txt
root@LAPTOP-BFO405GC:~# cat test.txt 
hello
word
root@LAPTOP-BFO405GC:~# fluent-utils print-backwards test.txt 
word
hello
```
>默认输出文件的所有反向内容  
>`-o` 指定读取的行数*  
>`-c` 设置读取的缓存大小


## FPHttpFS 简单文件服务器

支持文件上传，下载，二维码扫描下载等功能

![image](https://user-images.githubusercontent.com/16282152/114277052-167ea780-9a5c-11eb-9112-c2fd6aaf2fde.png)
