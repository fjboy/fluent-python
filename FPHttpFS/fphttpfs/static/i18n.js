const MESSAGES = {
    en: {
        ok: 'ok',
        cancel: 'Cancel',
        lang: 'Language',
        en: 'English',
        zh: 'Chinese',
        user: 'User',
        setting: 'setting',
        signOut: 'sing out',
        fileUploadProgress: 'File upload progress',
        scanLink: 'Scan to connect ',
        scanUsePhoneBrower: 'Please use the mobile browser to scan',
        search: 'search',
        uploadFiles: 'upload files',
        uploadDir: 'upload directory',
        newFile: 'create file',
        newDir: 'create dirctory',
        delete: 'delete',
        rename: 'rename',
        view: 'view',
        displayQRCode: 'Display QR code ',
        download: 'download',
        file: 'file',
        size: 'size',
        modifyTime: 'modify time',
        operation: 'operation',
        displayAll: 'display all ',
        root: 'roog',
        back: 'back',
        refresh: 'refresh',
        filename: 'file name',
        newFileName: 'new file name',
        pleaseInputFileName: 'please input file name',
        pleaseInput: 'please input ...',
        createNewDir: 'create new dir',
        createDirsTips: 'Use / to create multi-level directories, such as foo/bar, invalid chars: !@#$%^&*():\";\'<>?,.~.',
        diskUsage: 'disk usage',
        invalidChar: 'invalid char',
        dirNameNull: 'directory is null',
        makeSureDelete: 'Are you sure delete this file/directory?',
        accountSignIn: 'Sign In With Account',
        signIn: 'Sign In',
        username: 'username',
        password: 'password',
        pleaseInputUsername: 'please input username',
        pleaseInputPassword: 'please input password',
        authFailed: 'auth Failed',
        authSuccess: 'auth success',
        loginFailed: 'Login Failed',
        getfileContentFailed: 'get file content failed',
        fileNameCannotEmpty: 'file name can not be empty',
        getSearchHistoryFailed: 'get search history failed',
    },
    zh: {
        ok: '确定',
        cancel: '取消',
        lang: '语言',
        en: '英文',
        zh: '中文',
        user: '用户',
        setting: '设置',
        signOut: '注销',
        fileUploadProgress: '文件上传进度',
        scanLink: '扫一扫连接',
        scanUsePhoneBrower: '打开手机浏览器扫一扫',
        search: '搜索',
        uploadFiles: '上传文件',
        uploadDir: '上传目录',
        newFile: '新建文件',
        newDir: '新建目录',
        delete: '删除',
        rename: '重命名',
        view: '预览',
        displayQRCode: '显示二维码',
        download: '下载',
        file: '文件',
        size: '大小',
        modifyTime: '修改时间',
        operation: '操作',
        displayAll: '显示全部',
        root: '根目录',
        back: '返回',
        refresh: '刷新',
        filename: '文件名',
        newFileName: '新文件名',
        pleaseInputFileName: '请输入新文件名',
        pleaseInput: '请输入...',
        createNewDir: '创建新目录',
        createDirsTips: '使用 / 创建多层目录，例如 foo/bar，非法字符包括： !@#$%^&*():\";\'<>?,.~。',
        diskUsage: '磁盘空间',
        invalidChar: '非法字符',
        dirNameNull: '目录不能为空',
        makeSureDelete: '确定要删除该文件/目录？',
        accountSignIn: '账号登录',
        signIn: '登录',
        username: '用户名',
        password: '密码',
        pleaseInputUsername: '请输入用户名',
        pleaseInputPassword: '请输入密码',
        authFailed: '认证失败',
        authSuccess: '认证成功',
        loginFailed: '登录失败',
        getfileContentFailed: '文件内容获取失败',
        fileNameCannotEmpty: '文件名不能为空',
        getSearchHistoryFailed: '无法获取搜索历史',
    },
};

const I18N = new VueI18n({locale: 'en', messages: MESSAGES})

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
    return I18N.locale;
}

function setDisplayLang(language) {
    I18N.locale = language;
    document.cookie = `language=${language}`;
}
