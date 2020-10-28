# Home Made Object Versioning
Like Amazon S3 Object Versioning, this Python program is able to create objects and making versions of it. 
# What is it ?
This python program implements an object storage system by which we can perform the following actions : 
1. PUT (creation of an object) : By giving the name of the object and a file's path that contains the data of the object.
2. GET (requesting an object) : By mentioning the object's name followed by the path where we will store the retreived object.
3. DELETE (for deleting an object) : By mentioning the object's name.
4. LIST (to lists objects or versions of an object) : The user is able to see all the existing objects or all the object's versions if he mentioned the object's name.
# Functionnalities of Object Versioning 
-The objects meta-data are stored in a SQLITE3 Database.
-We can store multiple versions of the same object.
-The PUT command of an existing object creates a new version of it.
-By default, the GET command retreive the latest version of the object. Also, the user can choose to retreive a specific version of the object.
-By default, the DELETE command achieve complete deletion of the whole object. The user can delete a specific version by mentioning this latter.
# Client Server Architecture 
I have developed a Client Server Architecture that is able to run the system remotly through different machines (the user should set up the necessary configurations to the firewall in order to ensure the execution of the Server python script).
# Client Server with transfer
The object's content can migrate through the network between the two endpoints. For example,in case of a PUT command, the client can read a file and transmit it to the server, and the latter can store the received file localy.
# Client Server without transfer 
The server have the access to the client's paths. He can read/write the client's files.
# Object's Versions management Policies:
1- Global Policy: the user can set a maximum number of versions to store for each created object. Any creation of a new version that exceeds the maximum number of versions should follow the deletion of the oldest existing version.
2-Dynamic Policy : same as the the global policy, but a creation of any new version is preceded by deleting 25% of the oldest versions.
3- Each Object have its Policy.
# Prerequisites
You can use the program localy or remotely. You should install SQLITE3.
Before executing the Client Server interaction, make sure that SQLITE3 is installed besides the Server Side.
