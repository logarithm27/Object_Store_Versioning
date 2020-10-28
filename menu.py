class Menu:
    def __init__(self):
        self.store_mode = ""
        self.val = None
        self.quit_choice = False

    # to select the storage mode in case we are dealing with a client-server
    def storage_mode(self):
        print("Select storage mode : ")
        print("1- Without Transfer (You must ensure access to your computer)")
        print("2- With Transfer (transfer files through network, ensure you are connected with endpoint)")
        self.store_mode = input("Please choose between 1 and 2 : ")
        while not self.store_mode:
            self.store_mode = input("Invalid! try again ")
        return str(self.store_mode)

    # print the choice menu
    def printing(self):
        print("Welcome to object store versioning : ")
        print("1- PUT : takes object name, and content's path\n")
        print("2- GET : takes also object name, and destination path \n")
        print("3- DELETE : by mentioning object name, and optional version\n ")
        print("4- LIST : lists all objects, if you specify the object name, it lists all of its versions\n")
        self.val = input("please choose a command (1 to 4):\n ")
        if self.val.__eq__(str(1)):
            print("the PUT command should be as follow : ")
            print("put <object_name> <path> <number_of_max_objects> <policy>")
            print("note that the number of max objects and policy are optionals")
            print("by default, number of max objects is 100 ")
            print("by default, the policy is 1 (Global), put 2 if you want to change to Dynamic\n")
        if self.val.__eq__(str(2)):
            print("the GET command should be as follow : ")
            print("get <object_name> <path> <version> ")
            print("the version is optional\n")
        if self.val.__eq__(str(3)):
            print("the DELETE command should be as follow : ")
            print("delete <object_name> <version>")
            print("the version is optional, if not specified, the whole object will be deleted\n")
        if self.val.__eq__(str(4)):
            print("the List command should be as follow : ")
            print("list <object_name>")
            print("the object_name is optional, if you specify the latter, it will list all object's versions\n")
        input_command = input()

        # check if the user gave an empty input
        while not input_command:
            print("invalid command")
            input_command = input()
        # check if the input is consistent with the choice
        if input_command:
            if self.val == str(1):
                input_ = self.input_checker(3, 5, "put", input_command)
            if self.val == str(2):
                input_ = self.input_checker(3, 4, "get", input_command)
            if self.val == str(3):
                input_ = self.input_checker(2, 3, "delete", input_command)
            if self.val == str(4):
                input_ = self.input_checker(1, 2, "list", input_command)
        return input_

    # quit menu in order to know whether the user wants to continue or to quit
    def quit(self):
        quit_menu = input("Do you want to quit Y/N : ")
        if quit_menu.lower().__eq__("y"):
            return True
        else:
            return False

    # check the given command
    # every command have its necessary arguments and optional arguments
    # depending on the command, this method checks if the input don't have more or less
    # arguments than it normally takes
    def input_checker(self,arg_min_number, argmax_number, command,input_):
        input_1 = input_
        while len(input_1.split(' ')) > argmax_number or len(input_1.split(' ')) < arg_min_number:
            print(f"invalid command, takes {arg_min_number} or {argmax_number} arguments and got {len(input_1.split(' '))} instead")
            input_1 = input()
        while ((command not in input_1.split(' ') or not command.__eq__(input_1.split(' ')[0]))):
            print("invalid input try again")
            input_1 = input()
        return input_1