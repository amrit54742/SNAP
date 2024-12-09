# import socket
# import time

# host = '127.0.0.1' 
# port = 65432  

# # while True:
# #     # Create a socket and connect to the server
# #     time.sleep(1)
# with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
#     client_socket.connect((host, port))
#     while True:
#         # Create a socket and connect to the server
#         time.sleep(1)
#         # Receive the message from the server
#         data = client_socket.recv(1024)
#         print(f"Received from server: {data.decode()}")




# Client Code
import socket
import time

host = '127.0.0.1' 
port = 65432  

# Create a socket and connect to the server
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
    client_socket.connect((host, port))
    print("Connected to the server.")

    while True:
        try:
            # Send a request to the server
            client_socket.sendall(b"Hello, Server!")

            # Receive the response from the server
            data = client_socket.recv(1024)
            if not data:
                print("Server closed the connection.")
                break

            print(f"Received from server: {data.decode()}")

            # Wait for 1 second before sending the next request
            time.sleep(1)
        except KeyboardInterrupt:
            print("\nClient is shutting down.")
            break
        except Exception as e:
            print(f"Error: {e}")
            break