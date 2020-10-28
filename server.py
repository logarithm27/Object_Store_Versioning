import socket
from operations import *
import threading
import pickle

# get the host address by its hostname and set a port
ADDR_PORT = (socket.gethostbyname(socket.gethostname()), 1234)
# used as flag to listening to clients
LISTENING = True
# the format of encoding when we receive/retrieve data with client
FORMAT = 'utf-8'
# the header size by which we know how many chunks of bytes we will send/receive
HEADER_SIZE = 16
# the quit message if the user decided to quit
QUIT_MESSAGE = 'quit'
# message to send to client if the client is about to send a file to the server
SEND_CLIENT_TO_SERVER = "PUT FILE : TRANSFER FROM CLIENT TO SERVER"
# same as the previous in inverse way
SEND_SERVER_TO_CLIENT = "GET FILE : TRANSFER FROM SERVER TO CLIENT"
# acknowledge message to send to client about which storage mode has been created
ST_MODE_W_T = "Storage mode with transfer activated "
ST_MODE_WITHOUT_T = "Storage mode without transfer activated "
# continue message if the user wants to maintain connection with server
CONTINUE = "CONTINUE"

class Server:
    def __init__(self):
        # init server
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(ADDR_PORT)
        self.server.listen()
        # flag to test if we are already connected with a client
        self.cnt_with_client = False
        while LISTENING:
            # if not connected with a client, accept further connection with clients
            if not self.cnt_with_client:
                print("Waiting for a client to connect ...")
                self.client_socket, self.client_address = self.server.accept()
            # to store the command received from the client user
            self.command = ""
            # initialise the operations engine
            self.op = Operations()
            # to store response received from client during the connection
            self.resp = None
            # to store the storage mode chosen by  user
            self.transfer_mode = ""
            # to store the content/file name given in the put command (from the client)
            # will be used only in storage mode with transfer
            self.put_file_name = ""
            # to store the path where the file is saved in the server's local system
            # also it's used only in storage mode with transfer
            self.new_put_path = ""
            # to store the path where the user have chosen to save its get file
            # used in case of storage mode with transfer is activated
            self.client_get_path = ""
            # receive the first message from the client
            # it will be the storage mode chose by the user in the client console
            self.resp = self.receive_response_from_client()
            # for debug (printing the storage mode)
            print(self.resp)
            # if the storage mode is 2
            if self.resp.__eq__("2"):
                # set the transfer mode to 'storage with transfer'
                self.transfer_mode = "2"
                # set the transfer mode in the operation's engine to 2
                # because its output will depends in this variable for some commands
                self.op.transfer_mode = 2
                # send to client that the server is acknowledged about the transfer mode
                self.send_acknowledge(ST_MODE_W_T)
            # if the storage mode is 1 ( do the same as we have done with storage mode 2)
            elif self.resp.__eq__("1"):
                self.transfer_mode = "1"
                # tell the operations engine that we will operate remotely
                # in order to tell to the server that it have access to the clients' contents
                self.op.remote_or_local = "from_server"
                self.send_acknowledge(ST_MODE_WITHOUT_T)
            # get back the command from the client
            self.resp = self.receive_response_from_client()
            # convert the command to a list to distinguish the command itself and its arguments
            self.command = self.resp.split(' ')
            # perform the operation requested by the client
            self.perform_operation_with_transfer_mode()
            self.resp = self.receive_response_from_client()
            if self.resp.__eq__(QUIT_MESSAGE):
                print('Disconnected from the client ')
                self.cnt_with_client = False
                self.client_socket.close()
            if self.resp.__eq__(CONTINUE):
                self.cnt_with_client = True

    # self.send_receive(client_socket,client_address)
    def perform_operation_with_transfer_mode(self):
        # if the command is a "put" and the storage is with transfer
        if self.command[0] == "put":
            if self.transfer_mode == "2":
                # get the put file name given by the client in the input
                # the path is always the third element in the after splitting the command into a list
                self.put_file_name = ntpath.split(self.command[2].rstrip('/'))[1]
                # send to the client that the server is about to send a file to it
                # so the client will be prepared
                self.send_acknowledge(SEND_CLIENT_TO_SERVER)
                # after receiving file from the client, it will be stored in the server
                # so we get its path inside the server
                self.new_put_path = self.receive_file_from_client(self.put_file_name)
                # we still have the old file's path (of the client, which the server can't access to it)
                # so we set the path inside the server as the new path of the file
                self.command[2] = self.new_put_path
                # we perform the put, and we store our object in the database (which is in the server)
                ack = self.server_put(self.command, self.op)
                # we send to the client information about the performed command put
                self.send_acknowledge(ack)
            # if the transfer mode is 1, then the server have access to the clients files
            # so we perform the put operation normally
            elif self.transfer_mode == "1":
                ack = self.server_put(self.command, self.op)
                self.send_acknowledge(ack)
        # if the command is get and transfer mode is 2
        if self.command[0] == "get":
            if self.transfer_mode == "2":
                # we store the path (where to store the object) given by client
                self.client_get_path = self.command[2]
                # we modify the path and we set it as the current directory (where the server is being executed)
                self.command[2] = os.getcwd()
                # perform the get operation inside the engine
                # we get the path where the object is stored in the server
                path_of_get_file_in_server = self.server_get(self.command, self.op)
                # if the object name is found and the file was created
                if path_of_get_file_in_server != "Object not Found":
                    # let the client to know
                    self.send_acknowledge(SEND_SERVER_TO_CLIENT)
                    self.receive_response_from_client()
                    # send that file to the client
                    self.send_file_through_network(path_of_get_file_in_server)
                # if the object requested by the the client was not found by the engine
                else:
                    self.send_acknowledge("Object not Found")
            # perform get command normally if the storage is without transfer
            if self.transfer_mode == "1":
                ack = self.server_get(self.command, self.op)
                self.send_acknowledge(ack)
        # perform delete and list commands whatever the storage mode is
        if self.command[0] == "delete":
            ack = self.server_delete(self.command, self.op)
            self.send_acknowledge(ack)
        if self.command[0] == "list":
            ack = self.server_list(self.command, self.op)
            self.send_acknowledge(ack)

    # delete command
    def server_delete(self, received_command, operation):
        acknowledge = ''
        # test if the input contains 2 elements (the command and its first optional argument)
        # we do the same with all the operations and depending to each one
        if len(received_command[1:]) == 1:
            object_name = received_command[1]
            acknowledge = operation.delete(object_name)
        # test if the input contains 3 elements (the command and its two optional arguments)
        if len(received_command[1:]) == 2:
            object_name, version = received_command[1:]
            acknowledge = operation.delete(object_name, int(version))
        return acknowledge

    # get command
    def server_get(self, received_command, operation):
        if len(received_command[1:]) == 3:
            object_name, path, version = received_command[1:]
            acknowledge = operation.get(object_name, path, int(version))
        else:
            object_name, path = received_command[1:]
            acknowledge = operation.get(object_name, path)
        return acknowledge

    # put command
    def server_put(self, received_command, operation):
        acknowledge = ''
        # get the 2 necessary arguments (object_name and path)
        object_name, path = received_command[1:3]
        # if the storing is with transfer :
        # if the put command got 4 arguments from the user
        if len(received_command[1:]) == 4:
            # take the 2 last arguments
            max_versions, policy = received_command[3:]
            acknowledge = operation.put(object_name, path, int(max_versions), int(policy))
        # if the put command got 3 arguments
        if len(received_command[1:]) == 3:
            # take the third optional argument
            max_versions = received_command[3]
            acknowledge = operation.put(object_name, path, int(max_versions))
        if len(received_command[1:]) == 2:
            object_name, path = received_command[1:]
            acknowledge = operation.put(object_name, path)
        return acknowledge

    # listing
    def server_list(self, received_command, operation):
        if len(received_command[1:]) == 1:
            object_name = received_command[1]
            return operation.list(object_name)
        else:
            return operation.list()

    # send a message through network
    # takes the message as argument
    def send_acknowledge(self, acknowledge):
        # using pickle, we can transform anything (object, string, dict...) to a byte stream
        # we use dumps to serialize the message and transform it to a format where it can be easily reconstructed in the client
        acknowledge_to_send = pickle.dumps(acknowledge)
        # we insert with the serialized message its length,
        # followed by a large space alignment to the right that have the size of the header_size, then followed
        # by the message to send
        # so the client will know at the first reception the length of the message because its stored at the first
        # and then can quickly loads it
        acknowledge_to_send = bytes(f'{len(acknowledge_to_send):<{HEADER_SIZE}}', FORMAT) + acknowledge_to_send
        # send the message to the client
        self.client_socket.send(acknowledge_to_send)

    # to receive a message from the client
    def receive_response_from_client(self):
        receiving_response = True
        response_length = 0
        i = 0
        while receiving_response:
            # receive the first HEADER_SIZE bytes chunk of data
            # the first chunk contains surely the length of the message and spaces
            # example 84______________
            response_from_server = self.client_socket.recv(HEADER_SIZE)
            if i == 0 and response_from_server:
                # we convert the length of the message to int
                response_length = int(response_from_server)
            i += 1
            # we de-serialize and get the entire message by giving the full message length to the recv method
            full_response = pickle.loads(self.client_socket.recv(response_length))
            # we return the message
            return full_response

    # receive file (used in the case of get operation performed)
    def receive_file_from_client(self, file_name):
        # store the file got from the client in the current directory
        cwr = os.getcwd()
        receiving_response = True
        response_length = 0
        i = 0
        # pickle is powerful, so we can receive the file data as a list consisting of binary data elements
        while receiving_response:
            receive_file_from_client = self.client_socket.recv(HEADER_SIZE)
            if i == 0 and receive_file_from_client:
                response_length = int(receive_file_from_client)
            i += 1
            full_response = pickle.loads(self.client_socket.recv(response_length))
            receiving_response = False
        # open the file in write binary mode after receiving all the file data
        with open(os.path.join(str(cwr), file_name), "wb") as f:
            print('writing...')
            # for each binary data element in the list of that stores all files data
            for chunk in full_response:
                # write that data into the file
                f.write(chunk)
        print(f'File received to server and placed on {str(os.path.join(str(cwr), file_name))}')
        return str(os.path.join(str(cwr), file_name))

    # send file to the client
    def send_file_through_network(self,path):
        # initialize the list that stores the files data
        file_data = []
        # open the file in read binary mode
        with open(path, "rb") as f:
            print('reading file data ...')
            while True:
                # read 1024 bytes of file's binary data and store it as an element in the list
                binary_data_read = f.read(1024)
                file_data.append(binary_data_read)
                # if there is no more data to read exit
                if not binary_data_read:
                    break
        # convert list to stream of bytes and serialize it
        file_data_to_send = pickle.dumps(file_data)
        file_data_to_send = bytes(f'{len(file_data_to_send):<{HEADER_SIZE}}', FORMAT) + file_data_to_send
        print('File data sent to client')
        # send the list
        self.client_socket.send(file_data_to_send)

Server()
