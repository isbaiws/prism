#!/usr/bin/env python
import BaseHTTPServer
import json

class RestHandler(BaseHTTPServer.BaseHTTPRequestHandler, object):

    def do_POST(self):
        fn = 'recv/'+self.path.replace('/', '%')[1:]
        try:
            email_raw = self.rfile.read(int(self.headers['content-length']))
            email = json.loads(email_raw)
            # some process here
            open(fn, 'w').write(json.dumps(email))
            self.send_201({'hello': 'world'})
        except Exception as e:
            self.send_400({str(type(e)): str(e)})

    def do_GET(self):
        fn = 'recv/'+self.path.replace('/', '%')[1:]
        try:
            self.send_200(json.loads(open(fn).read()))
        except Exception as e:
            self.send_400({str(type(e)): str(e)})

    def send_200(self, body):
        body_str = json.dumps(body)
        self.send_response(200)
        self.send_json(body_str)

    def send_201(self, body):
        body_str = json.dumps(body)
        self.send_response(201)
        self.send_json(body_str)

    def send_400(self, body):
        body_str = json.dumps(body)
        self.send_response(400)
        self.send_json(body_str)
    
    def send_json(self, body):
        self.send_header('Content-Type', 'application/json')
        self.send_header("Content-Length", str(len(body)))
        self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(body)

if __name__ == '__main__':
    server_address = ('', 8008)
    httpd = BaseHTTPServer.HTTPServer(server_address, RestHandler)
    print 'Server is listening on %s:%s' % (httpd.server_name, httpd.server_port) 
    httpd.serve_forever()
