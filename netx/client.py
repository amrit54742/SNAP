import socket
import time

# Server configuration
host = '127.0.0.1'  # Server address (localhost)
port = 65432  # Port to connect to

while True:
    # Create a socket and connect to the server
    time.sleep(1)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((host, port))
        
        # Receive the message from the server
        data = client_socket.recv(1024)
        print(f"Received from server: {data.decode()}")
