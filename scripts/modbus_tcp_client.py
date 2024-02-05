# How to call and initiate class:
# ===============================

#     myModbusClient = ModbusClient(server_ip(string), server_port(int))

# This class has 3 usable functions:
# ==================================

#     Request_Holding Registers():
#     ----------------------------

#         Function Inputs (2 Options):
#             A: (register(int), amount(int)) 
#             B: (register(int), amount(int), transaction_id(int), protocolo_id(int), device_address(int))

#         Description:
#             Used to read multiple holding registers on the server at once.
#             If input type A is used, the transaction id, protocol id and 
#             device address will be set to 0. If an error accurred the function
#             output will be an empty deque, else it would be an deque with values.

#     Write_Holding_Registers():
#     --------------------------

#         Function Inputs (2 Options):
#             A: (register(int), value(16_uint)) 
#             B: (register(int), value(16_uint), transaction_id(int), protocolo_id(int), device_address(int))

#         Description:
#             Used to write to a SINGLE holding register. If input type A
#             is used, the transaction id, protocol id and device address
#             will be set to 0. If the function did not encounter any erros
#             it will return the string "success", else it will return "error"

#     Write_Holding_Registers_M():
#     --------------------------

#         Function Inputs (2 Options):
#             A: (register(int), list[value(16_uint)]) 
#             B: (register(int), list[value(16_uint)], transaction_id(int), protocolo_id(int), device_address(int))

#         Description:
#             Used to write to a MULTIPLE holding register. If input type A
#             is used, the transaction id, protocol id and device address
#             will be set to 0. If the function did not encounter any erros
#             it will return the string "success", else it will return "error"

#     Close_Connections():
#     --------------------

#         Description: Used to close the connection to the server.

import socket
from collections import deque

class ModbusClient:
    max_registers_per_request = 125

    def __init__(self, host, port):
        self.client_socket = socket.socket(
        socket.AF_INET, 
        socket.SOCK_STREAM)
        self.client_socket.connect((host, port))

    def __to_Word__(self, decimal):
        msb = (decimal >> 8) & 0xff
        lsb = decimal & 0xff
        return [msb, lsb]

    def __to_Byte__(self, decimal):
        return [decimal]

    def __Word_to_Decimal__(self, msb, lsb):
        return (msb << 8) + lsb

    def __Check_for_Error__(self, res):
        if res[7] > 20: return True
        return False

    def __Calculate_Frame_Counts__(self, total):
        frame_counts = []
        for x in range(int(total/self.max_registers_per_request)):
            frame_counts.append(self.max_registers_per_request)
        current_total = sum(frame_counts)
        if current_total < total:
            frame_counts.append(total - current_total)
        return frame_counts

    def Request_Holding_Registers(self, *args):
        holding_registers = deque()
        if len(args) == 2: overheads = [0, 0, 0]
        elif len(args) == 5: overheads = [args[2], args[3], args[4]]
        else: return []
        start_register = args[0]
        frame_counts = self.__Calculate_Frame_Counts__(args[1])
        for count in frame_counts:
            frame = self.__to_Word__(overheads[0])
            frame += self.__to_Word__(overheads[1]) + [0, 6]
            frame += self.__to_Byte__(overheads[2]) + [3] 
            frame += self.__to_Word__(start_register)
            frame += self.__to_Word__(count)
            self.client_socket.sendall(bytes(frame))
            res = self.client_socket.recv(10 + 2*count)
            if not self.__Check_for_Error__(res):
                data = res[9:]
                if len(data)%2 != 0: return []
                for x in range(0, len(data), 2):
                    holding_registers.append(
                    self.__Word_to_Decimal__(data[x], data[x+1]))
            else: return []
            start_register += count
        if len(holding_registers) != args[1]:return []
        return holding_registers

    def Write_Holding_Register(self, *args):
        if len(args) == 2: overheads = [0,0,0]
        elif len(args) == 5: overheads = [args[2], args[3], args[4]]
        else: return "error"
        frame = self.__to_Word__(overheads[0])
        frame += self.__to_Word__(overheads[1]) + [0, 6]
        frame += self.__to_Byte__(overheads[2]) + [6] 
        frame += self.__to_Word__(args[0])
        frame += self.__to_Word__(args[1])
        self.client_socket.sendall(bytes(frame))
        res = self.client_socket.recv(12)
        if self.__Check_for_Error__(res): return "error"
        return "updated"

    def Write_Holding_Register_M(self, *args):
        if len(args) == 2: overheads = [0,0,0]
        elif len(args) == 5: overheads = [args[2], args[3], args[4]]
        else: return "error"
        frame_data = []
        frame = self.__to_Word__(overheads[0])
        frame += self.__to_Word__(overheads[1])
        frame += self.__to_Word__(len(args[1]*2) + 7)
        frame += self.__to_Byte__(overheads[2]) + [16] 
        frame += self.__to_Word__(args[0])
        frame += self.__to_Word__(len(args[1]))
        frame += [len(args[1])*2]
        for val in args[1]:
            frame_data += self.__to_Word__(val)
        frame += frame_data
        self.client_socket.sendall(bytes(frame))
        res = self.client_socket.recv(12)
        if self.__Check_for_Error__(res): return "error"
        return "updated"

    def Close_Connection(self):
        self.client_socket.close()
