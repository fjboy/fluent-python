class HttpFSClient {
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
        this._getEndpoint = function(){
            let port = window.location.port != '' ? `/${window.location.port}` : ''
            return `${window.location.protocol}//${window.location.host}${port}`
        }
        this.get = function(url, params){
            this.request('GET', url, params)
        }
        this.delete = function(url, params){this.request('DELETE', url, params)}
        this.post = function(url, params){this.request('POST', url, params)}
        this.put = function(url, params){this.request('PUT', url, params)}
        this.getFSLink = function(dirPath){return `${this._getEndpoint()}/fs/${dirPath}`}

        this.getFsUrl = function(dirPath){return `/fs${this._safe_path(dirPath)}`}
        this.getDownloadUrl = function(dirPath){return `/file${this._safe_path(dirPath)}`}

        this.fsGet = function(path, showAll=false){
            // path like: /dir1/dir2
            let tmp_path = this._safe_path(path);
            return axios.get(`/fs${tmp_path}?showAll=${showAll}`)
        }
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

        this.ls = function (path, showAll=false) {
            let safe_path = this._safe_path(path);
            return axios.get(`/fs${safe_path}?showAll=${showAll}`)
        };
        this.rm = function (path, force=false) {
            let safe_path = this._safe_path(path);
            return axios.delete(`/fs${safe_path}?force=${force}`)
        }
        this.mkdir = function (path) {
            let safe_path = this._safe_path(path);
            return axios.post(`/fs${safe_path}`)
        };
        this.rename = function(path, new_name){
            let tmp_path = this._safe_path(path);
            return axios.put(`/fs${tmp_path}`, {'dir': {'new_name': new_name}})
        }

        this.uploadFile = function (path_list, file, onload_callback, onerror_callback = null, uploadCallback = null) {
            let action = {
                name: 'upload_file',
                params: { path_list: path_list , relative_path: file.webkitRelativePath}
            };
            let formData = new FormData();
            formData.append('action', JSON.stringify(action));
            formData.append('file', file);
            this.postAction(formData, onload_callback, onerror_callback = onerror_callback, uploadCallback = uploadCallback);
        };
        this.cat = function(file){
            let safe_path = this._safe_path(file);
            return axios.get(`/file${safe_path}`)
        };
        this.upload = function(path, file, uploadCallback=null){
            let formData = new FormData();
            formData.append('file', file);
            let safe_path = this._safe_path(path);
            return axios({
                url: `/file${safe_path}`,
                method: 'POST',
                data: formData,
                headers: {'Content-Type': 'multipart/form-data'},
                onUploadProgress: function(progressEvent){
                    if(uploadCallback){
                        uploadCallback(progressEvent)
                    }
                },
            });
        };
        this.find = function(name){
            // find files by specified name, e.g. *.py, *.js
            return axios.post('/search', {'search': {'partern': name}})
        };
        this.findHistory = function(){
            return axios.get('/search');
        };
        this.auth = function(authInfo, params={}){
            let req_params = params;
            req_params.body = {auth: authInfo}
            this.post('/auth', req_params);
        };
    }
}

export {HttpFSClient};
