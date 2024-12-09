import socket
import threading
import sys
import time
bufferSize = 1024

def send_to_server(socket_tcp, image_file):
    global FLAG
    global bufferSize
    with open(image_file, "rb") as img:
        seq_num = 0
        while True:
            packet_data = img.read(1021)

            if len(packet_data) < 1021:
                last_bytes = 1
            else:
                last_bytes = 0

            seq_num_bytes = seq_num.to_bytes(2, byteorder='big')
            last_flag_bytes = last_bytes.to_bytes(1, byteorder='big')

            message = seq_num_bytes + last_flag_bytes + packet_data

            # keep trying to send, to handle the case of timeout due to send buffer being full
            while True:
                try:
                    socket_tcp.send(message)
                    break
                except:
                    continue
            print("sent packet with sequence num {} and last flag {}".format(seq_num, last_bytes))
       
            if last_bytes == 1:
                break
       
            seq_num = (seq_num + 1)%65536

        print('Image file has been shared')

def recv_from_server(connectionSocket, img_output):
    global bufferSize

    seq_num = 0
    seq_num_data = {}
    buf = b''
    while True:
        try:
            chunk = connectionSocket.recv(bufferSize)
        except socket.timeout:
            break
        if not chunk:
            break
        buf += chunk
        while len(buf) >= bufferSize:
            recievedMessage = buf[0:bufferSize]
            buf = buf[bufferSize:]

            seq_num_bytes = recievedMessage[0:2]
            last_flag_bytes = recievedMessage[2:3]
            packet_data = recievedMessage[3:]

            seq_num = int.from_bytes(seq_num_bytes, byteorder='big')
            last_flag = int.from_bytes(last_flag_bytes, byteorder='big')

            seq_num_data[seq_num] = packet_data
            print("Received packet with sequence number {} and last flag {} ".format(seq_num, last_flag))

            if(last_flag == 1):
                print("Last Byte received with sequence number {} and last flag {}".format(seq_num, last_flag))
                break
    # in case the buffer has data not added to the data dictionary
    if len(buf) > 0:
        recievedMessage = buf
        buf = b''

        seq_num_bytes = recievedMessage[0:2]
        last_flag_bytes = recievedMessage[2:3]
        packet_data = recievedMessage[3:]
        seq_num_data[seq_num] = packet_data

        seq_num = int.from_bytes(seq_num_bytes, byteorder='big')
        last_flag = int.from_bytes(last_flag_bytes, byteorder='big')
        seq_num_data[seq_num] = packet_data

        print("Received packet with sequence number {} and last flag {} ".format(seq_num, last_flag))

        if(last_flag == 1):
            print("Last Byte received with sequence number {} and last flag {}".format(seq_num, last_flag))

    # write output to file
    with open(img_output, "wb") as file:
        for i in range(seq_num + 1):
            write_packet_data = seq_num_data[i]
            file.write(write_packet_data)
        print("output written to file!")

# this is main function
def main():
    threads = []

    # server IP and port
    HOST = '10.0.0.2'
    PORT = 20002

    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # tcp socket for data transfer
    clientSocket.bind(('10.0.0.1', 20001))                             # bind socket to client IP and port

    # connect to server
    clientSocket.connect((HOST, PORT))
    print('Client is connected to the Server\n')

    clientSocket.settimeout(5)

    image_file = "vid1.mp4"
    output_file = "clientOutput.mp4"
    
    #separate threads for sending and receiving
    t_send = threading.Thread(target=send_to_server, args=(clientSocket, image_file))
    t_rcv = threading.Thread(target=recv_from_server, args=(clientSocket, output_file))

    threads.append(t_send)
    threads.append(t_rcv)
    t_send.start()
    t_rcv.start()

    t_send.join()
    t_rcv.join()

    clientSocket.close()
    print('\nEXITING')
    sys.exit()

if __name__ == '__main__':
    main()