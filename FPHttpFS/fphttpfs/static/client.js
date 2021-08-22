class WetoolFS {
    constructor() {
        this.postAction = function (body, onload_callback, onerror_callback = null, uploadCallback = null) {
            var xhr = new XMLHttpRequest();
            xhr.onload = function () {
                var data = JSON.parse(xhr.responseText);
                onload_callback(xhr.status, data);
            };
            xhr.onerror = function () {
                if (onerror_callback != null) {
                    onerror_callback();
                }
            };
            xhr.open("POST", '/action', true);
            if (body.constructor.name == 'FormData') {
                xhr.upload.addEventListener('progress', function (e) {
                    if (e.lengthComputable) {
                        if (uploadCallback != null) {
                            uploadCallback(e.loaded, e.total);
                        }
                    }
                });
                xhr.send(body);
            } else {
                xhr.send(JSON.stringify({ action: body }));
            }
        };
        this._getRespData = function(xhr){
            console.log('xhr.responseText');
            console.log(xhr.responseText)
            let contentType = xhr.getResponseHeader('content-type');
            if (contentType && contentType.indexOf('application/json') >= 0){
                return JSON.parse(xhr.responseText);
            }
            return xhr.responseText
        }
        this.request = function(method, url, params){
            var self = this;
            let get_params = {
                onload_callback: null,
                onerror_callback: null,
                body: null
            };
            for (var k in params){
                get_params[k] = params[k]
            }
            var xhr = new XMLHttpRequest();
            xhr.onload = function () {
                let data = self._getRespData(xhr);
                if (params.onload_callback){
                    get_params.onload_callback(xhr.status, data); 
                }
            };
            xhr.onerror = function () {
                if (params.onerror_callback ){
                    get_params.onerror_callback(xhr.status, data);
                }
            };
            xhr.open(method, url, true);
            if (params.body){
                console.log('params.body:')
                console.log(params.body)
                xhr.send(JSON.stringify(params.body));
            }else{
                xhr.send();
            }
        }
        this._safe_path = function(path){return path.slice(0, 1) == '/' ? path : '/' + path}
        this.get = function(url, params){this.request('GET', url, params)}
        this.delete = function(url, params){this.request('DELETE', url, params)}
        this.post = function(url, params){this.request('POST', url, params)}
        this.put = function(url, params){this.request('PUT', url, params)}

        this.fsGet = function(path, showAll=false, params={}){
            // path like: /dir1/dir2
            let tmp_path = this._safe_path(path);
            this.get(`/fs${tmp_path}?showAll=${showAll}`, params)
        }
        this.fsDelete = function(path, force=false, params={}){
            let tmp_path = this._safe_path(path);
            this.delete(`/fs${tmp_path}?force=${force}`, params)}
        this.fsCreate = function(path, params={}){
            let tmp_path = this._safe_path(path);
            this.post(`/fs${tmp_path}`, params);
        }
        this.fsRename = function(path, new_name, params={}){
            let tmp_path = this._safe_path(path);
            let req_params = params;
            req_params.body = {'dir': {'new_name': new_name}};
            this.put(`/fs${tmp_path}`, req_params);
        }

        this.listDir = function (pathItems, showAll, onload_callback, onerror_callback = null) {
            let dir = pathItems.join('/')
            this.fsGet(dir, showAll, {
                onload_callback: onload_callback,
                onerror_callback: onerror_callback})
        };
        this.deleteDir = function (pathItems, onload_callback, onerror_callback = null) {
            let dir = pathItems.join('/')
            this.fsDelete(dir, false, {
                onload_callback: onload_callback,
                onerror_callback: onerror_callback})
        };

        this.createDir = function (dirPath, onload_callback, onerror_callback = null) {
            this.fsCreate(dirPath, {
                onload_callback: onload_callback,
                onerror_callback: onerror_callback
            });
        };
        this.getFileContent = function (filePath, onload_callback, onerror_callback = null) {
            this.fsGet(filePath, this.showAll, {
                onload_callback: onload_callback,
                onerror_callback: onerror_callback
            })
        };
        this.uploadFile = function (path_list, file, onload_callback, onerror_callback = null, uploadCallback = null) {
            var action = {
                name: 'upload_file',
                params: { path_list: path_list , relative_path: file.webkitRelativePath}
            };
            var formData = new FormData();
            formData.append('action', JSON.stringify(action));
            formData.append('file', file);
            this.postAction(formData, onload_callback, onerror_callback = onerror_callback, uploadCallback = uploadCallback);
        };
        this.search = function(partern, onload_callback, onerror_callback = null){
            var action = {
                name: 'search',
                params: { partern: partern}
            };
            this.postAction(action, onload_callback, onerror_callback = onerror_callback);
        };
        this.getServerInfo = function(onload_callback, onerror_callback = null){
            var xhr = new XMLHttpRequest();
            xhr.onload = function () {
                var data = JSON.parse(xhr.responseText);
                onload_callback(xhr.status, data);
            };
            xhr.onerror = function () {
                if (onerror_callback != null) {
                    onerror_callback();
                }
            };
            xhr.open("GET", '/server', true);
            xhr.send();
        };
        this._getEndpoint = function(){
            let port = window.location.port != '' ? `/${window.location.port}` : ''
            return `${window.location.protocol}//${window.location.host}${port}`
        }
        this.getFSLink = function(dirPath){
            return `${this._getEndpoint()}/fs/${dirPath}`
        }
        
    }
}

function delItemsAfter(array, afterIndex){
    // Delete array items after <afterIndex>
    while(array.length > afterIndex +1){
        array.pop();
    }
}

function getItemsBefore(array, beforeIndex){
    let items = [];
    if (beforeIndex >= array.length){
        items = array;
    }else{
        for (let index = 0; index <= beforeIndex; index++) {
            items.push(array[index]);
        }
    }
    return items;
}