import socket

# Server configuration
host = '127.0.0.1'  # Localhost
port = 65432  # Port to bind the server

# Create a socket and bind it to the address
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    server_socket.bind((host, port))
    server_socket.listen(1)
    print(f"Server listening on {host}:{port}")

    while True:
        try:
            # Accept incoming connections
            conn, addr = server_socket.accept()
            with conn:
                print(f"Connected to {addr}")
                # Send a message to the client
                conn.sendall(b"Hi, XYZ")
        except KeyboardInterrupt:
            print("\nServer is shutting down.")
            break