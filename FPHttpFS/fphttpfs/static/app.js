
var app = new Vue({
    el: '#app',
    data: {
        children: [],
        downloadFile: {name: '', qrcode: '' },
        showAll: false,
        fsClient: new HttpFSClient(),
        renameItem: { name: '', newName: '' },
        newDir: { name: '', validate: null },
        fileEditor: { name: '', content: '' },
        uploadQueue: { completed: 0, tasks: [] },
        debug: false,
        pathItems: [],
        diskUsage: {used: 0, total: 100},
        searchPartern: '',
        searchResult: [],
        showPardir: false,
        currentDirList: [],
        log: null,
        searchHistory: []
    },
    methods: {
        refreshChildren: function () {
            this.log.debug('更新目录');
            this.goTo(this.pathItems.length - 1);
        },
        getAbsPath: function (child) {
            if (absPath == '/') {
                absPath += child.name;
            } else {
                absPath += '/' + child.name;
            }
            return absPath;
        },
        clickPath: function (child) {
            if (child.type != "folder") {
                return
            }
            var self = this;
            let pathItems = self.getPathText(self.pathItems).concat(child.name);

            this.fsClient.listDir(
                pathItems, self.showAll,
                function (status, data) {
                    if (status == 200) {
                        self.currentDirList.push(child.name);
                        self.pathItems.push({text: child.name, href: '#' })
                        self.children = data.dir.children;
                        self.diskUsage = data.dir.disk_usage;
                    } else {
                        self.log.error(`请求失败，${status}, ${data.error}`);
                    }
                }
            );
        },
        getPathText: function(pathItems){
            let pathText = [];
            pathItems.forEach(function(item) {
                pathText.push(item.text);
            });
            return pathText;
        },
        getDirPath: function(dirItems){
            return dirItems.join('/')
        },
        getCurrentPath: function(){
            return this.getDirPath(this.pathItems);
        },
        getFSPath: function(dirName){
            let currentDir = this.currentDirList.concat(dirName);
            return this.getDirPath(currentDir)
        },
        getFSUrl: function(dirItem){
            if (dirItem.pardir){
                return this.fsClient.getFsUrl(`${dirItem.pardir}/${dirItem.name}`);
            }else{
                return this.fsClient.getFsUrl(this.getFSPath(dirItem.name));
            }
        },
        getDownloadUrl: function(dirItem){
            if (dirItem.pardir){
                return this.fsClient.getDownloadUrl(`${dirItem.pardir}/${dirItem.name}`);
            }else{
                return this.fsClient.getDownloadUrl(this.getFSPath(dirItem.name));
            }
        },
        goTo: function(clickIndex) {
            var self = this;
            self.showPardir = false;
            let pathItems = self.getPathText(getItemsBefore(self.pathItems, clickIndex));
            this.fsClient.listDir(
                pathItems, self.showAll,
                function (status, data) {
                    if (status == 200) {
                        delItemsAfter(self.currentDirList, clickIndex);
                        delItemsAfter(self.pathItems, clickIndex);
                        self.children = data.dir.children;
                        self.diskUsage = data.dir.disk_usage;
                    } else {
                        self.log.error(`请求失败，${status}, ${data.error}`);
                    }
                }
            );
        },
        setFileQrcode: function(dirItem){
            this.downloadFile = dirItem;
        },
        showFileQrcode: function () {
            let filePath = null;
            if (this.downloadFile.pardir){
                filePath = `${this.downloadFile.pardir}/${this.downloadFile.name}`;
            }else{
                filePath = this.getFSPath(this.downloadFile.name);
            }
            this.showQrcode('fileQrcode', this.fsClient.getFSLink(filePath))
        },
        makeSureDelete: function(item){
            var self = this;
            this.$bvModal.msgBoxConfirm(item.name, {
                title: translate('makeSureDelete'),
                okVariant: 'danger',
            }).then(value => {
                self.log.debug(`make sure delete? ${value}`)
                if(value == true){
                    self.deleteDir(item);
                    self.refreshChildren();
                }
            });
        },
        deleteDir: function (item) {
            var self = this;
            this.fsClient.deleteDir(
                this.getPathText(self.pathItems).concat([item.name]),
                function (status, data) {
                    if (status == 200) {
                        self.log.info('删除成功');
                    } else {
                        self.log.error(`删除失败, ${status}, ${data.error}`);
                    }
                },
                function () {
                    self.log.error('请求失败');
                }
            );
        },
        toggleShowAll: function () {
            this.showAll = !this.showAll;
            this.refreshChildren();
        },
        renameDir: function () {
            var self = this;
            if (self.renameItem.name == self.renameItem.newName) {
                return;
            }
            if (self.renameItem.newName == '') {
                self.log.error('文件名不能为空');
                return;
            }
            this.fsClient.fsRename(
                self.getFSPath(self.renameItem.name), self.renameItem.newName, {
                onload_callback: function (status, data) {
                    if (status == 200) {
                        self.log.info('重命名成功');
                        self.refreshChildren();
                    } else {
                        self.log.error(`重命名失败, ${data.error}`, autoHideDelay = 5000)
                    }
                },
                onerror_callback: function () { self.log.error('请求失败') }
            });
        },
        showRenameModal: function (item) {
            this.renameItem = { name: item.name, newName: item.name }
        },
        createDir: function () {
            var self = this;
            if (this.newDir.name == '') {
                this.log.error(translate('dirNameNull'))
                return;
            }
            if (! this.newDir.validate) {
                this.log.error(translate('invalidChar'))
                return;
            }
            var self = this;
            let newDir = self.getDirPath(self.currentDirList.concat(self.newDir.name));
            self.fsClient.fsCreate(newDir, {
                onload_callback: function (status, data) {
                    if (status == 200) {
                        self.log.info('目录创建成功');
                        self.refreshChildren();
                    } else {
                        self.log.error(`目录创建失败, ${status}, ${data.error}`, autoHideDelay=5000)
                    }
                    self.newDir = { name: '' }
                },
                onerror_callback: function () {
                    self.log.error('请求失败');
                }
            });
        },
        uploadFiles: function (files) {
            var self = this;
            if (files.length == 0) { return };
            self.log.info(`准备上传 ${files.length} 个文件`);
            for (let index = 0; index < files.length; index++) {
                const file = files[index];
                const progress = { file: file.name, loaded: 0, total: 100 };
                self.uploadQueue.tasks.push(progress);

                self.fsClient.uploadFile(
                    self.getPathText(self.pathItems), file,
                    function (status, data) {
                        if (status != 200) {
                            self.log.error(`文件上传失败, ${status}, ${data.error}`, autoHideDelay = 5000)
                        }else{
                            self.refreshChildren()
                            self.uploadQueue.completed += 1;
                        }
                    },
                    function () { self.log.error('请求失败') },
                    function (loaded, total) {
                        progress.loaded = loaded;
                        progress.total = total;
                    }
                )
            }
        },
        uploadFile: function () {
            var form = document.forms["formFileUpload"];
            this.uploadFiles(form.inputUploadFile.files);
        },
        uploadDir: function () {
            var form = document.forms["formDirUpload"];
            this.uploadFiles(form.inputUploadDir.files);
        },
        showFileModal: function (item) {
            this.fileEditor.name = item.name;
            var self = this;
            self.fsClient.fsGet(self.getFSPath(item.name), false, {
                onload_callback: function (status, data) {
                    if (status == 200) {
                        self.fileEditor.content = data;
                    } else {
                        self.log.error(`文件内容获取失败, ${status}, ${data.error}`, autoHideDelay = 5000)
                    }
                },
                onerror_callback: function () {
                    self.log.error('请求失败');
                },
            });
        },
        updateFile: function () {
            this.log.error('文件修改功能未实现');
        },
        getDiskUsage: function(){
            let ONE_KB = 1024;
            let ONE_MB = ONE_KB * 1024;
            let ONE_GB = ONE_MB * 1024;
            let displayUsed = this.diskUsage.used;
            let displayTotal = this.diskUsage.total;
            let unit = 'B'
            if (this.diskUsage.total >= ONE_GB){
                displayUsed = this.diskUsage.used / ONE_GB;
                displayTotal = this.diskUsage.total / ONE_GB;
                unit = 'GB';
            } else if (this.diskUsage.total >= ONE_MB){
                displayUsed = this.diskUsage.used / ONE_MB;
                displayTotal = this.diskUsage.total / ONE_MB;
                unit = 'MB';
            } else if (this.diskUsage.total >= ONE_KB){
                displayUsed = this.diskUsage.used / ONE_KB;
                displayTotal = this.diskUsage.total / ONE_KB;
                unit = 'KB';
            }
            return `${displayUsed.toFixed(2)}${unit}/${displayTotal.toFixed(2)}${unit}`;
        },
        refreshSearchHistory: function(){
            var self = this
            this.fsClient.getSearchHistory({
                onload_callback: function(status, data){
                    if (status != 200){
                        self.log.error('get search history failed');
                    }
                    self.searchHistory = data.search.history;
                }
            });
        },
        search: function(){
            if(this.searchPartern == ''){return;}
            var self = this;
            self.showPardir = true;
            self.searchResult = [];
            this.fsClient.searchPost(
                this.searchPartern, {
                    onload_callback: function (status, data) {
                        if (status == 200) {
                            self.children = data.search.dirs;
                        } else {
                            self.log.error(`搜索失败, ${status}, ${data.error}`, autoHideDelay = 5000)
                        }
                    },
                    onerror_callback: function () { self.log.error('请求失败') }
                }
            )
        },
        showQrcode: function(elemId, text){
            // chinese is not support for qrcode.js now
            console.debug(`make code: ${text}`)
            var qrcode = new QRCode(elemId);
            qrcode.makeCode(text);
        },
        refreshConnectionLink: function(){
            this.showQrcode('connectionLink2', window.location.href)
        },
        checkIsDirInvalid: function(){
            let invalidChar = this.newDir.name.search(/[!@#$%^&*():";'<>?,.~]/i);
            if(invalidChar >= 0){
                this.newDir.validate = false;
            }else{
                this.newDir.validate = true;
            }
        },
        refreshDir: function(){
            var self = this;
            this.fsClient.fsGet(
                this.currentDirList.join('/'), self.showAll, {
                    onload_callback: function (status, data) {
                        if (status == 200) {
                            self.children = data.dir.children;
                            self.diskUsage = data.dir.disk_usage;
                        } else {
                            self.log.error(`请求失败，${status}, ${data.error}`);
                        }
                    }
                }
            );
        }
    },
    created: function () {
        this.log = new LoggerWithBVToast(this.$bvToast, debug=false)
        this.log.debug('vue app created');
        this.goTo(-1);
    },
});
