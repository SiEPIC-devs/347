import json
import os

file_path = os.path.join(os.getcwd(), "database", "selection_serial.json")
with open(file_path, "r") as f:
    serial_list = json.load(f)

print("选择的序列号是：", serial_list)