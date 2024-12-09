import socket
import threading
import sys
import time

bufferSize = 1024

def recv_from_client(conn, img_output):
    global bufferSize
    seq_num = 0
    seq_num_data = {}
    buf = b''
    while True:
        try:
            chunk = conn.recv(bufferSize)
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

    # in case the packets in buf havent been added to the data dictionary
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

    # write to output file
    with open(img_output, "wb") as file:
        for i in range(seq_num + 1):
            write_packet_data = seq_num_data[i]
            file.write(write_packet_data)
        print("output written to file!")

def send_to_client(conn, image_file):
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
                    conn.send(message)
                    break
                except:
                    continue
            print("sent packet with sequence num {} and last flag {}".format(seq_num, last_bytes))
   
            if last_bytes == 1:
                break
   
            seq_num = (seq_num + 1)%65536

    print('Image file has been shared')

def main():
    threads = []
    global FLAG

    # server IP and port
    HOST = '10.0.0.2'
    serverPort = 20002

    img_output = "serverOutput.mp4"
    image_file = "vid2.mp4"

    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)    # tcp socket

    serverSocket.bind((HOST, serverPort))
    print("Socket binded.")

    # socket for listening to connection requests
    serverSocket.listen(1)
    print("Listening.....")

    # socket for data transfer
    connectionSocket, addr = serverSocket.accept()
    print('Connection Established with a Client on ', addr, '\n')

    connectionSocket.settimeout(5)

    # separate threads for sending and receiving
    t_rcv = threading.Thread(target=recv_from_client, args=(connectionSocket,img_output))
    t_send = threading.Thread(target=send_to_client, args=(connectionSocket,image_file))

    threads.append(t_rcv)
    threads.append(t_send)
    t_send.start()
    t_rcv.start()

    t_send.join()
    t_rcv.join()

    print('\nEXITING')
    connectionSocket.close()
    serverSocket.close()

    sys.exit()

if __name__ == '__main__':
    main()