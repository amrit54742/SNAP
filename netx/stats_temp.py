import subprocess
import time
import csv
import re
import string
import signal
import os

l = 1 / 2  # initializing lambda for poisson distribution
e = 2.71828  # Euler's number
counter = 1

prev_ack_no = 0
stat_col_map = ["sent_bytes", "nfast_retrans", "ntimeouts", "cwin", 'sample_rtt', 'cur_send_queue', 'rwin', 'sum_rtt', 'max_send_queue']  # socket statistics to be collected

# initializing cumulative values to zero
ini_fast_retrans = 0
ini_ntimeouts = 0
max_send_queue = 0

# to calculate the poisson probability for k packet arrivals in l ms of time
def poisson(l, k):
    return ((e ** (-l)) * (l ** k)) / fact(k)

columns = {stat: [] for stat in stat_col_map}  # dictionary to store the statistics values
timeout = 0.0005  # timeout between successive iterations
k = 0  # number of packet arrivals initialized to zero

# Function to append a particular statistic to the required col
def append_to_column(columns, column_name, data):
    if column_name in columns:
        columns[column_name].append(data)
    else:
        columns[column_name] = [data]

with open('MonitorOutput.csv', "w", newline='') as outfile:
    writer = csv.writer(outfile)
    writer.writerow(stat_col_map)  # Write the header of the CSV

    while True:
        counter += 1

        # capturing packets using tcpdump on port 65432
        try:
            if os.path.exists("capture.pcap"):
                os.remove("capture.pcap")
            # Run tcpdump as a separate process
            tcpdump_process = subprocess.Popen(
                "sudo tcpdump -U -i lo tcp port 65432 -w capture.pcap", 
                shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            # Let tcpdump capture for a short while
            time.sleep(2)  # Adjust this as needed

            # Stop tcpdump gracefully after capturing the packets
            tcpdump_process.terminate()
            tcpdump_process.wait()  # Ensure the process terminates correctly
            time.sleep(1)

        except Exception as e:
            print(f"Error with tcpdump process: {e}")
            break

        tcpdump_output = subprocess.check_output("tcpdump -nn -tt -r capture.pcap 'tcp and src port 65432'", shell=True)
        tcpdump_output = tcpdump_output.decode("utf-8")
        if len(tcpdump_output) != 0:
            first_line = tcpdump_output.splitlines()[0]
            
            # Extract the window size (look for 'win' in the line)
            words = first_line.split()
            for i in range(len(words)):
                if words[i] == "win":
                    # Strip "win" and return the numeric value
                    window_size = words[i + 1]
                    window_size = window_size[:-1]
                    append_to_column(columns, 'rwin', int(window_size))
                    break

        # for finding CWin and SentBytes
        result = subprocess.run('ss -i -o', shell=True, stdout=subprocess.PIPE, universal_newlines=True)
        lines_dummy = result.stdout
        lines = result.stdout.splitlines()
        line = lines[len(lines) - 1]
        pos1 = line.find('lastack:')

        if pos1 != -1:
            r = line.split('lastack:')[1]
            s = r.split(' ')[0]
            s = int(s)
            l += s

        pos = line.find('cwnd:')
        if pos != -1:
            r = lines_dummy.split('cwnd:')[1]
            s = r.split(' ')[0]
            s = int(s)
            cwin = s
            if len(columns['rwin']) > len(columns['cwin']):
                append_to_column(columns, 'cwin', cwin)

        pos = line.find('segs_out:')
        if pos != -1:
            r = line.split('segs_out:')[1]
            s = r.split(' ')[0]
            s = int(s)
            segs_out = s
            if len(columns['rwin']) > len(columns['sent_bytes']):
                append_to_column(columns, 'sent_bytes', segs_out * 1024)

        pos2 = line.find("bytes_acked:")
        if pos2 != -1:
            r = line.split('bytes_acked:')[1]
            s = r.split(' ')[0]
            k = cwin
            k = int(k)

        # for finding #SampleRTT and SumRTT
        result = subprocess.check_output("tshark -r capture.pcap -Y 'tcp.analysis.ack_rtt' -T fields -e tcp.analysis.ack_rtt", shell=True)
        result = result.decode('utf-8')
        lines = result.splitlines()
        n = len(lines)
        if n > 0:
            line = lines[-1]
            sample_rtt = n
            append_to_column(columns, 'sample_rtt', sample_rtt)
            sum_rtt = 0
            for i in range(n):
                sum_rtt = sum_rtt + float(lines[i])
            append_to_column(columns, 'sum_rtt', sum_rtt)

        # Send_queue
        result = subprocess.run('netstat -tn', shell=True, stdout=subprocess.PIPE)
        result = result.stdout.decode('utf-8')
        send_q = re.findall(r"\s+\d+\s+(\d+)\s+", result)
        
        if len(send_q) > 0:
            send_queue = send_q[0]
            send_queue = int(send_queue)

            if len(columns['rwin']) > len(columns['cur_send_queue']):
                append_to_column(columns, 'cur_send_queue', send_queue)

            if len(columns['rwin']) > len(columns['max_send_queue']):
                if send_queue > max_send_queue:
                    max_send_queue = send_queue
                append_to_column(columns, 'max_send_queue', max_send_queue)

        # FastRetrans and #timeouts
        cmd = "cat /proc/net/netstat"
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
        result = result.stdout.decode('utf-8')  # Decode the bytes to string
        lines = result.split('\n')
        lines = " ".join(lines)
        print("debugging for lines******************")
        # print(lines)
        parts = lines.split('TcpExt:')
      
        #############################################################################################

        # Check the structure of 'parts'
        if len(parts) >= 3:
            print("DEBUG: Found three or more sections after splitting on 'TcpExt:'.")
            b = parts[1].strip()  # Strip leading/trailing spaces or newlines
            c = parts[2].strip()
        else:
            print("WARNING: Less than 3 sections found after splitting on 'TcpExt:'.")
            b = parts[0].strip()  # Take the first part as 'b'
            c = ''  # Assign empty string to 'c'

        if not c:
            print("ERROR: 'c' is empty or invalid. Cannot parse 'timeouts' and other values.")
            timeouts = "0" 
        else:
            fields = c.split()  
            print(f"DEBUG: Fields in 'c': {fields}")

            if len(fields) > 48: 
                fast_retrans = fields[45].strip()
                timeouts = fields[48].strip()
                print(f"DEBUG: Extracted fast_retrans = '{fast_retrans}'")
                print(f"DEBUG: Extracted timeouts = '{timeouts}'")
            else:
                print("ERROR: Not enough fields in 'c' to extract 'timeouts'.")
                timeouts = "0"  # Assign a default value

        #####################################################################################################
        # fast_retrans = c[45]
        # timeouts = c[48]
        if ini_fast_retrans == 0:
            ini_fast_retrans = fast_retrans
            ini_ntimeouts = timeouts

        # if len(columns['rwin']) > len(columns['nfast_retrans']):
        #     append_to_column(columns, 'nfast_retrans', int(fast_retrans) - int(ini_fast_retrans))
        #     append_to_column(columns, 'ntimeouts', int(timeouts) - int(ini_ntimeouts))

        if len(columns['rwin']) > len(columns['nfast_retrans']):
            try:

                print(f"DEBUG: timeouts = '{timeouts}', ini_ntimeouts = '{ini_ntimeouts}'")
                timeouts = timeouts.strip() or "0"
                ini_ntimeouts = ini_ntimeouts.strip() or "0"
                append_to_column(columns, 'ntimeouts', int(timeouts) - int(ini_ntimeouts))
                ########################
                print(f"DEBUG: fast_retrans = '{fast_retrans}', ini_fast_retrans = '{ini_fast_retrans}'")
                fast_retrans = fast_retrans.strip() or "0"
                ini_fast_retrans = ini_fast_retrans.strip() or "0"
                append_to_column(columns, 'nfast_retrans', int(fast_retrans) - int(ini_fast_retrans))

            except ValueError as e:
                print(f"ValueError: Could not convert timeouts or ini_ntimeouts to int. Error: {e}")
                print(f"DEBUG: timeouts = '{timeouts}', ini_ntimeouts = '{ini_ntimeouts}'")
                print(f"DEBUG: fast_retrans = '{fast_retrans}', ini_fast_retrans = '{ini_fast_retrans}'")
        if l * k > 0:
            timeout = k / (l / counter) / 1000
            if timeout < 1e-8:
                timeout = 0.0005

        writer.writerow([columns[stat] for stat in stat_col_map]) 

        time.sleep(timeout)  