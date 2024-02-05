import sys
import time
import subprocess

command = sys.executable

# Check if all required modules are installed
# If they are not installed the program will attempt to install them
# The rest of the code will not run untill everything is installed
process = subprocess.Popen(
[command, "./install.py"], shell = True)
process.wait()

while True: 
    # Run main application
    # If the main application crashes it will automatically restart 
    process = subprocess.Popen(
    [command, "./scripts/main.py"], shell = True)
    process.wait()  

    # Wait for 0.5 seconds before restarting
    time.sleep(0.5)
     
