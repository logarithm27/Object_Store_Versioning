from operations import *
from menu import *
'''
TO TEST THE OPERATIONS ENGINE IN LOCAL SYSTEM, USE THIS FILE
TO TEST THE ENGINE WITH CLIENT SERVER, RUN THE server.py then client.py 
'''

def run():
    op = Operations()
    m = Menu()
    input_command = m.printing()
    input_command = input_command.split(' ')
    print(len(input_command[1:]))
    # if put
    if m.val.__eq__("1"):
        object_name, path = input_command[1:3]
        if len(input_command[1:]) == 4:
            max_versions, policy = input_command[3:]
            print(op.put(object_name, path, int(max_versions), int(policy)))
        if len(input_command[1:]) == 3:
            max_versions = input_command[3]
            print(op.put(object_name, path, int(max_versions)))
        if len(input_command[1:]) == 2:
            object_name, path = input_command[1:]
            print(op.put(object_name, path))
    # if get
    if m.val.__eq__("2"):
        if len(input_command[1:]) == 3:
            object_name, path, version = input_command[1:]
            print(op.get(object_name, path, int(version)))
        else:
            object_name, path = input_command[1:]
            print(op.get(object_name, path))


    if m.val.__eq__("3"):
        if len(input_command[1:]) == 1:
            object_name = input_command[1]
            print(object_name)
            print(op.delete(object_name))
        if len(input_command[1:]) == 2:
            object_name, version = input_command[1:]
            print(op.delete(object_name, int(version)))

    if m.val.__eq__("4"):
        list_ = None
        if len(input_command[1:]) == 1:
            object_name = input_command[1]
            list_ = op.list(object_name)
        else:
            list_ = op.list()
        if list_ == "Object not found":
            print("Object not found")
        else:
            for element in list_:
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
    quit_or_not = m.quit()
    if quit_or_not:
        pass
    elif not quit_or_not:
        run()

run()

