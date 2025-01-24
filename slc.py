import socket
import re
import struct

print("SLC v1.0.0") # Software Version
      
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
        ip_address = "127.0.0.1" # input("Enter IP Address: ")
        try:
            socket.inet_aton(ip_address)
            break
        except socket.error:
            print("Invalid IP address format. Please try again.")
    
    while True:
        port = "65432" # input("Enter Port: ")
        if port.isdigit() and 0 < int(port) < 65536:
            port = int(port)
            break
        else:
            print("Invalid port format. Please enter a number between 1 and 65535.")
    
    return product, ip_address, port

# Function to validate 16-bit hexadecimal value
def is_valid_hex(value):
    return bool(re.fullmatch(r'^[0-9A-Fa-f]{1,4}$', value))

# Function to calculate CRC-16-CCITT
def calculate_crc(data):
    crc = 0xFFFF
    for word in data:
        crc ^= word
        for _ in range(16):  # Process each bit in the word
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0x8408
            else:
                crc >>= 1
    return crc & 0xFFFF

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
    if product in ["ROC", "TOC"]:
        header = 0xAA55
        if rw == 'r':
            message_type = 0x0001  # TOC to ROC Command
            address_word = int(address, 16) & 0x7FFF  # Read flag (0) and address
            data_word = 0x0000
        elif rw == 'w':
            message_type = 0x0001  # TOC to ROC Command
            address_word = (int(address, 16) & 0x7FFF) | 0x8000  # Write flag (1) and address
            data_word = int(val, 16)
        crc_word = calculate_crc([header, message_type, address_word, data_word])
        packet = struct.pack('!HHHHH', header, message_type, address_word, data_word, crc_word)
    else:
        rw_bit = 1 if rw == 'w' else 0
        address_bits = int(address, 16) & 0x7FFF
        data_bits = int(val, 16) if val else 0
        packet = struct.pack('!I', (rw_bit << 31) | (address_bits << 16) | data_bits)
    return packet

# Main function to handle the client-server communication
def main():
    product, host, port = get_user_input()

    # Create a TCP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to the server
    try:
        client_socket.connect((host, port))
        print(f"Connected to server at {host}:{port}")
    except socket.gaierror:
        print(f"Error: The IP address {host} cannot be found.")
        return
    except socket.error as e:
        print(f"Error: The IP address {host} cannot be connected to. Details: {e}")
        return

    while True:
        rw, address, val = get_user_command()
        if rw == 'w' and address and val:
            print(f"Command: {rw}, Address: {address}, Value: {val}")
            packet = create_data_packet(product, rw, address, val)
            client_socket.sendall(packet)
            response = client_socket.recv(1024)
            print(f"Server response: {response.decode('utf-8')}")
        elif rw == 'r' and address:
            print(f"Command: {rw}, Address: {address}")
            packet = create_data_packet(product, rw, address)
            client_socket.sendall(packet)
            response = client_socket.recv(1024)
            if len(response) >= 2:
                data_word = struct.unpack('!H', response[:2])[0]
                print(f"Data word: 0x{data_word:04X} ({data_word})")
            else:
                print(f"Server response: {response.decode('utf-8')}")
        else:
            print("Please enter a valid command")

if __name__ == "__main__":
    main()