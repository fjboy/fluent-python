//use custom bootstrap styling
import {HttpFSClient} from './httpfsclient.js'

new Vue({
    el: '#app',
    data: {
        conf: {
            pbarHeight: {current: 5, min:1, max:10},
        },
        children: [],
        downloadFile: { name: '', qrcode: '' },
        showAll: false,
        fsClient: new HttpFSClient(),
        renameItem: { name: '', newName: '' },
        newDir: { name: '', validate: null },
        fileEditor: { name: '', content: '' },
        uploadQueue: { completed: 0, tasks: [] },
        debug: false,
        pathItems: [],
        diskUsage: { used: 0, total: 100 },
        searchPartern: '',
        searchResult: [],
        showPardir: false,
        currentDirList: [],
        log: null,
        searchHistory: [],
    },
    methods: {
        refreshChildren: function () {
            this.log.debug('更新目录');
            this.goTo(this.pathItems.length - 1);
        },
        clickPath: function (child) {
            if (child.type != "folder") { return }
            var self = this;
            let dirPath = ''
            if (child.pardir){
                dirPath = `${child.pardir}/${child.name}`;
            } else {
                dirPath = self.getPathText(self.pathItems).concat(child.name).join('/');
            }
            this.fsClient.ls(
                dirPath, self.showAll
            ).then(success => {
                if (child.pardir) {
                    // TODO delete currentDirList use pathItems
                    this.pathItems = [];
                    this.currentDirList = [];
                    child.pardir.slice(1).split('/').forEach(item => {
                        this.pathItems.push({text: item, href: '#'});
                        self.currentDirList.push(item)
                    })
                    console.log(self.currentDirList)
                }
                self.currentDirList.push(child.name);
                self.pathItems.push({ text: child.name, href: '#' })
                self.children = success.data.dir.children;
                self.diskUsage = success.data.dir.disk_usage;
            }).catch(error => {
                self.log.error(`请求失败，${error.status}, ${error.data.error}`);
            });
        },
        getPathText: function (pathItems) {
            let pathText = [];
            pathItems.forEach(function (item) { pathText.push(item.text) });
            return pathText;
        },
        getDirPath: function (dirItems) {return dirItems.join('/')},
        getCurrentPath: function () { return this.getDirPath(this.pathItems) },
        getFSPath: function (dirName) { return this.getDirPath(this.currentDirList.concat(dirName)) },
        getFSUrl: function (dirItem) {
            this.fsClient.getFsUrl(
                dirItem.pardir ? `${dirItem.pardir}/${dirItem.name}` : this.getFSPath(dirItem.name)
            )
        },
        getDownloadUrl: function (dirItem) {
            return this.fsClient.getDownloadUrl(
                dirItem.pardir ? `${dirItem.pardir}/${dirItem.name}` : this.getFSPath(dirItem.name)
            );
        },
        goTo: function (clickIndex) {
            var self = this;
            self.showPardir = false;
            let pathItems = self.getPathText(getItemsBefore(self.pathItems, clickIndex));
            this.fsClient.ls(
                pathItems.join('/'), self.showAll
            ).then(success => {
                delItemsAfter(self.currentDirList, clickIndex);
                delItemsAfter(self.pathItems, clickIndex);
                self.children = success.data.dir.children;
                self.diskUsage = success.data.dir.disk_usage;
            }).catch(error => {
                self.log.error(`请求失败，${error.status}, ${error.data.error}`);
            });
        },
        setFileQrcode: function (dirItem) {
            this.downloadFile = dirItem;
        },
        showFileQrcode: function () {
            let filePath = null;
            if (this.downloadFile.pardir) {
                filePath = `${this.downloadFile.pardir}/${this.downloadFile.name}`;
            } else {
                filePath = this.getFSPath(this.downloadFile.name);
            }
            this.showQrcode('fileQrcode', this.fsClient.getFSLink(filePath))
        },
        makeSureDelete: function (item) {
            var self = this;
            this.$bvModal.msgBoxConfirm(item.name, {
                title: I18N.t('makeSureDelete'),
                okVariant: 'danger',
            }).then(value => {
                self.log.debug(`make sure delete? ${value}`)
                if (value == true) {
                    self.deleteDir(item);
                    self.refreshChildren();
                }
            });
        },
        deleteDir: function (item) {
            var self = this;
            this.fsClient.rm(
                this.getPathText(self.pathItems).concat([item.name]).join('/'), false
            ).then(successs => {
                self.log.info(I18N.t('deleteSuccess'));
                self.refreshChildren();
            }).catch(error => {
                self.log.error(`${I18N.t('deleteFailed')}, ${error.status}, ${error.data.error}`);
            });
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
                self.log.error(I18N.t('fileNameCannotEmpty'));
                return;
            }
            this.rename(
                self.getFSPath(self.renameItem.name), self.renameItem.newName
            ).then(success => {
                self.log.info(I18N.t('renameSuccess'));
            }).catch(error => {
                self.log.error(`${I18N.t('renameFailed')}, ${error.status} ${error.data.error}`, 5000)
            });
        },
        showRenameModal: function (item) {
            this.renameItem = { name: item.name, newName: item.name }
        },
        createDir: function () {
            var self = this;
            if (this.newDir.name == '') {
                this.log.error(I18N.t('dirNameNull'))
                return;
            }
            if (!this.newDir.validate) {
                this.log.error(I18N.t('invalidChar'))
                return;
            }
            var self = this;
            let newDir = self.getDirPath(self.currentDirList.concat(self.newDir.name));
            self.fsClient.mkdir(newDir).then(success => {
                console.log(success)
                self.log.info(I18N.t('createDirSuccess'));
                self.refreshChildren();
            }).catch(error => {
                console.error(error);
                self.log.error(`${I18N.t('createDirFailed')}, ${error.status}, ${error.data.error}`, autoHideDelay = 5000)
            });
        },
        uploadFiles: function (files) {
            var self = this;
            if (files.length == 0) { return };
            self.log.debug(`准备上传 ${files.length} 个文件`);
            for (let index = 0; index < files.length; index++) {
                let file = files[index];
                let progress = { file: file.name, loaded: 0, total: 100 };
                self.uploadQueue.tasks.push(progress);
                self.fsClient.upload(
                    self.getPathText(self.pathItems).join('/'), file,
                    uploadEvent => {
                        progress.loaded = uploadEvent.loaded;
                        progress.total = uploadEvent.total;
                    }
                ).then(success => {
                    self.refreshChildren()
                    self.uploadQueue.completed += 1;
                }).catch(error => {
                    self.log.error(`${I18N.t('uploadFailed')}, ${error.data.error}`, 5000)
                });
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
            self.fsClient.cat(
                self.getFSPath(item.name)
            ).then(success => {
                self.fileEditor.content = success.data;
            }).catch(error => {
                let msg = `${I18N.t('getfileContentFailed')}, ${error.status}, ${error.data.error}`;
                self.log.error(msg, 5000);
            })
        },
        updateFile: function () {
            this.log.error('文件修改功能未实现');
        },
        getDiskUsage: function () {
            let ONE_KB = 1024;
            let ONE_MB = ONE_KB * 1024;
            let ONE_GB = ONE_MB * 1024;
            let displayUsed = this.diskUsage.used;
            let displayTotal = this.diskUsage.total;
            let unit = 'B'
            if (this.diskUsage.total >= ONE_GB) {
                displayUsed = this.diskUsage.used / ONE_GB;
                displayTotal = this.diskUsage.total / ONE_GB;
                unit = 'GB';
            } else if (this.diskUsage.total >= ONE_MB) {
                displayUsed = this.diskUsage.used / ONE_MB;
                displayTotal = this.diskUsage.total / ONE_MB;
                unit = 'MB';
            } else if (this.diskUsage.total >= ONE_KB) {
                displayUsed = this.diskUsage.used / ONE_KB;
                displayTotal = this.diskUsage.total / ONE_KB;
                unit = 'KB';
            }
            return `${displayUsed.toFixed(2)}${unit}/${displayTotal.toFixed(2)}${unit}`;
        },
        refreshSearchHistory: function () {
            var self = this;
            self.fsClient.findHistory().then(success => {
                self.searchHistory = success.data.search.history;
            }).catch(error => {
                self.log.error(I18N.t('getSearchHistoryFailed'));
            })
        },
        search: function () {
            if (this.searchPartern == '') { return; }
            var self = this;
            self.showPardir = true;
            self.searchResult = [];
            this.fsClient.find(this.searchPartern).then(success => {
                self.children = success.data.search.dirs;
            }).catch(error => {
                self.log.error(`${I18N.t('searchFailed')}, ${error.status}, ${error.data.error}`, 5000)
            });
        },
        showQrcode: function (elemId, text) {
            // chinese is not support for qrcode.js now
            console.debug(`make code: ${text}`)
            var qrcode = new QRCode(elemId);
            qrcode.makeCode(text);
        },
        refreshConnectionLink: function () {
            this.showQrcode('connectionLink', window.location.href)
        },
        checkIsDirInvalid: function () {
            let invalidChar = this.newDir.name.search(/[!@#$%^&*():";'<>?,.~]/i);
            if (invalidChar >= 0) {
                this.newDir.validate = false;
            } else {
                this.newDir.validate = true;
            }
        },
        refreshDir: function () {
            var self = this;
            this.fsClient.ls(
                this.currentDirList.join('/'), self.showAll
            ).then(success => {
                self.children = success.data.dir.children;
                self.diskUsage = success.data.dir.disk_usage;
            }).catch*(error => {
                self.log.error(`请求失败，${error.data.error}`);
            });
        },
        saveSettings: function(){
            this.log.warn('TODO: saving settings');
        }
    },
    created: function () {
        setDisplayLang(getUserSettedLang() || navigator.language);
        this.log = new LoggerWithBVToast(this.$bvToast, false)
        this.log.debug('vue app created');
        this.goTo(-1);
    },
});
