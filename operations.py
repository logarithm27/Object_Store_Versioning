from database import *
import os
import ntpath
import platform
import posixpath
import macpath

MAX_ver = 100

class Policy():
    Global = 1
    Dynamic = 2

class Operations :
    def __init__(self):
        self.db = Database()
        self.db.connect_db()
        self.remote_or_local = "from_local"
        self.transfer_mode = 1

    #Create object
    def put(self,object_name,path,max_obj=MAX_ver,policy=Policy.Global):
        path_to_content, content_name = ["",""]
        # if we operate with client-server, we will not test if the path exists ( the client should do it)
        if (os.path.exists(path) and self.remote_or_local.__eq__("from_local")) or self.remote_or_local.__eq__("from_server"):
            # removing last slash or backslash so the content_name won't be empty in the db using rstrip
            # split the path into file or directory name and its path
            if platform.system().__eq__("Windows"):
                path_to_content, content_name = ntpath.split(path.rstrip('/'))
            elif platform.system().__eq__("Linux"):
                path_to_content, content_name = posixpath.split(path.rstrip('/'))
            elif platform.system().__eq__("Darwin"):
                path_to_content, content_name = macpath.split(path.rstrip('/'))
            # the function takes the object name, the path of the file that contains the content,
            # the name of the content itself and the function that verifies if the objects exists already or not
            return self.db.create_object(object_name,self.db.conn,path_to_content,content_name,self.db.object_name_exists(object_name,self.db.conn),max_obj,policy)
        elif (not os.path.exists(path)) and self.remote_or_local.__eq__("from_local"):
            return "Wrong Path"
        return None

    #Get an object
    def get(self,object_name,path, version=None):
        # the path shouldn't be a file because the get must store the object as a new file
        if (not os.path.exists(path) or os.path.isfile(path)) and self.remote_or_local.__eq__("from_local"):
            return "Wrong Path"
        else :
            # change condition if we operate with client-server or in local machine
            condition = None
            if self.remote_or_local.__eq__("from_server"):
                condition = os.path.isdir(path) or self.remote_or_local.__eq__("from_server")
            elif self.remote_or_local.__eq__("from_local"):
                condition = os.path.isdir(path)
            if condition:
                # if the object name exists
                if self.db.object_name_exists(object_name,self.db.conn):
                    # if the version is not None and exists (by default the user will get the last version)
                    if (get_data := self.db.get_version(object_name,self.db.conn,version)) is not None:
                        # create object as new text file
                        # get the last attribute of the Versions' table which is the name of the object
                        # and set it as the name of the file the will be written
                        crt_obj_as_file = open(os.path.join(path,(str(get_data[-1])+".txt")),"w")
                        # get all attributes' data except the object name
                        version_, content_names,content_paths = get_data[0:len(get_data) - 1]
                        contents =  list(map(lambda x, y: os.path.join(x,y), content_paths.split(";"), content_names.split(";")[0:-1]))
                        # write into the object's file the data and the attributes of the data to be readable
                        # use | as a separator instead of comma and removing parenthesis got from db fetched data
                        #.format is used to write multiple lines
                        crt_obj_as_file.write("{:<15}{:>15}".format("Version", "Contents\n"))
                        crt_obj_as_file.write(f"{version_}\n")
                        for content in contents:
                            crt_obj_as_file.write("{:<20}{:>18}".format("",content + "\n"))
                        # close the file
                        crt_obj_as_file.close()
                        if self.transfer_mode == 2:
                            return (os.path.join(path,(str(get_data[-1])+".txt")))
                        # if transfer mode is without transfer
                        if self.transfer_mode == 1:
                            return "The GET file is made and ready!"
                        return "The GET file is made and ready!"
                else:
                    return "Object not Found"

    # Delete an object
    def delete(self,object_name, version=None):
        if self.db.object_name_exists(object_name, self.db.conn):
            return self.db.delete_obj(object_name,self.db.conn,version)
        else:
            return f"Object {object_name} not found"

    # listing objects
    # if the object name is specified by the user then it shows only objects
    # else, it will show all versions of the given object
    def list(self, object_name=None):
        return self.db.get_objects_versions(self.db.conn,object_name)