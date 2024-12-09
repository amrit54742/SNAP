# import subprocess
# import time
# import re
# import os

# # List of statistics to collect
# stat_col_map = [
#     "sent_bytes", "nfast_retrans", "ntimeouts", "cwin",
#     "sample_rtt", "cur_send_queue", "rwin",
#     "sum_rtt", "max_send_queue"
# ]

# # Dictionary to store the statistics
# columns = {stat: [] for stat in stat_col_map}

# # Initialize variables
# ini_fast_retrans = 0
# ini_ntimeouts = 0
# max_send_queue = 0

# # Helper function to append a value to the respective column
# def append_to_column(columns, column_name, data):
#     if column_name in columns:
#         columns[column_name].append(data)
#     else:
#         columns[column_name] = [data]

# # Monitor TCP stats during a ping operation
# def monitor_tcp_stats():
#     global ini_fast_retrans, ini_ntimeouts, max_send_queue

#     # Start ping to google.com
#     ping_process = subprocess.Popen(["ping", "google.com", "-c", "10"], stdout=subprocess.PIPE)
#     time.sleep(1)  # Allow some packets to transmit

#     while ping_process.poll() is None:
#         # Step 1: Extract stats from `ss`
#         result_ss = subprocess.run("ss -i", shell=True, stdout=subprocess.PIPE, text=True).stdout
#         if result_ss:
#             lines = result_ss.splitlines()
#             if lines:
#                 last_line = lines[-1]

#                 # Extract Congestion Window (cwin)
#                 cwin_match = re.search(r"cwnd:(\d+)", last_line)
#                 if cwin_match:
#                     append_to_column(columns, "cwin", int(cwin_match.group(1)))

#                 # Extract Sent Bytes
#                 segs_out_match = re.search(r"segs_out:(\d+)", last_line)
#                 if segs_out_match:
#                     append_to_column(columns, "sent_bytes", int(segs_out_match.group(1)) * 1024)

#                 # Extract Current Send Queue
#                 send_queue_match = re.search(r"send ([0-9]+) bytes", result_ss)
#                 if send_queue_match:
#                     send_queue = int(send_queue_match.group(1))
#                     append_to_column(columns, "cur_send_queue", send_queue)

#                     # Update Max Send Queue
#                     if send_queue > max_send_queue:
#                         max_send_queue = send_queue
#                     append_to_column(columns, "max_send_queue", max_send_queue)

#         # Step 2: Extract RTT stats using `tshark`
#         result_rtt = subprocess.run(
#             "tshark -i any -Y 'tcp.analysis.ack_rtt' -T fields -e tcp.analysis.ack_rtt",
#             shell=True, stdout=subprocess.PIPE, text=True
#         ).stdout
#         if result_rtt:
#             rtt_values = [float(value) for value in result_rtt.splitlines()]
#             if rtt_values:
#                 append_to_column(columns, "sample_rtt", rtt_values[-1])
#                 append_to_column(columns, "sum_rtt", sum(rtt_values))

#         # Step 3: Extract Receiver Window Size (rwin) from `tcpdump`
#         tcpdump_output = subprocess.run(
#             "tcpdump -nn -tt -r capture.pcap 'tcp and src port 80'",
#             shell=True, stdout=subprocess.PIPE, text=True
#         ).stdout
#         if tcpdump_output:
#             first_line = tcpdump_output.splitlines()[0]
#             rwin_match = re.search(r"win (\d+)", first_line)
#             if rwin_match:
#                 append_to_column(columns, "rwin", int(rwin_match.group(1)))

#         # Step 4: Extract retransmissions and timeouts from `/proc/net/netstat`
#         with open("/proc/net/netstat", "r") as f:
#             netstat_output = f.read()
#         lines = netstat_output.splitlines()
#         if "TcpExt:" in lines[-1]:
#             stats = lines[-1].split()
#             fast_retrans = int(stats[45])
#             timeouts = int(stats[48])

#             # Append Fast Retransmissions
#             if ini_fast_retrans == 0:
#                 ini_fast_retrans = fast_retrans
#             append_to_column(columns, "nfast_retrans", fast_retrans - ini_fast_retrans)

#             # Append Timeouts
#             if ini_ntimeouts == 0:
#                 ini_ntimeouts = timeouts
#             append_to_column(columns, "ntimeouts", timeouts - ini_ntimeouts)

#     # Save all data to a file
#     with open("MonitorOutput.txt", "w") as outfile:
#         for stat, values in columns.items():
#             outfile.write(f"{stat}:\n{values}\n\n")
#     print("Monitoring completed. Results saved in MonitorOutput.txt.")

# # Run the monitoring function
# if __name__ == "__main__":
#     monitor_tcp_stats()








import socket
import subprocess
import time
import re

# List of statistics to collect
stat_col_map = [
    "sent_bytes", "nfast_retrans", "ntimeouts", "cwin",
    "sample_rtt", "cur_send_queue", "rwin",
    "sum_rtt", "max_send_queue"
]

# Dictionary to store the statistics
columns = {stat: [] for stat in stat_col_map}

# Initialize variables
ini_fast_retrans = 0
ini_ntimeouts = 0
max_send_queue = 0

# Helper function to append a value to the respective column
def append_to_column(columns, column_name, data):
    if column_name in columns:
        columns[column_name].append(data)
    else:
        columns[column_name] = [data]

# Monitor TCP stats during a socket connection
def monitor_tcp_stats():
    global ini_fast_retrans, ini_ntimeouts, max_send_queue

    # Establish socket connection to google.com
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(("google.com", 80))
            s.sendall(b"GET / HTTP/1.1\r\nHost: google.com\r\n\r\n")

            for _ in range(10):  # Monitor for 10 iterations
                time.sleep(1)

                # Step 1: Extract stats from `ss`
                result_ss = subprocess.run("ss -i", shell=True, stdout=subprocess.PIPE, text=True).stdout
                if result_ss:
                    lines = result_ss.splitlines()
                    if lines:
                        last_line = lines[-1]

                        # Extract Congestion Window (cwin)
                        cwin_match = re.search(r"cwnd:(\d+)", last_line)
                        if cwin_match:
                            append_to_column(columns, "cwin", int(cwin_match.group(1)))

                        # Extract Sent Bytes
                        segs_out_match = re.search(r"segs_out:(\d+)", last_line)
                        if segs_out_match:
                            append_to_column(columns, "sent_bytes", int(segs_out_match.group(1)) * 1024)

                        # Extract Current Send Queue
                        send_queue_match = re.search(r"send ([0-9]+) bytes", result_ss)
                        if send_queue_match:
                            send_queue = int(send_queue_match.group(1))
                            append_to_column(columns, "cur_send_queue", send_queue)

                            # Update Max Send Queue
                            if send_queue > max_send_queue:
                                max_send_queue = send_queue
                            append_to_column(columns, "max_send_queue", max_send_queue)

                # Step 2: Extract RTT stats using `tshark`
                result_rtt = subprocess.run(
                    "tshark -i any -Y 'tcp.analysis.ack_rtt' -T fields -e tcp.analysis.ack_rtt",
                    shell=True, stdout=subprocess.PIPE, text=True
                ).stdout
                if result_rtt:
                    rtt_values = [float(value) for value in result_rtt.splitlines()]
                    if rtt_values:
                        append_to_column(columns, "sample_rtt", rtt_values[-1])
                        append_to_column(columns, "sum_rtt", sum(rtt_values))

                # Step 3: Extract Receiver Window Size (rwin) from `tcpdump`
                subprocess.run(
                    "sudo tcpdump -nn -tt -i any -c 1 tcp and src port 80 -w capture.pcap",
                    shell=True, stdout=subprocess.PIPE
                )
                tcpdump_output = subprocess.run(
                    "tcpdump -nn -tt -r capture.pcap 'tcp and src port 80'",
                    shell=True, stdout=subprocess.PIPE, text=True
                ).stdout
                if tcpdump_output:
                    first_line = tcpdump_output.splitlines()[0]
                    rwin_match = re.search(r"win (\d+)", first_line)
                    if rwin_match:
                        append_to_column(columns, "rwin", int(rwin_match.group(1)))

                # Step 4: Extract retransmissions and timeouts from `/proc/net/netstat`
                with open("/proc/net/netstat", "r") as f:
                    netstat_output = f.read()
                lines = netstat_output.splitlines()
                if "TcpExt:" in lines[-1]:
                    stats = lines[-1].split()
                    fast_retrans = int(stats[45])
                    timeouts = int(stats[48])

                    # Append Fast Retransmissions
                    if ini_fast_retrans == 0:
                        ini_fast_retrans = fast_retrans
                    append_to_column(columns, "nfast_retrans", fast_retrans - ini_fast_retrans)

                    # Append Timeouts
                    if ini_ntimeouts == 0:
                        ini_ntimeouts = timeouts
                    append_to_column(columns, "ntimeouts", timeouts - ini_ntimeouts)

    except socket.error as e:
        print(f"Socket error occurred: {e}")
    finally:
        # Save all data to a file
        with open("MonitorOutput.txt", "w") as outfile:
            for stat, values in columns.items():
                outfile.write(f"{stat}:\n{values}\n\n")
        print("Monitoring completed. Results saved in MonitorOutput.txt.")

# Run the monitoring function
if __name__ == "__main__":
    monitor_tcp_stats()












