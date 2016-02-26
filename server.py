import socket
import sys
import StringIO
import whyilikethis

class Server():

    def __init__(self, server_address, application):
        self.host, self.port = server_address
        self.application = application

    def build_environment(self, parsed_request):
        # Create the environ dict
        env = {}

        env['REQUEST_METHOD'] = parsed_request[0]
        env['PATH_INFO'] = parsed_request[1]
        env['SERVER_NAME'] = socket.getfqdn(self.host)
        env['SERVER_PORT'] = str(self.port)

        env['wsgi.version']      = (1, 0)
        env['wsgi.url_scheme']   = 'http'
        env['wsgi.input']        = StringIO.StringIO(parsed_request)
        env['wsgi.errors']       = sys.stderr
        env['wsgi.multithread']  = False
        env['wsgi.multiprocess'] = False
        env['wsgi.run_once']     = False

        return env

    def serve(self):
        # this is the main server loop
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(10)
        while True:
            self.client_socket, client_ip = server_socket.accept()
            request = self.client_socket.recv(1024)
            self.handle_request(request)

    def handle_request(self, request):
        # this is where each request is handled and application is called with env and the response procedure
        parsed_request = request.split(" ")
        # print 'request in handle_request =',request
        env = self.build_environment(parsed_request)

        result = None
        if env:
            result = self.application(env, self.start_response)
        # result is an iterable
        try:
            for data in result:
                self.write(data)
        except Exception as e:
            print "Error in handling request!", e.message
        finally:
            if result:
                result.close()

    def start_response(self, status, headers):
        # The procedure that returns a write callable
        print 'status and headers =',status, headers
        self.headers = [status, headers]
        return self.write

    def write(self, data):
        self.client_socket.sendall(data)
        self.client_socket.close()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit("Usage: python server.py whyilikethis.py")

    server = Server(('localhost', 5000), whyilikethis.app)
    print 'Starting server...'
    server.serve()
