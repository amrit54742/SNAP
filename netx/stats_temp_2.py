# import subprocess
# import time
# import csv
# import re
# import os
# import random

# # Socket statistics to be collected
# snapshot_stats = ["send_buffer", "cwnd", "sample_rtt", "rwin", "packet_loss_events"]
# cumulative_stats = ["sum_rtt", "sample_rtt_count", "total_retransmissions", "total_timeouts", 
#                     "bytes_sent", "bytes_received", "sum_cwnd", "sum_send_buffer", "packet_drops"]

# # Initialize cumulative values
# cumulative = {stat: 0 for stat in cumulative_stats}

# # Helper function to append to the columns
# def append_to_column(columns, column_name, data):
#     if column_name in columns:
#         columns[column_name].append(data)
#     else:
#         columns[column_name] = [data]

# # Poisson interval
# def poisson_interval(mean_interval):
#     return random.expovariate(1 / mean_interval)

# mean_interval = 2  # Average interval in seconds
# counter = 0

# with open('MonitorOutput.csv', "w", newline='') as outfile:
#     writer = csv.writer(outfile)
#     writer.writerow(snapshot_stats + cumulative_stats)  # Write CSV header

#     while True:
#         counter += 1

#         # Start capturing packets
#         if os.path.exists("capture.pcap"):
#             os.remove("capture.pcap")
#         tcpdump_process = subprocess.Popen(
#             "sudo tcpdump -U -i lo tcp port 65432 -w capture.pcap", 
#             shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
#         )
#         time.sleep(2)
#         tcpdump_process.terminate()
#         tcpdump_process.wait()
        
#         snapshot = {}  # Snapshot stats for this iteration
        
#         # Parse RTT and window size
#         try:
#             tcpdump_output = subprocess.check_output("tcpdump -nn -tt -r capture.pcap 'tcp and src port 65432'", shell=True)
#             tcpdump_output = tcpdump_output.decode("utf-8")
#             if tcpdump_output:
#                 first_line = tcpdump_output.splitlines()[0]
#                 words = first_line.split()
#                 if "win" in words:
#                     win_index = words.index("win") + 1
#                     window_size = words[win_index].strip(',')  # Remove trailing comma or characters
#                     snapshot["rwin"] = int(window_size)
#                 else:
#                     snapshot["rwin"] = 0

#         except Exception as e:
#             print(f"Error parsing tcpdump output: {e}")
#             snapshot["rwin"] = 0

#         # Parse RTT sample from tshark
#         try:
#             result = subprocess.check_output("tshark -r capture.pcap -Y 'tcp.analysis.ack_rtt' -T fields -e tcp.analysis.ack_rtt", shell=True)
#             rtt_samples = list(map(float, result.decode('utf-8').splitlines()))
#             snapshot["sample_rtt"] = len(rtt_samples)
#             snapshot["sum_rtt"] = sum(rtt_samples)
#             cumulative["sum_rtt"] += snapshot["sum_rtt"]
#             cumulative["sample_rtt_count"] += snapshot["sample_rtt"]
#         except Exception as e:
#             print(f"Error parsing RTT: {e}")
#             snapshot["sample_rtt"] = 0
#             snapshot["sum_rtt"] = 0

#         # Parse congestion window, send buffer, etc., using `ss`
#         result = subprocess.run('ss -i -o', shell=True, stdout=subprocess.PIPE, universal_newlines=True)
#         lines = result.stdout.splitlines()
#         if lines:
#             last_line = lines[-1]
#             cwin_match = re.search(r'cwnd:(\d+)', last_line)
#             send_buffer_match = re.search(r'sndbuf:(\d+)', last_line)
#             bytes_acked_match = re.search(r'bytes_acked:(\d+)', last_line)
#             snapshot["cwnd"] = int(cwin_match.group(1)) if cwin_match else 0
#             snapshot["send_buffer"] = int(send_buffer_match.group(1)) if send_buffer_match else 0
#             cumulative["sum_cwnd"] += snapshot["cwnd"]
#             cumulative["sum_send_buffer"] += snapshot["send_buffer"]

#         # Parse retransmissions and timeouts
#         netstat_output = subprocess.check_output("cat /proc/net/netstat | grep TcpExt", shell=True).decode('utf-8')
#         try:
#             retrans_match = re.search(r'FastRetransmits\s+(\d+)', netstat_output)
#             retransmissions = int(retrans_match.group(1)) if retrans_match else 0

#             timeout_match = re.search(r'Timeouts\s+(\d+)', netstat_output)
#             timeouts = int(timeout_match.group(1)) if timeout_match else 0

#             cumulative["total_retransmissions"] = retransmissions
#             cumulative["total_timeouts"] = timeouts
#         except Exception as e:
#             print(f"Error parsing retransmissions/timeouts: {e}")


#         # Calculate packet drops (optional heuristic based on retransmissions)
#         cumulative["packet_drops"] = cumulative["total_retransmissions"] + cumulative["total_timeouts"]

#         # Merge snapshot and cumulative stats, write to CSV
#         stats_row = [snapshot.get(stat, 0) for stat in snapshot_stats] + [cumulative.get(stat, 0) for stat in cumulative_stats]
#         writer.writerow(stats_row)

#         # Wait for the next interval
#         time.sleep(poisson_interval(mean_interval))



###########################################################################################################