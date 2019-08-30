import http.server
import requests
import os
from urllib.parse import unquote, parse_qs
import threading
from socketserver import ThreadingMixIn
import subprocess

class ThreadHTTPServer(ThreadingMixIn, http.server.HTTPServer):
    "This is an HTTPServer that supports thread-based concurrency."

class RequestHandler(http.server.SimpleHTTPRequestHandler):

    def do_POST(self):
        length = self.headers.get('content-length')
        content_type = self.headers.get('content-type')
        nbytes = int(length)
        data = self.rfile.read(nbytes)

        path = self.path
        file_name = self.translate_path(path)

        cmd = [file_name]

        if content_type == 'application/x-www-form-urlencoded':
            cmd.append(data)

        p = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
        output, err = p.communicate()
        self.send_response(200, 'Here comes the script output!')
        self.wfile.write(output)
        print(output)
        p.stdout.close()
        p.stderr.close()

if __name__ == '__main__':
    server_address = ('', int(os.environ.get('PORT', '3000')))
    httpd = ThreadHTTPServer(server_address, RequestHandler)
    httpd.serve_forever()
