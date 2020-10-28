import os
import sqlite3
from sqlite3 import Error

# global variable that creates a working directory where we can store the database file
current_working_directory = os.getcwd()
# sqlite3 database file name
db_file_name = "/drive.db"


# database creation and connection
class Database:
    def __init__(self):
        self.conn = None

    def connect_db(self):
        # if database file doesn't exist, create new one and create database from scratch then connect
        if not os.path.exists(db_file := str(current_working_directory) + db_file_name):
            print(db_file)
            open(db_file, 'w').close()
            self.conn = self.create_connection(db_file)
            self.create_db_tables(self.conn)

        # else, simply connect to db
        else:
            self.conn = self.create_connection(db_file)

    def create_connection(self, db_file):
        connection = None
        try:
            connection = sqlite3.connect(db_file)
            print(f"connected with {sqlite3.version}")
            return connection
        except Error as error:
            print(error)
        return connection

    # create necessary tables for our object storage inside the database
    def create_db_tables(self, connection):
        objects_table = """ CREATE TABLE IF NOT EXISTS Objects (
                                        o_name text NOT NULL PRIMARY KEY,
                                        Max_versions INTEGER,
                                        Policy INTEGER); """

        # Version table contains the version(the number of the version auto incremented each time a new version comes)
        # content : the name of the content
        # content_path : the path of the file or directory that contains the object_data

        versions_table = """ CREATE TABLE IF NOT EXISTS Versions (
                                        ID integer PRIMARY KEY,
                                        version integer ,
                                        content_name text NOT NULL, 
                                        content_path text NOT NULL); """
        # Create foreign key constraint that references the Versions' o_name to the Objects' o_name
        object_versions_fk = """ ALTER TABLE Versions ADD COLUMN o_name text REFERENCES Objects(o_name); """
        if connection is not None:
            try:
                c = connection.cursor()
                c.execute(objects_table)
                c.execute(versions_table)
                c.execute(object_versions_fk)
                print("database created")
            except Error as error:
                print(error)

    # test if a certain object_name already exists
    def object_name_exists(self, object_name, c):
        cursor = c.cursor()
        search_for_object_name = """ SELECT * FROM Objects WHERE o_name=? """
        cursor.execute(search_for_object_name, (object_name,))
        if (data := cursor.fetchone()) is not None:
            print(f"The Object '{data[0]}' exists")
            return True
        print("Object not found")
        return False

    # get version of an object
    def get_version(self, object_name, c, version=None):
        cursor = c.cursor()
        # by default, version parameter is optional
        # if the version is not specified by the user, the latter will get the latest version of the object
        if version is None:
            get_last_version = """ SELECT version, content_name, content_path, o_name 
                                   FROM Versions 
                                   WHERE o_name=? and version = (SELECT MAX(version) from Versions)"""
            cursor.execute(get_last_version, (object_name,))
            fetched_data = cursor.fetchone()
            return fetched_data
        else:
            get_requested_version = """ SELECT version, content_name, content_path, o_name 
                                        FROM Versions 
                                        WHERE o_name=? and version =?"""
            cursor.execute(get_requested_version, (object_name, version,))
            fetched_data = cursor.fetchone()
            # if the version requested by the user don't exist, return nothing
            if fetched_data is None:
                print(f"This version : {str(version)} don't exist")
                return None
            else:
                return fetched_data

    # it creates an object in the database
    # the exists parameters is boolean that indicates whether the objects exists in the db or not
    def create_object(self, object_name, c, path, content_name, exists, MAX_Ver, policy):
        cursor = c.cursor()
        create_version = """ INSERT INTO Versions (version,content_name, content_path, o_name) 
                             VALUES(?,?,?,?)"""
        if not exists:
            create_new_object = """INSERT INTO Objects Values (?,?,?)"""
            cursor.execute(create_new_object, (object_name, MAX_Ver, policy))
            # the object is new and have only one version (the first version)
            # add ";" as a separator (in order to separate further contents names and paths on future versions)
            cursor.execute(create_version, (1, content_name+";", path+";", object_name))
            c.commit()
            return "New Object created"
        else:
            # get number of versions
            cursor.execute('''SELECT count(o_name) FROM Versions WHERE o_name=?''', (object_name,))
            number_of_versions = cursor.fetchone()[0]
            # get the max number of versions allowed to be stored that corresponds to the object
            cursor.execute('''SELECT Max_versions FROM Objects WHERE o_name=?''',(object_name,))
            max_versions = cursor.fetchone()[0]
            # if it exceeds the max number of versions set up by the program(by default) or by the user
            if number_of_versions >= max_versions:
                # we should now the policy used to manage the object
                cursor.execute('''SELECT policy FROM Objects WHERE o_name=?''', (object_name,))
                policy = cursor.fetchone()[0]
                # if the policy is global, we delete the oldest version
                if policy == 1:
                    oldest_version = ''' Select min(version) from versions where o_name=?'''
                    cursor.execute(oldest_version, (object_name,))
                    oldest_version = cursor.fetchone()[0]
                    self.delete_obj(object_name, c, oldest_version)
                # if its dynamic policy, whenever we add a new version, we delete 25% of the oldest versions
                elif policy == 2:
                    delete_quarter = ''' DELETE FROM Versions 
                                         WHERE version 
                                         IN (
                                            SELECT version 
                                            FROM Versions 
                                            WHERE o_name=? 
                                            ORDER BY version ASC LIMIT ?);'''
                    quarter_of_versions = number_of_versions / 4
                    cursor.execute(delete_quarter, (object_name, quarter_of_versions))
                    c.commit()
            # get the number of previous latest version of object and adding one to it
            last_version = ''' Select max(version) from versions where o_name=?'''
            cursor.execute(last_version, (object_name,))
            last_version = cursor.fetchone()
            last_version = last_version[0] + 1
            # get the content names and content paths of the object from previous version
            # plus the current content name and content path added
            content_n, paths = self.add_or_replace_paths_for_new_version(object_name,self.conn,path,content_name)
            cursor.execute(create_version, (last_version, content_n, paths, object_name))
            c.commit()
            return "New Version of the object created"


    # the version parameter is optional
    def delete_obj(self, object_name, c, version=None):
        cursor = c.cursor()
        del_all_versions = """Delete From Versions Where o_name=?"""
        del_obj = """Delete From Objects Where o_name=?"""
        # the user can specify a version, and the latter could be the only version existing
        # if its the case we skip to else and
        # so we delete the version and the object from the Objects table
        cursor.execute('''SELECT count(o_name) from Versions where o_name =?''', (object_name,))
        # if version is specified by user and exists and there is more than 1 version
        v_exist = self.get_version(object_name, c, version)
        if (version is not None) and (v_exist) is not None and (cursor.fetchone()[0] > 1):
            del_version = """DELETE FROM Versions WHERE o_name=? and version=?"""
            cursor.execute(del_version, (object_name, version))
            c.commit()
            return f"Version {str(version)} deleted"
        # if the version don't exist
        elif v_exist is None:
            return "Version not found"
        else:
            cursor.execute(del_all_versions, (object_name,))
            cursor.execute(del_obj, (object_name,))
            c.commit()
            return "Object Deleted"

    # listing objects or objects' versions
    # object name is optional
    def get_objects_versions(self, c, object_name=None):
        cursor = c.cursor()
        # if object name is not specified then list all existing object
        # else list all object's versions
        if object_name is not None:
            if self.object_name_exists(object_name, c):
                get_all_versions_of_objects = '''SELECT version,content_name,content_path FROM Versions where o_name=?'''
                cursor.execute(get_all_versions_of_objects, (object_name,))
                return cursor.fetchall()
            else :
                return "Object not found"
        else:
            get_all_objets = '''SELECT o_name FROM Objects'''
            cursor.execute(get_all_objets)
            return cursor.fetchall()

    # this function gets the latest version
    # and compares the content's name and path of the current version that is being created with the last version
    def add_or_replace_paths_for_new_version(self,object_name,c,path,content_name):
        cursor = c.cursor()
        # get content's name and path from the last version of the object
        last_version = '''SELECT content_name, content_path 
                          From Versions 
                          WHERE 
                          o_name=?
                          AND 
                          version=
                                    (SELECT MAX(version) 
                                    FROM Versions)'''
        cursor.execute(last_version, (object_name,))
        fetched_data = list(cursor.fetchone())
        # all contents are separated by semicolons, so we remove it
        # and each path/content name will be an element of a list
        # when we remove the semicolon, the last element of the array is empty, so we remove the last element
        content_names = fetched_data[0].split(";")[0:-1]
        content_paths = fetched_data[1].split(";")[0:-1]
        # for each element name in the latest version
        for index,c_name in enumerate(content_names):
            # if the content name given by the user is already existing(latest version)
            if content_name.lower().__eq__(c_name.lower()):
                # the name of the content remains the same, but the path change ( overwriting the content )
                content_paths[index]=path
                break
        # # if the content name given by the user is not existing
        if content_name not in content_names :
            # we add the new content name and path with the others from the latest version
            content_names.append(content_name)
            content_paths.append(path)
        # we convert lists to strings and we join them by making semicolons separators
        # in order to execute it with SQL query
        content_names = ";".join(content_names)+";"
        content_paths = ";".join(content_paths)+";"
        # we return content names and content paths that will be in the new version of the object
        return [content_names,content_paths]