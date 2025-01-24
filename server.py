import socket
import struct

# Function to calculate CRC-16-CCITT
def calculate_crc(data):
    crc = 0xFFFF
    for word in data:
        crc ^= word
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0x8408
            else:
                crc >>= 1
    return crc & 0xFFFF

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

        # Unpack the received packet
        header, message_type, address_word, data_word, crc_word = struct.unpack('!HHHHH', data[:10])
        received_crc = calculate_crc([header, message_type, address_word, data_word])

        if received_crc != crc_word:
            print("CRC mismatch. Packet may be corrupted.")
            response = b"CRC Error"
        else:
            print(f"Received packet: Header={header:04X}, MessageType={message_type:04X}, AddressWord={address_word:04X}, DataWord={data_word:04X}, CRC={crc_word:04X}")

            # Respond based on the received command
            if message_type == 0x0001 and (address_word & 0x8000) == 0x8000:
                response = b"Write Completed"
            elif message_type == 0x0001 and (address_word & 0x8000) == 0x0000:
                if (address_word & 0x7FFF) == 0x1000:  # Check if address is 1000
                    response = struct.pack('!H', 0x0BAE)  # Respond with 0BAE
                else:
                    response = b"Read Value"
            else:
                response = b"Unknown Command"

        # Send the response back to the client
        conn.sendall(response)

    # Close the connection
    conn.close()