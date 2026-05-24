**Rust Sql Server**

This tool takes in a command line argument of either a db (SQLite) or csv (in which case a sqlite database will be
created fro that file.  It then creates an asynchronous server that allows for issuing of the various
commands to and from the sqlite database with appropriate file locking and handling.  It allows for 
*unrestricted* access to the database it hosts with no security or prevention of commands like DROP, it is simply 
a lightweight tool to make it easier to use SQLite in other applications.
