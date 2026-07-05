# Network Traffic Emulation on Docker


This project is directly related to my IPS repo. The aim of this repo is to build and test a docker-based network traffic emulator that will be comprised of a trivial sub-net. This will serve as the prototype of the full size network traffic emulator. 

The docker enviroment will include 5 containers locally. 
## Phase 1

Goal: Generate and capture traffic: generate -> capture -> extract -> label -> train a model that can learn on the data from this docker based network traffic emulator before scaling up.

The docker env is made up of: 
/ container / role / 
/ victim / Juice Shop (web) + sshd - single target / 
/ attacker / nmap, hping3, slowloris, hydra / 
/ ws / benign host (curl / ssh loops) / 
/ cap / shares victim network namespace: tcpdump -> pcap -> extractor (CICFlowMeter -> flows.csv) / 
/ ctl / controller: scehdules benign + attacks, logs windows, runs labeller /

Attack Families: 
- port scan (recon)
- DoS (SYN flood + slowloris) (DDoS will be added later)
- SSH brute-force


Note: The extractor proposed for this project is CICFlowMeter () - but this will change for the final version of the network traffic emulator to Zeek. The reason for this is due to the fact that my current IPS pipeline already supports the feature extraction format of CICFlowMeter - but for the final IPS pipeline the plan is to use Zeek as we can extract features from the application layer and other richer features. Everything else will stay relatively the same. 

# Stage

1. Setting up simple 2 container docker env. 
2. Implement full 5 container enviroment to finnalise network topology (note that the full Juice web page image is not required at this stage - an open web port is sufficient)
3. Capture flow of benign traffic (HTTP browsing - including deadlinks -> 404, and occasional SSH logins attemps that lead to clean disconnects). 
    - implement benign traffic generator
    - Run generator script for 30s and capture traffic
    - Verify traffic by checking victim logs
4. Implement attack traffic generator - currently only bruteforce password attempts, portscan (recon) and DoS (SYN flood)
5. Implement the main orchestrater of the netem 'ctl'. Main purpose is to schedule attacks in a bed of benign traffic. 
6. Implement the extractor container and build. Using python cicflowmeter package - not java tool
7. Label captured flows - binary labelling: attack/benign
8. Scale up scenario - larger benign bed + diversing and pacing attacks. ~45 mins capture + extract + label
9. Prepare the IPS pipeline to receive the scaled up full run flow file. 
10. Refactor the netem generator to produce run B dataset. 
    - randomise packet sizes but randomising web page size (randomises the request body sizes)
    - randomise gaps between packets (before was a fixed gap time)
    - randomise DoS intervals - different slowloris durations 
    - different port scanning timings
    - different wordlist for bruteforce
    - diversify benign traffic patterns so that it can't be memorised - different paths/resources

## Status 

- Milestone 1: Init repo 
**DONE**
- Milestone 2: 5 containers built, live and reachable. 
**DONE**
- Milestone 3: Capture first full traffic run (with attacks). 
**DONE**
- Milestone 4: Extract relevant features from pcap files. 
**DONE** 
- Milestone 5: Capture scaled up network scenario (run A) and train xgboost on labelled data. 
**DONE** 
- Milestone 6: Generate a second run to compare the performnace of the original model trained on run A. 
**DONE**

## Current Stage:
- NetemDocker is working as required: generate -> capture -> label -> IPS pipeline 
- No further changes planned - repo is stalled. 


