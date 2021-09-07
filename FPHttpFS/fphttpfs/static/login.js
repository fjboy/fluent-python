import {HttpFSClient} from './httpfsclient.js'

new Vue({
    el: '#app',
    data: {
        log: null,
        auth: {username: '', password: ''},
        fsclient: new HttpFSClient()
    },
    methods: {
        login: function(){
            let self = this;
            if (this.auth.username == '' || this.auth.password == ''){
                self.log.error(I18N.t('invalidAuthInfo'))
                return;
            }
            this.fsclient.auth(
                self.auth
             ).then( success => {
                 self.log.error(I18N.t('authSuccess'));
                 window.location.reload();
             }).catch(error => {
                 self.log.error(I18N.t('loginFailed'))
             });
        },
        changeLanguage: function(language,){
            setDisplayLang(language);
        }
    },
    created: function(){
        setDisplayLang(getUserSettedLang());
        this.log = new LoggerWithBVToast(this.$bvToast, false)
    }
});