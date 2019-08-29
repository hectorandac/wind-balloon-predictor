import BaseHTTPServer
import SimpleHTTPServer
import subprocess

class RequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def do_POST(self):
        length = self.headers.getheader('content-length')
        content_type = self.headers.getheader('content-type')
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

httpd = BaseHTTPServer.HTTPServer(('', 8080), RequestHandler)

httpd.serve_forever()
