
var app = new Vue({
    el: '#app',
    data: {
        server: {name: '', version: ''},
        children: [],
        historyPath: [],
        linkQrcode: '',
        downloadFile: {name: '', qrcode: '' },
        showAll: false,
        wetoolFS: new WetoolFS(),
        renameItem: { name: '', newName: '' },
        newDir: { name: '' },
        fileEditor: { name: '', content: '' },
        uploadProgess: { loaded: 0, total: 100 },
        uploadQueue: { completed: 0, tasks: [] },
        debug: false,
        pathItems: [],
        diskUsage: {used: 0, total: 100},
        searchPartern: '',
        searchResult: [],
        showPardir: false,
        currentDirList: [],
        newDirNameIsInvalid: true
    },
    methods: {
        logDebug: function (msg, autoHideDelay = 1000, title = 'Debug') {
            if (this.debug == false) {
                return
            }
            this.$bvToast.toast(msg, {
                title: title,
                variant: 'default',
                autoHideDelay: autoHideDelay
            });
        },

        logInfo: function (msg, autoHideDelay = 1000, title = 'Info') {
            this.$bvToast.toast(msg, {
                title: title,
                variant: 'success',
                autoHideDelay: autoHideDelay
            });
        },
        logWarn: function (msg, autoHideDelay = 1000, title = 'Warn') {
            this.$bvToast.toast(msg, {
                title: title,
                variant: 'warning',
                autoHideDelay: autoHideDelay
            });
        },
        logError: function (msg, autoHideDelay = 5000, level = 'Error') {
            this.$bvToast.toast(msg, {
                title: level,
                variant: 'danger',
                autoHideDelay: autoHideDelay
            });
        },
        refreshChildren: function () {
            this.logDebug('更新目录');
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

            this.wetoolFS.listDir(
                pathItems, self.showAll,
                function (status, data) {
                    if (status == 200) {
                        self.currentDirList.push(child.name);
                        self.pathItems.push({text: child.name, href: '#' })
                        self.children = data.dir.children;
                        self.diskUsage = data.dir.disk_usage;
                    } else {
                        self.logError(`请求失败，${status}, ${data.error}`);
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
                return this.wetoolFS.getFsUrl(`${dirItem.pardir}/${dirItem.name}`);
            }else{
                return this.wetoolFS.getFsUrl(this.getFSPath(dirItem.name));
            }
        },
        getDownloadUrl: function(dirItem){
            if (dirItem.pardir){
                return this.wetoolFS.getDownloadUrl(`${dirItem.pardir}/${dirItem.name}`);
            }else{
                return this.wetoolFS.getDownloadUrl(this.getFSPath(dirItem.name));
            }
        },
        goTo: function(clickIndex) {
            var self = this;
            self.showPardir = false;
            let pathItems = self.getPathText(getItemsBefore(self.pathItems, clickIndex));
            this.wetoolFS.listDir(
                pathItems, self.showAll,
                function (status, data) {
                    if (status == 200) {
                        delItemsAfter(self.currentDirList, clickIndex);
                        delItemsAfter(self.pathItems, clickIndex);
                        self.children = data.dir.children;
                        self.diskUsage = data.dir.disk_usage;
                    } else {
                        self.logError(`请求失败，${status}, ${data.error}`);
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
            this.showQrcode('fileQrcode', this.wetoolFS.getFSLink(filePath))
        },
        deleteDir: function (item) {
            var self = this;
            this.wetoolFS.deleteDir(
                this.getPathText(self.pathItems).concat([item.name]),
                function (status, data) {
                    if (status == 200) {
                        self.logInfo('删除成功'); self.refreshChildren();
                    } else {
                        self.logError(`删除失败, ${status}, ${data.error}`);
                    }
                },
                function () {
                    self.logError('请求失败');
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
                self.logError('文件名不能为空');
                return;
            }
            this.wetoolFS.fsRename(
                self.getFSPath(self.renameItem.name), self.renameItem.newName, {
                onload_callback: function (status, data) {
                    if (status == 200) {
                        self.logInfo('重命名成功');
                        self.refreshChildren();
                    } else {
                        console.log(data);
                        console.log(typeof data);
                        console.log(data.error);
                        self.logError(`重命名失败, ${data.error}`, autoHideDelay = 5000)
                    }
                },
                onerror_callback: function () { self.logError('请求失败') }
            });
        },
        showRenameModal: function (item) {
            this.renameItem = { name: item.name, newName: item.name }
        },
        createDir: function () {
            var self = this;
            if (self.newDir.name == '') {
                self.logError(translate('dirNameNull'))
                return;
            }
            if (self.newDirNameIsInvalid) {
                self.logError(translate('invalidChar'))
                return;
            }
            let newDir = self.getDirPath(self.currentDirList.concat(self.newDir.name));
            self.wetoolFS.fsCreate(newDir, {
                onload_callback: function (status, data) {
                    if (status == 200) {
                        self.logInfo('目录创建成功');
                        self.refreshChildren();
                    } else {
                        self.logError(`目录创建失败, ${status}, ${data.error}`, autoHideDelay = 5000)
                    }
                    self.newDir = { name: '' }
                },
                onerror_callback: function () {
                    self.logError('请求失败');
                }
            });
        },
        uploadFiles: function (files) {
            var self = this;
            if (files.length == 0) { return };
            self.logInfo(`准备上传 ${files.length} 个文件`);
            for (let index = 0; index < files.length; index++) {
                const file = files[index];
                const progress = { file: file.name, loaded: 0, total: 100 };
                self.uploadQueue.tasks.push(progress);

                self.wetoolFS.uploadFile(
                    self.getPathText(self.pathItems), file,
                    function (status, data) {
                        if (status != 200) {
                            self.logError(`文件上传失败, ${status}, ${data.error}`, autoHideDelay = 5000)
                        }else{
                            self.refreshChildren()
                            self.uploadQueue.completed += 1;
                        }
                    },
                    function () { self.logError('请求失败') },
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
            self.wetoolFS.fsGet(self.getFSPath(item.name), false, {
                onload_callback: function (status, data) {
                    if (status == 200) {
                        self.fileEditor.content = data;
                    } else {
                        self.logError(`文件内容获取失败, ${status}, ${data.error}`, autoHideDelay = 5000)
                    }
                },
                onerror_callback: function () {
                    self.logError('请求失败');
                },
            });
        },
        updateFile: function () {
            this.logError('文件修改功能未实现');
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
        search: function(){
            var self = this;
            self.showPardir = true;
            self.searchResult = [];
            this.wetoolFS.search(
                this.searchPartern,
                function (status, data) {
                    if (status == 200) {
                        self.searchResult = data.dirs;
                        self.children = data.dirs;
                        console.log(`search result`);
                        console.log(self.children);
                    } else {
                        self.logError(`搜索失败, ${status}, ${data.error}`, autoHideDelay = 5000)
                    }
                },
                function () {
                    self.logError('请求失败');
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
                this.newDirNameIsInvalid = true;
            }else{
                this.newDirNameIsInvalid = false;
            }
        },
        refreshDir: function(){
            var self = this;
            this.wetoolFS.fsGet(
                this.currentDirList.join('/'), self.showAll, {
                    onload_callback: function (status, data) {
                        if (status == 200) {
                            self.children = data.dir.children;
                            self.diskUsage = data.dir.disk_usage;
                        } else {
                            self.logError(`请求失败，${status}, ${data.error}`);
                        }
                    }
                }
            );
        }
    },

    created: function () {
        this.goTo(-1);
    },
});
