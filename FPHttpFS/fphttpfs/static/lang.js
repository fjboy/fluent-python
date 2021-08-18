var DIRECOTRY = {
    ok: { en: 'ok', zh: '确定' },
    cancel: { en: 'Cancel', zh: '取消' },

    lang: { en: 'Language', zh: '语言' },
    en: { en: 'English', zh: '英文' },
    zh: { en: 'Chinese', zh: '中文' },

    user: { en: 'User', zh: '用户' },
    setting: { en: 'setting', zh: '设置' },
    signOut: { en: 'sing out', zh: '注销' },

    fileUploadProgress: { en: 'File upload progress', zh: '文件上传进度' },

    scanLink: { en: 'Scan to connect ', zh: '扫一扫连接' },
    scanUsePhoneBrower: { en: 'Please use the mobile browser to scan', zh: '请使用手机浏览器扫一扫' },
    search: { en: 'search', zh: '搜索' },

    uploadFiles: { en: 'upload files', zh: '上传文件' },
    uploadDir: { en: 'upload directory', zh: '上传目录' },
    newFile: { en: 'create file', zh: '新建文件' },
    newDir: { en: 'create dirctory', zh: '新建目录' },

    delete: { en: 'delete', zh: '删除' },
    rename: { en: 'rename', zh: '重命名' },
    view: { en: 'view', zh: '预览' },
    displayDownloadQRCode: { en: 'Display Download QR code ', zh: '显示下载二维码' },
    download: {en: 'download', zh: '下载'},

    file: { en: 'file', zh: '文件' },
    size: { en: 'size', zh: '大小' },
    modifyTime: { en: 'modify time', zh: '修改时间' },
    operation: { en: 'operation', zh: '操作' },
    displayAll: { en: 'display all ', zh: '显示全部' },

    root: { en: 'roog', zh: '根目录' },
    back: { en: 'back', zh: '返回' },
    refresh: { en: 'refresh', zh: '刷新' },

    filename: { en: 'roog', zh: '根目录' },
    newFilename: { en: 'new file name', zh: '新文件名' },
    pleaseInputFileName: { en: 'please input file name', zh: '请输入新文件名' },

    pleaseInput: { en: 'please input ...', zh: '请输入...' },
    createDirsTips: { en: 'Use / to create multi-level directories, such as foo/bar ', zh: '使用 / 创建多层目录，例如 foo/bar' },
    diskUsage: {en: 'disk usage', zh: '磁盘空间'},

};
var SUPPORT_LANG = ['en', 'zh'];

function getUserSettedLang() {
    const cookies = document.cookie.split(';');
    for (let index = 0; index < cookies.length; index++) {
        const config = cookies[index].split('=');
        if (config[0].trim() == 'language') {
            return config[1].trim();
        }
    }
    return null;
}

function getDispalyLang() {
    let useLang = getUserSettedLang();
    if (useLang != null && SUPPORT_LANG.indexOf(useLang) >= 0) { return useLang; }
    useLang = navigator.language || navigator.userLanguage;
    if (SUPPORT_LANG.indexOf(useLang) >= 0) { return useLang; }
    useLang = useLang.split('-')[0];
    if (SUPPORT_LANG.indexOf(useLang) >= 0) { return useLang; }
    return 'en';
}


function setDisplayLang(language) {
    document.cookie = `language=${language}`;
}


var USE_LANG = getDispalyLang();

var translate = function (content) {
    if (!DIRECOTRY.hasOwnProperty(content)) {
        return content;
    }
    return DIRECOTRY[content][USE_LANG];
}
