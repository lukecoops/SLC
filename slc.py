import socket
import re

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
        ip_address = input("Enter IP Address: ")
        try:
            socket.inet_aton(ip_address)
            break
        except socket.error:
            print("Invalid IP address format. Please try again.")
    
    while True:
        port = input("Enter Port: ")
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
    command = input("Enter a command in '[r/w] [address] [val]' or 'disconnect': ")
    parts = command.split()
    if parts[0] == 'disconnect':
        return 'disconnect', None, None
    elif len(parts) == 2 and parts[0] == 'r' and is_valid_hex(parts[1]):
        rw, address = parts
        return rw, address, None
    elif len(parts) == 3 and parts[0] == 'w' and is_valid_hex(parts[1]) and is_valid_hex(parts[2]):
        rw, address, val = parts
        return rw, address, val
    else:
        print("Invalid command format. The first argument must be 'r' or 'w'. The second and third arguments must be 16-bit hexadecimal values.")
        return None, None, None

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
        if rw == 'disconnect':
            print("Disconnecting from server")
            client_socket.close()
            break
        elif rw == 'w' and address and val:
            print(f"Command: {rw}, Address: {address}, Value: {val}")
            client_socket.sendall(b"Write Command")
            response = client_socket.recv(1024)
            print(f"Server response: {response.decode()}")
        elif rw == 'r' and address:
            print(f"Command: {rw}, Address: {address}")
            client_socket.sendall(b"Read Command")
            response = client_socket.recv(1024)
            print(f"Server response: {response.decode()}")
        else:
            print("Please enter a valid command")

if __name__ == "__main__":
    main()