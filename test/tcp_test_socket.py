import socket

# Create a TCP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to the server
host = '127.0.0.1'  # Localhost
port = 65432        # Same port as the server
client_socket.connect((host, port))
print(f"Connected to server at {host}:{port}")

# Send data to the server
client_socket.sendall(b"Hello, Server!")

# Receive the server's response
data = client_socket.recv(1024)  # Buffer size is 1024 bytes
print(f"Received: {data.decode()}")

# Close the connection
client_socket.close()