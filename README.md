# ZTP-Client

This repo is a client module for ZTP-Core.

client.py is a client code to run from terminal, server.py is a server code who connects with client.py. To scan system from ZTP-Ui you have to run server.py with sudo.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install pymongo and bson.

```bash
pip3 install pymongo
pip3 install bson
```

## Usage
You can use either public-key-path or ssh-password do not use them together. If you want to exclude some functions from scan you can add them to array for example "excluding_functions": ["linux_local_security"]


Excludable functions are:
 1)"linux_local_security"
 2)"ftp"
 3)"brute_force"
 
 To start scan:
```bash
sudo python3 client.py --start-scan '{"ssh-username":"username", "public-key-path":"/home/username/publickey", "ssh-password":"password", "ssh-port":"22", "targets":["ip1","ip2"],"brute-force-type":"light", "brute-force-path": "/home/username/passwords.txt", "excluding_functions":["brute_force"], "nmap": "nmap --unprivileged -vv"}'
```

To get status of scan:
```bash
sudo python3 client.py --get-status id
```
To get list of scans:
```bash
sudo python3 client.py --get-list '{"id":5}'
```
To stop scan:
```bash
sudo python3 client.py --stop-scan id
```
To delete scan:
```bash
sudo python3 client.py --delete-scan id
```
Or if you want to scan system from ZTP-Ui you just have to open server.py

```bash
sudo python3 server.py
```