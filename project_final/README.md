
# Computer Networks Group Project

## TCP connection monitoring for an application deployed as microservice in a Kubernetes cluster

This Project is made by:    
Name 1 : Ahmik Virani (ES22BTECH11001) <br>
Name 2 : Devraj (ES22BTECH11011) <br>
Name 3 : Divya Rajparia (ES22BTECH11013) <br>
Name 4 : Gupta Dhawal Pravin (ES22BTECH11015) <br>
Name 5 : Prashans Chauhan (ES22BTECH11028) <br>
Name 6 : Praveen Prakash Ayila (ES22BTECH11029) <br>

## Overview

This project consists of a client and server TCP full duplex connection, along with programs that monitor socket statistics and extract CPU and memory utilization information. <br>
The files submitted are:
1. client.py
2. server.py
3. monitor.py
4. cpu_util.py

Other files which you need:
1. [DRIVE LINK](https://drive.google.com/drive/folders/14aWBpB--JDoZ3lheso-l_OFK1avn3Qx5?usp=sharing) : Download these files and save on the same folder as the project 
2. Ensure that the names of the downloaded files are:
    - vid1.mp4
    - vid2.mp4

## Conifiguring Mininet Prompt
1. Open the VM (mininet) terminal and go to the directory where the files related to this project are saved
2. Run the following command
```bash
sudo mn
```
3. Open 2 instances of host h1 and 1 instance of host h2
    - Enter this command twice on the VM terminal (one to run the client.py and the other for monitor.py):
    ```bash
    xterm h1
    ```
    - Enter this command once on the VM terminal (we will run server.py here):
    ```bash
    xterm h2
    ```
4. We have run on the following configurations, ensure to set channel configurations before running to emulate realistic scenario:
    - Bandwidth: 10Mbps
    - Loss: 10%
    - Delay: 10ms
5. Open an additional instance of VM terminal (we will run cpu_util.py here)

## Deployment
Note: Following steps must be done sequentially and in quick succession to ensure any average calculations required to find cpu utilization or socket statistics are not biased <br><br>
1. Run the following on the VM terminal 
   ```bash
   python3 cpu_util.py
   ```
2. Run the following on h2
   ```bash
   python3 server.py
   ```
3. Run the following on one instance of h1 <br>(This step is only required if you need to monitor the socket)
   ``` bash
   python3 monitor.py
   ```
4. Run the following on the other instace of h1
   ```bash
   python3 client.py
   ```

## Output
The names of output files would be:
1. clientOutput.mp4
2. serverOutput.mp4
3. MonitorOutput : Set of all logs for every iteration
4. FinalOutput : Final collective logs