import socket
import re
import struct
import serial
import time

print("BAE Systems Australia SLC v1.0.0") # Software Version

# ANSI escape codes for coloured output
RED = '\033[91m'
RESET = '\033[0m'

# Function to get user input for product, IP address, and port
def get_user_input():
    valid_products = ["DRX", "TOC", "ROC", "DWG"]
    while True:
        product = input("Enter Product (DRx, TOC, ROC, DWG): ").strip().upper()
        if product in valid_products:
            break
        else:
            print(f"{RED}Invalid product. Please enter one of the following: DRx, TOC, ROC, DWG.{RESET}")
    
    while True:
        address = input("Enter IP Address or COM port: ").strip()
        if is_valid_ip(address):
            connection_type = "network"
            ip_address = address
            while True:
                port = input("Enter port number: ").strip()
                if port.isdigit() and 0 < int(port) < 65536:
                    port = int(port)
                    break
                else:
                    print(f"{RED}Invalid port format. Please enter a number between 1 and 65535.{RESET}")
            return product, connection_type, ip_address, port
        elif is_valid_com_port(address):
            connection_type = "com"
            com_port = address
            try:
                serial.Serial(com_port)
                return product, connection_type, com_port, None
            except serial.SerialException as e:
                print(f"{RED}Error: Could not open COM port {com_port}. Details: {e}{RESET}")
        else:
            print(f"{RED}Invalid input. Please enter a valid IP address or COM port.{RESET}")

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

# Function to get user commands
def get_user_commands():
    commands = input("Enter commands separated by ';' (e.g., 'r 1234; w 5678 9ABC'): ").strip()
    command_list = commands.split(';')
    parsed_commands = []
    for command in command_list:
        parts = command.strip().split()
        if len(parts) == 2 and parts[0] == 'r' and is_valid_hex(parts[1]):
            rw, address = parts
            parsed_commands.append((rw, address, None))
        elif len(parts) == 3 and parts[0] == 'w' and is_valid_hex(parts[1]) and is_valid_hex(parts[2]):
            rw, address, val = parts
            parsed_commands.append((rw, address, val))
        else:
            print(f"{RED}Invalid command format: {command}. The first argument must be 'r' or 'w'. The second and third arguments must be 16-bit hexadecimal values.{RESET}")
            return False, []
    return True, parsed_commands

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

# Main function to handle the client-server communication
def main():
    product, connection_type, host_or_com, port = get_user_input()

    if connection_type == "network":
        # Create a TCP socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect to the server
        try:
            client_socket.connect((host_or_com, port))
            client_socket.settimeout(5)  # Set a timeout of 5 seconds
            print(f"Connected to server at {host_or_com}:{port}")
        except socket.gaierror:
            print(f"{RED}Error: The IP address {host_or_com} cannot be found.{RESET}")
            return
        except socket.error as e:
            print(f"{RED}Error: The IP address {host_or_com} is in use or cannot be connected to. Details: {e}{RESET}")
            return

        while True:
            valid, commands = get_user_commands()
            if not valid:
                continue
            print("-" * 50)  # Horizontal line before command results
            for rw, address, val in commands:
                if rw == 'w' and address and val:
                    print(f"Write Complete. Address: {address}, Value: {val}")
                    packet = create_data_packet(product, rw, address, val)
                    client_socket.sendall(packet)
                    # Read back to verify
                    packet = create_data_packet(product, 'r', address)
                    client_socket.sendall(packet)
                    try:
                        response = client_socket.recv(4)
                        if len(response) >= 4:
                            data_word = struct.unpack('<H', response[2:4])[0]  # Extract 4th byte followed by 3rd byte
                            if data_word == int(val, 16):
                                print(f"Write Verified. Address: {address} Data: 0x{data_word:04X} ({data_word})")
                            else:
                                print(f"{RED}Write Error: Different Value Read Back. Address: {address} Data: 0x{data_word:04X} ({data_word}){RESET}")
                        else:
                            print(f"Raw server response: {response}")
                    except socket.timeout:
                        print(f"{RED}Error: Server response timed out.{RESET}")
                elif rw == 'r' and address:
                    packet = create_data_packet(product, rw, address)
                    client_socket.sendall(packet)
                    try:
                        response = client_socket.recv(4)
                        if len(response) >= 4:
                            data_word = struct.unpack('<H', response[2:4])[0]  # Extract 4th byte followed by 3rd byte
                            print(f"Read Complete. Address: {address} Data: 0x{data_word:04X} ({data_word})")
                        else:
                            print(f"Raw server response: {response}")
                    except socket.timeout:
                        print(f"{RED}Error: Server response timed out.{RESET}")
                else:
                    print(f"{RED}Please enter a valid command{RESET}")
                time.sleep(0.5)  # Delay of 0.5 seconds between commands
            print("-" * 50)  # Horizontal line after all command results
    else:
        # Create a serial connection
        try:
            ser = serial.Serial(host_or_com, 9600, timeout=1)
            print(f"Connected to {host_or_com}")
        except serial.SerialException as e:
            print(f"{RED}Error: Could not open COM port {host_or_com}. Details: {e}{RESET}")
            return

        while True:
            valid, commands = get_user_commands()
            if not valid:
                continue
            print("-" * 50)  # Horizontal line before command results
            for rw, address, val in commands:
                if rw == 'w' and address and val:
                    packet = create_data_packet(product, rw, address, val)
                    ser.write(packet)
                    print(f"Write Complete. Address: {address}, Value: {val}")
                    # Read back to verify
                    packet = create_data_packet(product, 'r', address)
                    ser.write(packet)
                    response = ser.read(4)
                    if len(response) >= 4:
                        data_word = struct.unpack('<H', response[2:4])[0]  # Extract 4th byte followed by 3rd byte
                        if data_word == int(val, 16):
                            print(f"Write Verified. Address: {address} Data: 0x{data_word:04X} ({data_word})")
                        else:
                            print(f"{RED}Write Error: Different Value Read Back. Address: {address} Data: 0x{data_word:04X} ({data_word}){RESET}")
                    else:
                        print(f"Raw server response: {response}")
                elif rw == 'r' and address:
                    packet = create_data_packet(product, rw, address)
                    ser.write(packet)
                    response = ser.read(4)
                    if len(response) >= 4:
                        data_word = struct.unpack('<H', response[2:4])[0]  # Extract 4th byte followed by 3rd byte
                        print(f"Read Complete. Address: {address} Data: 0x{data_word:04X} ({data_word})")
                    else:
                        print(f"Raw server response: {response}")
                else:
                    print(f"{RED}Please enter a valid command{RESET}")
                time.sleep(0.5)  # Delay of 0.5 seconds between commands
            print("-" * 50)  # Horizontal line after all command results

if __name__ == "__main__":
    main()