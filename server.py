import socket
import struct

# Create a TCP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to an address and port
host = '127.0.0.1'  # Localhost
port = 65432        # Arbitrary non-privileged port
server_socket.bind((host, port))

# Start listening for incoming connections
server_socket.listen(1)
print(f"Server listening on {host}:{port}")

while True:
    # Accept a new connection
    conn, addr = server_socket.accept()
    print(f"Connected by {addr}")

    while True:
        # Receive data from the client
        data = conn.recv(1024)  # Buffer size is 1024 bytes
        if not data:
            break

        if len(data) == 4:  # Common packet structure 4 bytes
            packet = struct.unpack('!I', data[:4])[0]
            rw_bit = (packet >> 31) & 0x1
            address_bits = (packet >> 16) & 0x7FFF
            data_bits = packet & 0xFFFF

            print(f"Received packet: RW={rw_bit}, Address={address_bits:04X}, Data={data_bits:04X}")

            # Respond based on the received command
            if rw_bit == 0:
                response = b"Write Completed"
            else:
                if address_bits == 0x602B:  # Check if address is 0x602B
                    response = struct.pack('!I', 0b11100000001010110000000000001111)  # Respond with 11100000001010110000000000001111
                else:
                    response = struct.pack('!I', 0b11100000001010110000000000000001)  # Respond with 11100000001010110000000000000001
        else:
            response = b"Invalid Packet"

        conn.sendall(response)
    conn.close()