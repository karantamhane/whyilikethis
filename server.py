import socket, sys
import StringIO
import whyilikethis

class Server():

    def __init__(self, server_address, application):
        self.host, self.port = server_address
        self.application = application

    def build_environment(self, request_line, env, body):
        # Create the environ dict
        method, orig_path, http_version = request_line.split(" ")
        # Extract query strings from url - currently ignores query strings to avoid crashes on unknown routes
        if "?" in request_line:
            path, env['QUERY_STRING'] = orig_path.split("?", 1)[0], ''
        else:
            path, env['QUERY_STRING'] = orig_path, ''
        # Replace the 'COOKIE' env key to 'HTTP_COOKIE' for wsgi
        if 'COOKIE' in env:
            env['HTTP_COOKIE'] = env['COOKIE']

        # Add all other necessary wsgi env keys
        env['REQUEST_METHOD'] = method
        env['PATH_INFO'] = path
        env['SERVER_NAME'] = self.host #socket.getfqdn(self.host)
        env['SERVER_PORT'] = str(self.port)

        env['wsgi.version']      = (1, 0)
        env['wsgi.url_scheme']   = 'http'
        env['wsgi.input']        = StringIO.StringIO(body)
        env['wsgi.errors']       = sys.stderr
        env['wsgi.multithread']  = False
        env['wsgi.multiprocess'] = False
        env['wsgi.run_once']     = False

        # print 'env =',env
        return env

    # Temporary method for testing file upload
    def parse_headers(self, headers):
        # Create the environ dict
        headers_list = headers.split("\r\n")
        request_line = headers_list[0]
        print '['+str(request_line)+']'
        headers = headers_list[1:]
        # print 'headers =',headers
        env_list = [[line.split(": ")[0].upper(), line.split(": ")[1]] for line in headers]
        # Convert all hyphens to underscores for wsgi-friendly env keys
        for e in env_list:
            if "-" in e[0]:
                e[0] = e[0].split("-")[0] + "_" + e[0].split("-")[1]
        return request_line, dict(env_list)

    def serve(self):
        # this is the main server loop
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(10)
        try:
            while True:
                # Accept client connection
                self.client_socket, client_ip = server_socket.accept()
                # Read from client socket till all headers are received
                request = self.client_socket.recv(1024)
                headers_string = ''
                while "\r\n\r\n" not in request:
                    headers_string += request
                    request = self.client_socket.recv(1024)
                    # print 'request is now',request
                # Once header-body separator is seen, exit loop and separate header and body chunks
                last_header_chunk, first_body_chunk = request.split("\r\n\r\n", 1)
                headers_string += last_header_chunk
                body = first_body_chunk

                # Parse headers into dict and retrieve content-length
                request_line, header_dict = self.parse_headers(headers_string)
                content_length = header_dict.get('CONTENT_LENGTH', 0)
                # print 'extracted content-length is',content_length

                while len(body) < int(content_length):
                    # Read the rest of the request body till all content-length is received
                    body += self.client_socket.recv(4096)

                # Create the entire wsgi environment with all parameters
                env = self.build_environment(request_line, header_dict, body)
                self.handle_request(env)
        finally:
            print 'Closing server socket...'
            server_socket.close()

    def handle_request(self, env):
        # this is where each request is handled and application is called with env and the response procedure
        # Pass request to the application and process response
        result = None
        if env:
            result = self.application(env, self.start_response)
        # result is an iterable
        try:
            self.write(result)
        except Exception as e:
            print "Error in handling request!", e.message
        finally:
            if result:
                result.close()

    def start_response(self, status, headers):
        # The procedure that returns a write callable for wsgi
        self.headers = [status, headers]
        return self.write

    def write(self, result):
        try:
            status, response_headers = self.headers
            response = 'HTTP/1.1 {status}\r\n'.format(status=status)
            for header in response_headers:
                response += '{0}: {1}\r\n'.format(*header)
            response += '\r\n'
            for data in result:
                response += data
            # print(''.join(
            #     '> {line}\n'.format(line=line)
            #     for line in response.splitlines()
            # ))
            self.client_socket.sendall(response)
            self.client_socket.close()
        except Exception as e:
            print "Error sending response! Closing client socket...",e.message
            self.client_socket.close()



if __name__ == '__main__':

    server = Server(('localhost', 5000), whyilikethis.app)
    print 'Starting server...'
    server.serve()
