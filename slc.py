import socket
import re
import struct
import serial

print("BAE Systems Australia SLC v1.0.0") # Software Version

# Function to get user input for product, IP address, and port
def get_user_input():
    valid_products = ["DRX", "TOC", "ROC", "DWG"]
    while True:
        product = input("Enter Product (DRx, TOC, ROC, DWG): ").strip().upper()
        if product in valid_products:
            break
        else:
            print("Invalid product. Please enter one of the following: DRx, TOC, ROC, DWG.")
    
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
                    print("Invalid port format. Please enter a number between 1 and 65535.")
            return product, connection_type, ip_address, port
        elif is_valid_com_port(address):
            connection_type = "com"
            com_port = address
            return product, connection_type, com_port, None
        else:
            print("Invalid input. Please enter a valid IP address or COM port.")

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

# Function to get user command
def get_user_command():
    command = input("Enter a command in '[r/w] [address] [val]': ")
    parts = command.split()
    if len(parts) == 2 and parts[0] == 'r' and is_valid_hex(parts[1]):
        rw, address = parts
        return rw, address, None
    elif len(parts) == 3 and parts[0] == 'w' and is_valid_hex(parts[1]) and is_valid_hex(parts[2]):
        rw, address, val = parts
        return rw, address, val
    else:
        print("Invalid command format. The first argument must be 'r' or 'w'. The second and third arguments must be 16-bit hexadecimal values.")
        return None, None, None

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
            print(f"Error: The IP address {host_or_com} cannot be found.")
            return
        except socket.error as e:
            print(f"Error: The IP address {host_or_com} is in use or cannot be connected to. Details: {e}")
            return

        while True:
            rw, address, val = get_user_command()
            if rw == 'w' and address and val:
                print(f"Command: {rw}, Address: {address}, Value: {val}")
                packet = create_data_packet(product, rw, address, val)
                client_socket.sendall(packet)
                print("Write Complete")
            elif rw == 'r' and address:
                print(f"Command: {rw}, Address: {address}")
                packet = create_data_packet(product, rw, address)
                client_socket.sendall(packet)
                try:
                    response = client_socket.recv(4)
                    print(f"Raw server response: {response}")
                    if len(response) >= 4:
                        data_word = struct.unpack('<H', response[2:4])[0]  # Extract 4th byte followed by 3rd byte
                        print(f"Data word: 0x{data_word:04X} ({data_word})")
                    else:
                        print(f"Raw server response: {response}")
                except socket.timeout:
                    print("Error: Server response timed out.")
            else:
                print("Please enter a valid command")
    else:
        # Create a serial connection
        try:
            ser = serial.Serial(host_or_com, 9600, timeout=1)
            print(f"Connected to {host_or_com}")
        except serial.SerialException as e:
            print(f"Error: Could not open COM port {host_or_com}. Details: {e}")
            return

        while True:
            rw, address, val = get_user_command()
            if rw == 'w' and address and val:
                print(f"Command: {rw}, Address: {address}, Value: {val}")
                packet = create_data_packet(product, rw, address, val)
                ser.write(packet)
                print("Write Complete")
            elif rw == 'r' and address:
                print(f"Command: {rw}, Address: {address}")
                packet = create_data_packet(product, rw, address)
                ser.write(packet)
                response = ser.read(4)
                print(f"Raw server response: {response}")
                if len(response) >= 4:
                    data_word = struct.unpack('<H', response[2:4])[0]  # Extract 4th byte followed by 3rd byte
                    print(f"Data word: 0x{data_word:04X} ({data_word})")
                else:
                    print(f"Raw server response: {response}")
            else:
                print("Please enter a valid command")

if __name__ == "__main__":
    main()