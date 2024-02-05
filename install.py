import os

os.system("cls")
installed = False

while not installed:
    try: # test if the non-built-in libraries/modules are allready installed
        import psutil
        installed = True
    except: # if the requires libs are not installed
        try: # install the libraries/modules that are not built into python
            os.system("pip install psutil")
            installed = True
        except: # if the program could not install the required libs/modules
            os.system("cls")
            print("=================================================")
            print("Could not install all required modules")
            print("Make sure the computer has an internet connection")
            print("- - - - - - - - - - - - - - - - - - - - - - - - -")
            print("Press Enter key to try again")
            print("=================================================")
            input()