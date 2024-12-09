# import socket

# # Server configuration
# host = '127.0.0.1'  # Localhost
# port = 65432  # Port to bind the server

# # Create a socket and bind it to the address
# with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
#     server_socket.bind((host, port))
#     server_socket.listen(1)
#     print(f"Server listening on {host}:{port}")

#     while True:
#         try:
#             # Accept incoming connections
#             conn, addr = server_socket.accept()
#             with conn:
#                 print(f"Connected to {addr}")
#                 # Send a message to the client
#                 conn.sendall(b"Hi, XYZ")
#         except KeyboardInterrupt:
#             print("\nServer is shutting down.")
#             break



import socket
import threading

# Server configuration
host = '127.0.0.1'  # Localhost
port = 65432  # Port to bind the server

def handle_client(conn, addr):
    print(f"Connected to {addr}")
    try:
        while True:
            try:
                # Receive data from the client
                data = conn.recv(1024)
                if not data:
                    print(f"Client {addr} disconnected.")
                    break

                print(f"Received from client {addr}: {data.decode()}")

                # Send a response to the client
                conn.sendall(b"Hello, Client!")
            except Exception as e:
                print(f"Error with client {addr}: {e}")
                break
    finally:
        conn.close()

# Create a socket and bind it to the address
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    server_socket.bind((host, port))
    server_socket.listen()
    print(f"Server listening on {host}:{port}")

    try:
        while True:
            # Accept a new connection
            conn, addr = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.daemon = True
            client_thread.start()
    except KeyboardInterrupt:
        print("\nServer is shutting down.")
    except Exception as e:
        print(f"Server error: {e}")