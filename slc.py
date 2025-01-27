import socket
import re
import struct
import time
import os
import csv
from datetime import datetime, timedelta, timezone
import sys
import select

# Import msvcrt for detecting key presses on Windows
if os.name == 'nt':
    import msvcrt
    import serial
else:
    import termios
    import tty

# Software Version
software_version = "v1.0.0"
print(f"BAE SYSTEMS AUSTRALIA SIMPLE LOCAL CONTROL {software_version}") # Software Version

# ANSI escape codes for coloured output
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

# Ensure the SLC_LOG directory exists
log_dir = "SLC_LOG"
os.makedirs(log_dir, exist_ok=True)

# Generate a unique log file name based on the current date and time
session_time = datetime.now(timezone(timedelta(hours=10.5))).strftime('%Y-%m-%d_%H-%M-%S')  # Adelaide time
log_file = os.path.join(log_dir, f"slc_command_log_{session_time}.csv")

# Write the header to the CSV file
with open(log_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Timestamp", "Message", "RW", "Address", "Value"])

# Function to log messages to CSV
def log_to_csv(timestamp, message, rw="", address="", value=""):
    # Remove ANSI escape codes from the message
    ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
    message = ansi_escape.sub('', message)
    try:
        with open(log_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, message, rw, address, value])
    except PermissionError:
        print(f"{RED}Error: Permission denied when writing to {log_file}.{RESET}")

# Function to print with timestamp and log to CSV
def print_with_timestamp(message, rw="", address="", value=""):
    timestamp = datetime.now(timezone(timedelta(hours=10.5))).strftime('%Y-%m-%d %H:%M:%S')  # Adelaide time
    log_to_csv(timestamp, message, rw, address, value)
    print(f"[{timestamp}] {message}")

# Function to get user input for product, address, and port
def get_user_input():
    config = read_config()
    product = config.get('product') if config else None
    address = config.get('address') if config else None
    port = config.get('port') if config else None

    if product and address:
        print(f"Loaded from config file: Product={product}, Address={address}")
        if is_valid_ip(address) and port and port.isdigit() and 0 < int(port) < 65536:
            return product, "network", address, int(port)
        elif os.name == 'nt' and is_valid_com_port(address):
            return product, "com", address, None
        else:
            print(f"{RED}Invalid address or port in config file.{RESET}")
            product, address, port = None, None, None

    valid_products = ["TOC", "ROC"]
    while not product:
        product = input("Enter Product (TOC, ROC): ").strip().upper()
        if product not in valid_products:
            print(f"{RED}Invalid product. Please enter one of the following: TOC, ROC.{RESET}")
            product = None
    
    while not address:
        address_input = input("Enter IP Address or COM port: ").strip()
        if is_valid_ip(address_input):
            connection_type = "network"
            address = address_input
            while not port:
                port = input("Enter port number (usually 10001): ").strip()
                if not (port.isdigit() and 0 < int(port) < 65536):
                    print(f"{RED}Invalid port format. Please enter a number between 1 and 65535.{RESET}")
                    port = None
            return product, connection_type, address, int(port)
        elif os.name == 'nt' and is_valid_com_port(address_input):
            connection_type = "com"
            address = address_input
            try:
                serial.Serial(address)
                return product, connection_type, address, None
            except serial.SerialException as e:
                print(f"{RED}Error: Could not open COM port {address}. Details: {e}{RESET}")
        else:
            print(f"{RED}Invalid input. Please enter a valid IP address or COM port.{RESET}")

# Function to read config file
def read_config():
    config = {}
    if os.path.isfile('config.ini'):
        with open('config.ini', 'r') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    return config

# Function to validate IP address
def is_valid_ip(ip):
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False

# Function to validate COM port
def is_valid_com_port(port):
    return re.fullmatch(r'COM\d+', port, re.IGNORECASE) is not None

# Function to validate 16-bit hexadecimal value
def is_valid_hex(value):
    return bool(re.fullmatch(r'^[0-9A-Fa-f]{1,4}$', value))

# Function to get user commands from input or file
def get_user_commands():
    config = read_config()
    aliases = {k.lower(): v for k, v in config.items() if k.lower() not in ['product', 'address', 'port']}

    while True:
        commands = input("Enter commands separated by ';' (or help): ").strip()

        if commands.lower() == "help":
            print("Command format:")
            print("  Read: r <address>")
            print("  Write: w <address> <value>")
            print("  Delay: delay=<seconds>")
            print("  Continuous transmission: cont")
            print("  Load from file: <filename without extension>.txt")
            print("  Comments: #<comment>")
            print("Example: r 1234; w 5678 9ABC; delay=2; cont")
            continue

        # Remove trailing semicolon if present
        if commands.endswith(';'):
            commands = commands[:-1]

        command_list = commands.split(';')
        parsed_commands = []
        continuous_flag = False
        for command in command_list:
            command = command.strip()
            command_lower = command.lower()
            if command_lower in aliases:
                if os.path.isfile(command + ".txt"):
                    print(f"{YELLOW}Warning: Both a text file and a config file alias have the name '{command}'. The config file alias will take precedence.{RESET}")
                command = aliases[command_lower]
                command_list.extend(command.split(';'))
                continue
            if command.endswith('.txt'):
                file_name = command
            else:
                file_name = command + ".txt"
            if os.path.isfile(file_name):
                with open(file_name, 'r') as file:
                    file_commands = file.read().strip()
                if file_commands.endswith(';'):
                    file_commands = file_commands[:-1]
                command_list.extend(file_commands.split(';'))
                continue
            if command.startswith('#'):
                comment = command[1:].strip()
                print_with_timestamp(f"Comment: {comment}")
                continue
            if command.startswith('delay='):
                try:
                    delay = float(command.split('=')[1])
                    parsed_commands.append(('delay', delay))
                except ValueError:
                    print(f"{RED}Invalid delay format: {command}. Use delay=xx where xx is the number of seconds.{RESET}")
                continue
            if command == 'cont':
                continuous_flag = True
                continue
            if not command:
                continue
            parts = command.split()
            if len(parts) == 2 and parts[0] == 'r' and is_valid_hex(parts[1]):
                rw, address = parts
                parsed_commands.append((rw, address, None))
            elif len(parts) == 3 and parts[0] == 'w' and is_valid_hex(parts[1]) and is_valid_hex(parts[2]):
                rw, address, val = parts
                parsed_commands.append((rw, address, val))
            else:
                print(f"{RED}Invalid command format: {command}. Type 'help' for command format.{RESET}")
                return False, [], continuous_flag
        return True, parsed_commands, continuous_flag

# Function to create a data packet
def create_data_packet(product, rw, address, val=None):
    rw_bit = 1 if rw == 'r' else 0  # This sets rw_bit to 1 for read and 0 for write
    address_bits = int(address, 16) & 0x7FFF
    data_bits = int(val, 16) if val else 0

    # Combine rw_bit with address_bits
    address_bits = (rw_bit << 15) | address_bits

    # Pack address and data in little-endian format
    packet = struct.pack('<H', address_bits) + struct.pack('<H', data_bits)
    return packet

# Function to check for key press
def check_key_press():
    if os.name == 'nt':
        return msvcrt.kbhit() and msvcrt.getch().decode('utf-8').lower() == 'c'
    else:
        dr, dw, de = select.select([sys.stdin], [], [], 0)
        if dr:
            key = sys.stdin.read(1)
            return key.lower() == 'c'
        return False

# Main function to handle the client-server communication
def main():
    product, connection_type, address, port = get_user_input()

    if connection_type == "network":
        # Create a TCP socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect to the server
        try:
            client_socket.settimeout(5)  # Set a timeout of 5 seconds
            client_socket.connect((address, port))
            print(f"Connected to server at {address}:{port}")
        except socket.timeout:
            print(f"{RED}Error: Connection to {address} timed out.{RESET}")
            return
        except socket.gaierror:
            print(f"{RED}Error: The IP address {address} cannot be found.{RESET}")
            return
        except socket.error as e:
            if e.errno == 111:  # Connection refused
                print(f"{RED}Error: Connection refused by {address}.{RESET}")
            elif e.errno == 113:  # No route to host
                print(f"{RED}Error: No route to host {address}.{RESET}")
            else:
                print(f"{RED}Error: The IP address {address} is in use or cannot be connected to. Details: {e}{RESET}")
            return

        while True:
            valid, commands, continuous_flag = get_user_commands()
            if not valid:
                continue
            print("-" * 50)  # Horizontal line before command results
            if continuous_flag:
                print("Continuous send enabled. Press 'C' to cancel.")
            while True:
                for command in commands:
                    if command[0] == 'delay':
                        time.sleep(command[1])
                        continue
                    rw, address, val = command
                    if rw == 'w' and address and val:
                        print_with_timestamp(f"Write Complete. Address: {address}, Value: {val}", rw, address, val)
                        packet = create_data_packet(product, rw, address, val)
                        client_socket.sendall(packet)
                        # Read back to verify
                        packet = create_data_packet(product, 'r', address)
                        client_socket.sendall(packet)
                        time.sleep(0.1)  # Small delay before reading the response
                        try:
                            response = client_socket.recv(4)
                            if len(response) >= 4:
                                data_word = struct.unpack('<H', response[2:4])[0]  # Extract 4th byte followed by 3rd byte
                                if data_word == int(val, 16):
                                    print_with_timestamp(f"Write Verified. Address: {address} Data: 0x{data_word:04X} ({data_word})", 'r', address, val)
                                else:
                                    print_with_timestamp(f"{RED}Write Error: Different Value Read Back. Address: {address} Data: 0x{data_word:04X} ({data_word}){RESET}", 'r', address, val)
                            else:
                                print(f"{RED}Unknown error: {response}{RESET}")
                        except socket.timeout:
                            print(f"{RED}Error: Server response timed out.{RESET}")
                    elif rw == 'r' and address:
                        packet = create_data_packet(product, rw, address)
                        client_socket.sendall(packet)
                        time.sleep(0.1)  # Small delay before reading the response
                        try:
                            response = client_socket.recv(4)
                            if len(response) >= 4:
                                data_word = struct.unpack('<H', response[2:4])[0]  # Extract 4th byte followed by 3rd byte
                                print_with_timestamp(f"Read Complete. Address: {address} Data: 0x{data_word:04X} ({data_word})", rw, address)
                            else:
                                print(f"{RED}Unknown error: {response}{RESET}")
                        except socket.timeout:
                            print(f"{RED}Error: Server response timed out.{RESET}")
                    else:
                        print(f"{RED}Please enter a valid command{RESET}")
                    time.sleep(0.5)  # Delay of 0.5 seconds between commands
                if continuous_flag:
                    if check_key_press():
                        print("Continuous send stopped.")
                        break
                if not continuous_flag:
                    break
            print("-" * 50)  # Horizontal line after all command results
    elif os.name == 'nt':
        # Create a serial connection
        try:
            ser = serial.Serial(address, 9600, timeout=1)
            # Test the connection by writing and reading a test message
            test_message = b'\x00'
            ser.write(test_message)
            response = ser.read(1)
            if response != test_message:
                print(f"{RED}Error: No Server listening on {address.upper()}.{RESET}")
                return
            print(f"Connected to {address.upper()}")
        except serial.SerialException as e:
            print(f"{RED}Error: Could not open COM port {address}. Details: {e}{RESET}")
            return

        while True:
            valid, commands, continuous_flag = get_user_commands()
            if not valid:
                continue
            print("-" * 50)  # Horizontal line before command results
            if continuous_flag:
                print("Continuous send enabled. Press 'C' to cancel.")
            while True:
                for command in commands:
                    if command[0] == 'delay':
                        time.sleep(command[1])
                        continue
                    rw, address, val = command
                    if rw == 'w' and address and val:
                        packet = create_data_packet(product, rw, address, val)
                        ser.write(packet)
                        print_with_timestamp(f"Write Complete. Address: {address}, Value: {val}", rw, address, val)
                        # Read back to verify
                        packet = create_data_packet(product, 'r', address)
                        ser.write(packet)
                        time.sleep(0.1)  # Small delay before reading the response
                        response = ser.read(4)
                        if len(response) >= 4:
                            data_word = struct.unpack('<H', response[2:4])[0]  # Extract 4th byte followed by 3rd byte
                            if data_word == int(val, 16):
                                print_with_timestamp(f"Write Verified. Address: {address} Data: 0x{data_word:04X} ({data_word})", 'r', address, val)
                            else:
                                print_with_timestamp(f"{RED}Write Error: Different Value Read Back. Address: {address} Data: 0x{data_word:04X} ({data_word}){RESET}", 'r', address, val)
                        else:
                            print(f"{RED}Unknown error: {response}{RESET}")
                    elif rw == 'r' and address:
                        packet = create_data_packet(product, rw, address)
                        ser.write(packet)
                        response = ser.read(4)
                        if len(response) >= 4:
                            data_word = struct.unpack('<H', response[2:4])[0]  # Extract 4th byte followed by 3rd byte
                            print_with_timestamp(f"Read Complete. Address: {address} Data: 0x{data_word:04X} ({data_word})", rw, address)
                        else:
                            print(f"{RED}Unknown error: {response}{RESET}")
                    else:
                        print(f"{RED}Please enter a valid command{RESET}")
                    time.sleep(0.5)  # Delay of 0.5 seconds between commands
                if continuous_flag:
                    if check_key_press():
                        print("Continuous send stopped.")
                        break
                if not continuous_flag:
                    break
            print("-" * 50)  # Horizontal line after all command results

if __name__ == "__main__":
    main()