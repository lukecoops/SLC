import socket
import re
import struct

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
        ip_address = "127.0.0.1"
        try:
            socket.inet_aton(ip_address)
            break
        except socket.error:
            print("Invalid IP address format. Please try again.")
    
    while True:
        port = "65432"
        if port.isdigit() and 0 < int(port) < 65536:
            port = int(port)
            break
        else:
            print("Invalid port format. Please enter a number between 1 and 65535.")
    
    return product, ip_address, port

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

    packet = (rw_bit << 31) | (address_bits << 16) | data_bits
    return struct.pack('!I', packet)

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
        print(f"Error: The IP address {host} is in use or cannot be connected to. Details: {e}")
        return

    while True:
        rw, address, val = get_user_command()
        if rw == 'w' and address and val:
            print(f"Command: {rw}, Address: {address}, Value: {val}")
            packet = create_data_packet(product, rw, address, val)
            client_socket.sendall(packet)
            response = client_socket.recv(1024)
            print(f"Raw server response: {response}")
        elif rw == 'r' and address:
            print(f"Command: {rw}, Address: {address}")
            packet = create_data_packet(product, rw, address)
            client_socket.sendall(packet)
            response = client_socket.recv(1024)
            print(f"Raw server response: {response}")
            if len(response) >= 2:
                data_word = struct.unpack('!H', response[-2:])[0]
                print(f"Data word: 0x{data_word:04X} ({data_word})")
            else:
                print(f"Raw server response: {response}")
        else:
            print("Please enter a valid command")

if __name__ == "__main__":
    main()