import subprocess
import time
import csv
import re
import os
import random

# Initialization
snapshot_stat_map = ["sent_bytes", "cwin", "sample_rtt", "cur_send_queue", "rwin", "packet_loss_events"]
cumulative_stat_map = ["sum_rtts", "sample_rtt_count", "total_retransmissions", "total_timeouts",
                       "total_bytes_sent", "total_bytes_received", "sum_cwin", "sum_send_buffer_usage", "packet_drops"]

snapshot_columns = {stat: [] for stat in snapshot_stat_map}
cumulative_stats = {stat: 0 for stat in cumulative_stat_map}

mean_interval = 2  # Average interval in seconds
counter = 0
max_send_queue = 0
ini_fast_retrans = 0
ini_timeouts = 0

# Factorial (Poisson distribution helper)
def fact(n):
    ans = 1
    for i in range(1, n + 1):
        ans *= i
    return ans

# Poisson interval generator
def poisson_interval(mean_interval):
    """Generate an interval based on Poisson distribution."""
    return random.expovariate(1 / mean_interval)

# Append to columns
def append_to_column(columns, column_name, data):
    if column_name in columns:
        columns[column_name].append(data)
    else:
        columns[column_name] = [data]

# Write header to files
with open('SnapshotStats.csv', "w", newline='') as snapshot_file, open('CumulativeStats.csv', "w", newline='') as cumulative_file:
    snapshot_writer = csv.writer(snapshot_file)
    cumulative_writer = csv.writer(cumulative_file)

    snapshot_writer.writerow(snapshot_stat_map)  # Write snapshot CSV header
    cumulative_writer.writerow(cumulative_stat_map)  # Write cumulative CSV header

    try:
        while True:
            counter += 1
            print(f"Capturing snapshot {counter}...")

            # Remove old pcap file
            if os.path.exists("capture.pcap"):
                os.remove("capture.pcap")

            # Run tcpdump
            tcpdump_process = subprocess.Popen(
                "sudo tcpdump -U -i lo tcp port 65432 -w capture.pcap", 
                shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            time.sleep(2)  # Capture for a short duration
            tcpdump_process.terminate()
            tcpdump_process.wait()

            snapshot = {stat: 0 for stat in snapshot_stat_map}  # Initialize snapshot stats

            # Extract RTTs and window size
            try:
                tcpdump_output = subprocess.check_output("tcpdump -nn -tt -r capture.pcap 'tcp and src port 65432'", shell=True)
                tcpdump_output = tcpdump_output.decode("utf-8")
                if tcpdump_output:
                    first_line = tcpdump_output.splitlines()[0]
                    words = first_line.split()
                    if "win" in words:
                        win_index = words.index("win") + 1
                        window_size = words[win_index].strip(',')
                        snapshot["rwin"] = int(window_size)
            except Exception as e:
                print(f"Error parsing tcpdump output: {e}")

            # Extract TCP stats using `ss`
            try:
                result = subprocess.run('ss -i -o', shell=True, stdout=subprocess.PIPE, universal_newlines=True)
                lines = result.stdout.splitlines()
                line = lines[-1] if lines else ""
                if 'cwnd:' in line:
                    cwin = int(re.search(r'cwnd:(\d+)', line).group(1))
                    snapshot["cwin"] = cwin
                    cumulative_stats["sum_cwin"] += cwin
                if 'segs_out:' in line:
                    sent_bytes = int(re.search(r'segs_out:(\d+)', line).group(1)) * 1024
                    snapshot["sent_bytes"] = sent_bytes
                    cumulative_stats["total_bytes_sent"] += sent_bytes
            except Exception as e:
                print(f"Error parsing ss output: {e}")

            # Extract RTT and retransmissions
            try:
                rtt_output = subprocess.check_output("tshark -r capture.pcap -Y 'tcp.analysis.ack_rtt' -T fields -e tcp.analysis.ack_rtt", shell=True)
                rtt_output = rtt_output.decode("utf-8").splitlines()
                rtt_values = [float(rtt) for rtt in rtt_output if rtt]
                if rtt_values:
                    sample_rtt = len(rtt_values)
                    snapshot["sample_rtt"] = sample_rtt
                    cumulative_stats["sample_rtt_count"] += sample_rtt
                    cumulative_stats["sum_rtts"] += sum(rtt_values)
            except Exception as e:
                print(f"Error parsing RTTs: {e}")

            # Parse /proc/net/netstat for retransmissions and timeouts
            try:
                netstat_output = subprocess.check_output("cat /proc/net/netstat | grep TcpExt", shell=True).decode('utf-8')
                retrans_match = re.search(r'FastRetransmits\s+(\d+)', netstat_output)
                timeouts_match = re.search(r'Timeouts\s+(\d+)', netstat_output)
                fast_retrans = int(retrans_match.group(1)) if retrans_match else ini_fast_retrans
                timeouts = int(timeouts_match.group(1)) if timeouts_match else ini_timeouts

                snapshot["packet_loss_events"] = fast_retrans - ini_fast_retrans
                cumulative_stats["total_retransmissions"] += fast_retrans - ini_fast_retrans
                cumulative_stats["total_timeouts"] += timeouts - ini_timeouts

                ini_fast_retrans = fast_retrans
                ini_timeouts = timeouts
            except Exception as e:
                print(f"Error parsing retransmissions/timeouts: {e}")

            # Send buffer usage
            try:
                result = subprocess.run('netstat -tn', shell=True, stdout=subprocess.PIPE)
                result = result.stdout.decode('utf-8')
                send_q = re.findall(r"\s+\d+\s+(\d+)\s+", result)
                if send_q:
                    send_queue = int(send_q[0])
                    snapshot["cur_send_queue"] = send_queue
                    max_send_queue = max(max_send_queue, send_queue)
                    cumulative_stats["sum_send_buffer_usage"] += send_queue
            except Exception as e:
                print(f"Error parsing send buffer usage: {e}")

            # Write snapshot stats to CSV
            snapshot_writer.writerow([snapshot[stat] for stat in snapshot_stat_map])

            # Write cumulative stats to CSV
            cumulative_writer.writerow([cumulative_stats[stat] for stat in cumulative_stat_map])

            # Wait for the next interval
            interval = poisson_interval(mean_interval)
            print(f"Waiting {interval:.2f} seconds before the next snapshot.")
            time.sleep(interval)

    except KeyboardInterrupt:
        print("Program interrupted. Exiting...")
