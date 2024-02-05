import os
import csv
import psutil
import shutil
from json_reader import *
from datetime import datetime
from collections import deque

# Import settings from settings folder into objects
variables = load_json("./settings/variables.json")
comms = load_json("./settings/communication.json")
settings = load_json("./settings/file_handler.json")
infoRegs = load_json("./settings/info_registers.json")


# This function is used to list all files in a directory
def read_files_in_folder(dir):
    # Ensure the provided path is a directory
    if not os.path.isdir(dir): return []
    # Use list comprehension to get all files in the directory
    return [f for f in os.listdir(dir)
        if os.path.isfile(os.path.join(dir, f))]


# Move all files in data folder to the dumnp file
# The dump file is used as a backup file to ensure
# That the data folder does not have to many files 
# After a while of use
def dump_data_files(log_dir, dump_dir):
    # Ensure the provided paths are valid directories
    if not os.path.isdir(log_dir): return
    if not os.path.isdir(dump_dir): return
    # Get a list of all files in the source directory
    files_to_move = [f for f in os.listdir(
        log_dir) if os.path.isfile(os.path.join(log_dir, f))]
    if (len(files_to_move) >= settings["max files in log folder"]):
        # Move each file to the destination directory
        for file_name in files_to_move:
            src_path = os.path.join(log_dir, file_name)
            dest_path = os.path.join(dump_dir, file_name)
            shutil.move(src_path, dest_path)


# Find the newest file in the directory
def get_name_of_newest_file(files):
    # Assume files are in order from oldest to newest
    return files[len(files)-1]


# This function makes a new log file in the provided directory
# The file format is csv and the headers should also be provided
# When the function is called. The files name is is created using
# The current time and todays date in order to make it unique from 
# All the rest
def create_new_log_file(dir, headers):
	# Add date and time columns to headers
	headers.insert(0, "time")
	headers.insert(0, "date")
	# Generate a file name
	date_time = datetime.now()
	file_name = date_time.strftime("%Y-%m-%d___%H-%M-%S") + ".csv"
	# Create the file
	new_file = open(dir + file_name, "w")
	new_file.write(",".join(headers))
	new_file.close()
	return dir + file_name


# Return a object that is used to interface 
# With a file in a certain directory
def link_to_file(file_dir):
	return open(file_dir, "a")


# Used to read the headers present in a csv file
# Into a list, very important function
def read_file_headers(file_dir):
    # Assuming the first row contains the headers
	csv_file = open(file_dir, "r", newline="")
	csv_reader = csv.reader(csv_file)
	headers = next(csv_reader, [])
	csv_file.close()
	return headers


# This function is used to check if a valid log file is present
# If a valid one is present it will return a object to that file
# Else it would make a new file and then return the new file's object
def initiate_log_file():
	# Check if file dump needs to happen, if so do it
	dump_data_files(settings["logs folder"], settings["dump folder"])
	files = read_files_in_folder(settings["logs folder"])

	# If these is actuall files found in the data dir
	if (len(files) >= 1):
		new = get_name_of_newest_file(files)

		# Check if the newest file's date is the same as today's date
		if (new.split("_")[0] != datetime.now().strftime("%Y-%m-%d")):
			file_dir = create_new_log_file(settings["logs folder"], variables["names"])
			return link_to_file(file_dir)

		# Get the headers of the newest file in the data directory
		file_headers = read_file_headers(settings["logs folder"] + new)

		# If the number of headers do not match the number of variables to log
		if (len(file_headers) != len(variables["names"])+2):
			file_dir = create_new_log_file(settings["logs folder"], variables["names"])
			return link_to_file(file_dir)

		# If the header names are not the same as the names of the variable to log
		elif (file_headers[2:] != variables["names"]):
			file_dir = create_new_log_file(settings["logs folder"], variables["names"])
			return link_to_file(file_dir)

		# If the headers match exactly up with the variables to log
		else: return link_to_file(settings["logs folder"] + new)

	else: # If there are no files in the data directory
		file_dir = create_new_log_file(settings["logs folder"], variables["names"])
		return link_to_file(file_dir)
	

# Calculate how many logs should elapse before a certain time has passed
# This is used to calculate when a flush is ready to happen
# A flush is when data in the file buffer is actually writen to the file
# Making it non volatile
def cycles_before_flush():
	return int(settings["data flush wait time"]/comms["plc ping rate"])


# Append the current date and time to the data received from PLC 
# This is done before actually logging the data to the file
def append_date_and_time(data):
	# Append date and time 
	date_time = datetime.now()
	time = date_time.strftime("%H:%M:%S'%f")[:-4]
	date = date_time.strftime("%Y/%m/%d")
	data.appendleft(time)
	data.appendleft(date)
	return data


# Write.Append data to file using file object
def log_to_file(file_pointer, data):
	file_pointer.write("\n" + data)


# This function takes the current file that is being written to and
# Saves a copy of it to every USB drive connected to the computer
def save_file_to_usb(infoClient):
	usb_devices = []
	infoClient.Write_Holding_Register(infoRegs["usb save req"], 0)

	# Look for connected usb devices
	for partition in psutil.disk_partitions():
		if partition.opts in ["rw,removable", "removable"]:
			if partition.device in settings["usb save drives"]:
				usb_devices.append(partition.device)

	# If no usb devices are found
	if not len(usb_devices):
		infoClient.Write_Holding_Register(infoRegs["no usb"], 1)
		return

	try: # If this try catches an error it means there is a server side error
		files = read_files_in_folder(settings["logs folder"])
		newest_file = files[len(files)-1]
		curr_dir = settings["logs folder"] + newest_file

		# For every valid device to save to
		for usb in usb_devices:
			new_dir = usb[0] + ":\\" + "Saved Machine Data\\"

			if not os.path.exists(new_dir):
				os.makedirs(new_dir)

			new_dir += newest_file
			file_number = 1

			# While file name is present in folder
			while os.path.exists(new_dir):
				# Update name untill it is unique
				if "(" in new_dir and ")" in new_dir:
					file_number += 1
					new_dir = new_dir.split("(")[0]
					new_dir += "(" + str(file_number) + ").csv"
				else: new_dir = new_dir.split(".")[0] + "(1).csv"

			# Save copy of file to usb
			shutil.copy2(curr_dir, new_dir)
			infoClient.Write_Holding_Register(infoRegs["usb save done"], 1)
	except: infoClient.Write_Holding_Register(infoRegs["usb save error"], 1)

