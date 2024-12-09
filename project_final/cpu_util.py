import subprocess
import time
import re

#initializing counters and othe variables to be zero 
ctr = 0
tot_cpu_usage = 0
tot_mem_usage = 0
avg_cpu = 0
avg_mem = 0

#Running the vmstat command to get the stats
process = subprocess.Popen(['vmstat', '1'], stdout=subprocess.PIPE)


cnt = 0

for line in process.stdout:

    if cnt < 2:
        cnt+=1
        continue

    # print(line.strip())  # Print the output line by line
    data = line.strip()
    data = data.decode('utf-8')
    data = re.split(r'\s+', data.strip())

    if(len(data) < 14):
        cnt=1
        continue
        
#Extracting the percentage of cpu_idle, based on the index in the output
    cpu_idle = int(data[14])
    #Printing the instantenous CPU usage
    print("CPU Usage: ", 100 - cpu_idle, "%")

    #Totalling the cpu usage to help us later with averaging
    tot_cpu_usage+=(100-cpu_idle)

    #Running the command for Memory usage
    result = subprocess.run("free -k | awk '/^Mem:/ {print $2, $4, $7}'", 
                        shell=True, stdout=subprocess.PIPE)

    output = result.stdout.decode('utf-8').strip()

    total_memory, free_memory, available_memory = map(int, output.split())
    memory_utilized_percentage = ((total_memory - available_memory) / total_memory) * 100

    mem_util = ((total_memory - available_memory) / total_memory) * 100
    #Totalling the memory usage to help with average later
    tot_mem_usage+=(mem_util)

    #Printing the instantenous memory usage
    print("mem_util: ", mem_util, '%')
    ctr+=1

    #Printing the average values of cpu usage and memory usage up until now
    print("avg cpu util: ", tot_cpu_usage/ctr, "%, avg mem util: ", tot_mem_usage/ctr, '%')
    print()

    #Repeating this every one second
    time.sleep(1)  