import socket
import struct
import serial

# Function to handle network communication
def handle_network_communication():
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
            data = conn.recv(4)  # Buffer size is 4 bytes
            if not data:
                break

            if len(data) == 4:  # Common packet structure 4 bytes
                address_bits, data_bits = struct.unpack('<HH', data)  # Little-endian format
                rw_bit = (address_bits >> 15) & 0x1  # Extract rw_bit from the most significant bit of address_bits
                address_bits = address_bits & 0x7FFF  # Mask out the rw_bit

                print(f"Received packet: RW={rw_bit}, Address={address_bits:04X}, Data={data_bits:04X}")

                # Respond based on the received command
                if rw_bit == 0:
                    response = struct.pack('<I', 0xFFFF)  # Respond with "Write Completed" in hex (little-endian)
                else:
                    if address_bits == 0x602B:  # Check if address is 0x602B
                        response = struct.pack('!I', 0b11100000001010110000111100000000)  # Respond with 11100000001010110000000000001111
                    else:
                        response = struct.pack('!I', 0b11100000001010110000000100000000)  # Respond with 11100000001010110000000000000001
            else:
                response = struct.pack('!I', 0xAAAA)  # Respond with "Invalid Packet" in hex (little-endian)

            conn.sendall(response)
        conn.close()

# Function to handle serial communication
def handle_serial_communication():
    com_port = 'COM2'  # Change this to the desired COM port
    ser = serial.Serial(com_port, 9600, timeout=1)
    print(f"Server listening on {com_port}")

    while True:
        data = ser.read(4)  # Buffer size is 4 bytes
        if not data:
            continue

        if len(data) == 4:  # Common packet structure 4 bytes
            address_bits, data_bits = struct.unpack('<HH', data)  # Little-endian format
            rw_bit = (address_bits >> 15) & 0x1  # Extract rw_bit from the most significant bit of address_bits
            address_bits = address_bits & 0x7FFF  # Mask out the rw_bit

            print(f"Received packet: RW={rw_bit}, Address={address_bits:04X}, Data={data_bits:04X}")

            # Respond based on the received command
            if rw_bit == 0:
                response = struct.pack('<I', 0xFFFF)  # Respond with "Write Completed" in hex (little-endian)
            else:
                if address_bits == 0x602B:  # Check if address is 0x602B
                    response = struct.pack('!I', 0b11100000001010110000111100000000)  # Respond with 11100000001010110000000000001111
                else:
                    response = struct.pack('!I', 0b11100000001010110000000100000000)  # Respond with 11100000001010110000000000000001
        else:
            response = struct.pack('!I', 0xAAAA)  # Respond with "Invalid Packet" in hex (little-endian)

        ser.write(response)

if __name__ == "__main__":
    connection_type = input("Enter connection type (network/com): ").strip().lower()
    if connection_type == "network":
        handle_network_communication()
    elif connection_type == "com":
        handle_serial_communication()
    else:
        print("Invalid connection type. Please enter 'network' or 'com'.")