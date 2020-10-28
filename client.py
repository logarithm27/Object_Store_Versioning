import socket
from menu import *
import pickle
import os

''' I write some few comments here 
because I have already mentioned it in the server file
since the latter contains some symmetric functions '''

ADDR_PORT = (socket.gethostbyname(socket.gethostname()),1234)
FORMAT = 'utf-8'
HEADER_SIZE = 16
QUIT_MESSAGE = 'quit'
FILE_TRANSFER_ACTIVATED_MSG = "File transfer Activated"
ST_MODE_W_T = "Storage mode with transfer activated "
ST_MODE_WITHOUT_T = "Storage mode without transfer activated "
SEND_CLIENT_TO_SERVER = "PUT FILE : TRANSFER FROM CLIENT TO SERVER"
SEND_SERVER_TO_CLIENT = "GET FILE : TRANSFER FROM SERVER TO CLIENT"
CONTINUE = "CONTINUE"

class Client:
    def __init__(self):
        # create client
        self.client_socket = socket.create_connection(ADDR_PORT)
        self.start_client()

    def start_client(self):
        self.menu = Menu()
        # select the storage mode
        self.storage_mode = self.menu.storage_mode()
        # to store the response got from the server
        self.resp = None
        # send the storage mode chose by user
        self.send_msg_to_server(self.storage_mode)
        self.resp = self.receive_ack_from_server()
        # print for debug
        print(self.resp)
        # checking paths if the given command is PUT or GET
        self.command_operation = self.path_checker(self.menu.printing())
        # send the command the the server
        self.send_msg_to_server(self.command_operation)
        # get response from server to know further steps to take
        self.resp = self.receive_ack_from_server()
        # if the server requested a file ( in case of put command ( with transfer mode ) )
        if self.resp == SEND_CLIENT_TO_SERVER:
            self.send_file_through_network(self.command_operation)
            print(self.receive_ack_from_server())
        # if the server will a file ( in case of get command ( with transfer mode ) )
        if self.resp == SEND_SERVER_TO_CLIENT:
            self.send_msg_to_server('')
            self.receive_file_from_server(self.command_operation.split(' ')[1])
        # if the input contains the command list
        elif self.command_operation.split(' ')[0] == "list":
            # since listing depends on whether the user have mentioned the name of the object or not
            # we call the listing method to do so
            self.listing(self.resp)
        # if the input contains the delete operation
        elif self.command_operation.split(' ')[0] == "delete":
            print(self.resp)
        else:
            print(self.resp)
        # demanding to user if he wants to quit or continue after the command have been achieved
        quit_or_repeat = self.menu.quit()
        # if chose to quit
        if quit_or_repeat:
            # send quit message to server
            self.send_msg_to_server(QUIT_MESSAGE)
            # close connection
            self.client_socket.close()
        # else, repeat
        elif not quit_or_repeat:
            self.send_msg_to_server(CONTINUE)
            self.start_client()

    # check if a given path is valid depending on the given command
    def path_checker(self,command):
        if command.split(' ')[0].lower() == "get":
            while (not os.path.exists(command.split(' ')[2]) or
                   not os.path.isdir(command.split(' ')[2])):
                print("Invalid path, try again : ")
                command = input()
        if command.split(' ')[0].lower() == "put":
            while (not os.path.exists(command.split(' ')[2])):
                print("Invalid path, try again : ")
                command = input()
        return command

    # listing objects or version of objects
    def listing(self, listing_response):
        if listing_response == "Object not found":
            print("Object not found")
        else :
            for element in listing_response:
                # if we have retrieved versions of objects
                if len(element) > 1:
                    version = element[0]
                    # element[1] is the content name and element[2] is the path
                    content = list(
                        map(lambda x, y: os.path.join(x, y), element[2].split(";")[0:-1], element[1].split(";")[0:-1]))
                    print(f"Version {str(version)} contains :")
                    for c in content:
                        print("\t" + c)
                # if we have retrieved objects
                else:
                    print(f"Object {element[0]}")

    def receive_ack_from_server(self):
        receiving_response = True
        response_length = 0
        i = 0
        while receiving_response:
            response_from_server = self.client_socket.recv(HEADER_SIZE)
            if i == 0 and response_from_server:
                response_length = int(response_from_server)
            i += 1
            full_response = pickle.loads(self.client_socket.recv(response_length))
            return full_response

    def send_msg_to_server(self, message):
        message_to_send = pickle.dumps(message)
        message_to_send = bytes(f'{len(message_to_send):<{HEADER_SIZE}}', FORMAT) + message_to_send
        self.client_socket.send(message_to_send)

    def receive_file_from_server(self, file_name):
        cwr = os.getcwd()
        receiving_response = True
        response_length = 0
        i = 0
        while receiving_response:
            receive_file_from_server = self.client_socket.recv(HEADER_SIZE)
            if i == 0 and receive_file_from_server:
                response_length = int(receive_file_from_server)
            i += 1
            full_response = pickle.loads(self.client_socket.recv(response_length))
            receiving_response = False
        path_given_in_get_command = self.command_operation.split(' ')[2]
        with open(os.path.join(str(path_given_in_get_command), file_name+".txt"), "wb") as f:
            print('writing...')
            for chunk in full_response:
                f.write(chunk)
        print('writing finished')
        print(f"File received successfully via GET command on {str(os.path.join(str(path_given_in_get_command), file_name))}")
        return str(os.path.join(str(cwr), file_name))

    def send_file_through_network(self,command):
        path = command.split(' ')[2]
        file_data = []
        with open(path, "rb") as f:
            print('reading ...')
            while True:
                binary_data_read = f.read(1024)
                file_data.append(binary_data_read)
                if not binary_data_read:
                    break
        file_data_to_send = pickle.dumps(file_data)
        file_data_to_send = bytes(f'{len(file_data_to_send):<{HEADER_SIZE}}', FORMAT) + file_data_to_send
        print('reading finished')
        self.client_socket.send(file_data_to_send)

c = Client()









