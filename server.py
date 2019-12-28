import socket
import sys
import os


def main():
    server, connection_type, client_socket, client_address = initialize_server(sys.argv[1])
    while True:
        if connection_type == "close":
            client_socket, client_address = server.accept()
        # if the client doesn't send a new query in 1 second, close connection.
        client_socket.settimeout(1.0)
        try:
            query = client_socket.recv(2048)
            print(query.decode())
            # if client sent an empty packet, close the connection and handle the next one.
            if query.decode() == "":
                connection_type = "close"
                client_socket.close()
                continue
        except socket.timeout:
            client_socket.close()
            continue
        # separate the lines by new line char.
        lines = (query.decode()).split("\r\n")
        # extract file path from GET line.
        file_path = extract_file_path(lines)
        # if an empty file name was inserted, return index.html.
        if file_path == "/":
            file_path += "index.html"
        # if the client requests to redirect, return result.html.
        if file_path == "/redirect":
            handle_redirect(client_socket)
            continue
        # remove "/" from the beginning of the file name.
        file_path = file_path[1:]
        # navigate to the "files" folder.
        path = os.path.dirname(__file__)
        os.chdir(path + "/files")
        # if the requested file name wasn't found, return 404 not found error page.
        if not file_exists(file_path):
            handle_not_found(client_socket)
            continue
        # find the connection line, and extract to connection type from it.
        connection_type = extract_connection_type(lines)
        # use the relevant function to send the file.
        if extract_file_type(file_path) == "ico" or extract_file_type(file_path) == "jpg":
            send_jpg_ico(client_socket, file_path, connection_type)
        else:
            send_file(client_socket, file_path, connection_type)
        # if connection type is "close", close the socket to accept a new connection.
        if connection_type == "close":
            client_socket.close()


def initialize_server(port):
    # create a tcp socket.
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # accept all IP addresses, and use the command line arg as port number.
    server_ip = '0.0.0.0'
    server_port = int(port)
    server.bind((server_ip, server_port))
    # accept 1 client at a time.
    server.listen(1)
    # initialize client's parameters.
    connection_type = "close"
    client_socket = 0
    client_address = 0
    return server, connection_type, client_socket, client_address


def extract_file_path(lines):
    # skip irrelevant lines.
    i = 0
    while (lines[i].split(" "))[0] != "GET":
        i += 1
    # extract file name from GET line.
    file_path = (lines[i].split(" "))[1]
    return file_path


def extract_file_type(file_path):
    # file_path format is: "/.../file_name". split it and take the last part to extract file name.
    file_name = (file_path.split("/"))
    file_name = file_name[len(file_name) - 1]
    # extract file type from file name.
    file_type = file_name.split(".")[1]
    return file_type


def extract_connection_type(lines):
    connection_type = ""
    # find the connection line.
    for line in lines:
        line = line.split(" ")
        if line[0] == "Connection:":
            # extract the connection type.
            connection_type = line[1]
    return connection_type


def file_exists(file_path):
    # if file open (for reading) succeed, return true. else, return false.
    try:
        open(file_path, "r")
        return True
    except IOError:
        return False


def handle_redirect(client_socket):
    # if client requests to redirect, navigate to "result.html" as defined.
    message = "HTTP/1.1 301 Moved Permanently\r\n"
    message += "Connection: close\r\n"
    message += "Location: /result.html\r\n\r\n"
    client_socket.send(message.encode())
    client_socket.close()


def handle_not_found(client_socket):
    # if client requests a file which does not exist, return 404 page as defined.
    message = "HTTP/1.1 404 Not Found\r\n"
    message += "Connection: close\r\n\r\n"
    client_socket.send(message.encode())
    client_socket.close()


def send_file(client_socket, file_path, connection_type):
    # read the file to the buffer.
    buffer = ""
    f = open(file_path, 'r')
    temp = f.read(2048)
    while temp:
        buffer += temp
        temp = f.read(2048)
    f.close()
    # send the details of the file to the client.
    message = "HTTP/1.1 200 OK\r\n"
    message += ("Connection: " + connection_type + "\r\n")
    message += ("Content-Length: " + str(len(buffer)) + "\r\n")
    message += "\r\n"
    message += buffer
    message += "\r\n\r\n"
    client_socket.send(message.encode())


def send_jpg_ico(client_socket, file_path, connection_type):
    # get the file's size in bytes.
    file_size = os.path.getsize(file_path)
    # send the file's details to the client.
    message = "HTTP/1.1 200 OK\r\n"
    message += ("Connection: " + connection_type + "\r\n")
    message += ("Content-Length: " + str(file_size) + "\r\n")
    message += "\r\n"
    client_socket.send(message.encode())
    # read the file as bytes to var temp, and send the bytes straight to the client.
    f = open(file_path, 'rb')
    temp = f.read(2048)
    while temp:
        client_socket.send(temp)
        temp = f.read(2048)
    client_socket.send("\r\n\r\n".encode())
    f.close()


main()
