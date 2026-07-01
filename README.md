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
## Status 

- Milestone 1: Init repo 
