import time
import datetime
import threading
from json_reader import *
from file_handler import *
from modbus_tcp_client import *
from collections import deque


# Import settings from settings folder into objects
variable = load_json("./settings/variables.json")
settings = load_json("./settings/communication.json")
infoRegs = load_json("./settings/info_registers.json")


# This function runs in its own thread 
# Its purpose is to receive commands from the PLC
# It checks for commands every 2 seconds
def Check_For_PLC_Commands(infoClient):
	# Initiate register values on the PLC
	infoClient.Write_Holding_Register(infoRegs["usb save done"], 0)
	infoClient.Write_Holding_Register(infoRegs["usb save error"], 0)
	infoClient.Write_Holding_Register(infoRegs["no usb"], 0)
	while True:
		time.sleep(2)
		# Read all the info registers 
		plcReq = infoClient.Request_Holding_Registers(0, 6)

		# This line of code catches if a error response ware received from PLC
		if len(plcReq) == 0: continue
		
		# Check if file save needs to happen
		if plcReq[infoRegs["usb save req"]]: 
			save_file_to_usb(infoClient)


if __name__ == "__main__":
	# Inititiate connections to PLC's servers
	dataClient = ModbusClient(
	settings["plc IPv4"], settings["plc data PORT"])
	
	infoClient = ModbusClient(
	settings["plc IPv4"], settings["plc info PORT"])
	
	# Create and start PLC info thread
	info_thread = threading.Thread(
	target = Check_For_PLC_Commands,
	args = ([infoClient]))
	info_thread.daemon = True
	info_thread.start()

	# Get todays data and time
	date = datetime.now()
	today = date.strftime("%Y/%m/%d")

	# Initiate a log file and open it to be able to write to it
	log_file = initiate_log_file()

	# Determine how many logs should be made before the file is saved
	# Meaning it is update on the hard drive itself not just the buffer
	flush_count = cycles_before_flush()

	# Determine how many variable data should be received and saved
	var_count = len(variable["names"])

	# Counters used in the loop
	current_cycles = 0 # used to determine if a flush needs to take place
	counter = 0 # count the logs made

	while True: # This is the main log-loop
		# Check if a new calendar date has started
		date = datetime.now()
		now = date.strftime("%Y/%m/%d")

		# If a new calender date has started break from the main log-loop
		# This will restart the application causing it to create a new file
		# With a new calender data
		if now != today: break

		try:			
			# Read data from PLC
			data = dataClient.Request_Holding_Registers(0, var_count)

            # Devide data with devider
            for d in range(len(data)):
                data[d] = data[d]/variable["devider"]
			
			# If an error frame was recieved
			# The program will restart
			if (not len(data)):
				time.sleep(1)
				break

			# Check if data flush needs to take place
			if (current_cycles > flush_count):
				log_file.flush()
				current_cycles = 0
			current_cycles += 1

			#Increment counter
			if (counter >= 65000): counter = 0
			else : counter += 1

			# Add current date and time to the data
			data = append_date_and_time(data)

			# Convert the data to string format before saving
			str_data = [str(i) for i in data]

			# Actually write data ti log file
			log_to_file(log_file, ",".join(str_data))

			# Update the log counter on the PLC
			infoClient.Write_Holding_Register(0, counter)

			# Wait a short moment before starting the proccess again
			time.sleep(settings["plc ping rate"])

		except: # If a crash is detetcted in the main loop the program will restart
			time.sleep(1)
			break

	# Close connections before restarting the application
	infoClient.Close_Connection()
	dataClient.Close_Connection()
	log_file.flush()
	log_file.close()
