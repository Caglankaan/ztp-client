import os
import subprocess
import sys
from manager import ExecCmd
import argparse
import json

def parse_args():
    parser = argparse.ArgumentParser(description='')

    parser.add_argument('--get-report', '-report', type=str, help='Get report with id', default='')
    parser.add_argument('--get-status', '-status', type=str, help='Get status with id', default='')
    parser.add_argument('--get-list', '-list', type=str, help='Get list', default='')
    parser.add_argument('--start-scan', '-start', type=str, help="Start Scan", default='')
    parser.add_argument('--delete-scan', '-delete', type=str, help='Delete scan with id', default='')
    parser.add_argument('--stop-scan', '-stop', type=str, help='Stop scan with id', default='')
    
    args = parser.parse_args()

    return args

def CheckForRootPermission():
    if not 'SUDO_UID' in os.environ.keys():
        print("Must be run as root")
        sys.exit(1)

def main():
    CheckForRootPermission()

    args = parse_args()

    if args.get_report:
          #sudo python3 main.py --get-report id
        report_get_json = '{"id": "'+ args.get_report+'"}'
        my_json = ExecCmd('report get "'+ report_get_json+'"')

    if args.start_scan:
        #sudo python3 main.py --start-scan '{"ssh-username":"kaancaglan",  "ssh-password":"6al2a8yn", "ssh-port":"22", "targets":["192.168.2.147","192.168.2.47"], "brute-force-type":"light", "excluding_functions":["brute_force"]}'
        my_json = ExecCmd('scan new "' + args.start_scan + '"')

    if args.get_status:
          #sudo python3 main.py --get-status id
        my_json = ExecCmd('scan status "' + args.get_status + '"')
        
    if args.get_list:
          #sudo python3 main.py --get-list '{"id":5}'
        my_json =ExecCmd('scan list "' + args.get_list + '"')
    
    if args.stop_scan:
          #sudo python3 main.py --stop-scan id
        report_get_json = '{"id": "'+ args.stop_scan+'"}'
        my_json = ExecCmd('scan stop "'+ report_get_json+'"')

    if args.delete_scan:
          #sudo python3 main.py --delete-scan id
        report_get_json = '{"id": "'+ args.delete_scan+'"}'
        my_json = ExecCmd('scan delete "'+ report_get_json+'"')


if __name__ == '__main__':
    main()

