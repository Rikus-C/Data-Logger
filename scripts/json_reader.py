import json

# This function is used to read JSON files into
# a python object to use use in the program
def load_json(json_file_path):
    file = open(json_file_path, "r")
    data = json.load(file)
    file.close()
    return data
