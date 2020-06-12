#!/usr/bin/env python3

from http.server import BaseHTTPRequestHandler, HTTPServer
from json import dumps
import json
import re
import json
import os
import sys
from enum import Enum
import signal
import subprocess
from multiprocessing import Pipe
from bson import ObjectId
from pprint import pprint
from pymongo import MongoClient
from bson.json_util import loads
from bson.json_util import dumps

class ScanStatusType(Enum):
    FAILED = -1
    ONGOING = 1
    STOPPED = 2
    DONE = 3

def ScanNew(db, data, str_v):
    subprocess.run(["/usr/bin/python3","/home/kaancaglan/dev/ZTP/ztp-client/main.py","--start-scan", data["data"]])
    cursor = list(db["scan"].find().sort([('creation_date', -1)]).limit(1))[0]
    return cursor["_id"]

def ScanList(db, data):
    limit = 3
    if(data["limit"]):
        limit = data["limit"]
    scanArr = []

    for scan in db["scan"].find().limit(int(limit)):
        scanArr.append(scan)
        print("Scan: ", scan)

    return scanArr


def ScanStatus(db, data):
    if("id" not in data.keys()):
        print("bad request, id needed!")
        sys.exit(1)
    result = db["scan"].find_one({"_id": ObjectId(data["id"])})
    scan_status_file = open('/etc/ztp/scan_outputs/scan_status','w')
    scan_status_file.write(str(result))
    print("result: ", result)
    return result["status"]


def ScanDelete(db, data):
    scanId = ObjectId(data["id"])
    targetIds = db["target"].find({"scan_hash":scanId})
    for i in targetIds:
        db["dynamicreport"].delete_many({"target":ObjectId(i["_id"])})
    
    db["scan"].delete_one({"_id":scanId})
    db["target"].delete_many({"scan_hash":scanId})
    
    print("Scan reports are deleted")
    

def ScanStop(db, data):
    if("id" not in data.keys()):
        print("bad request, id needed!")
        sys.exit(1)
    
    scan_result = db["scan"].find_one({"_id": ObjectId(data["id"])})
    if(int(scan_result["status"]) != ScanStatusType.ONGOING.value):
        print("Scan's status is not ongoing!")
        sys.exit(1)

    if(int(scan_result["pid"]) <= 0):
        print("'pid' is <= 0")
        sys.exit(1)
    
    if(os.kill(int(scan_result["pid"]), signal.SIGTERM)): #or signal.SIGKILL 
        print("Couldn't stop the scan")
        sys.exit(1)

    db["scan"].update_one({"_id": ObjectId(data["id"])}, {"$set":{
        "status":2
    }})
    print("Stopped scan successfuly")

def ReportGet(db, data):
    if("id" not in data.keys()):
        print("bad request, id needed!")
        sys.exit(1)
    scan_result = db["scan"].find_one({"_id": ObjectId(data["id"])})
    
    if(not scan_result):
        print("No entry found!")
        sys.exit(1)
    if(int(scan_result["status"] == 2)):
        print("This scan has been stopped!")
        
    doc = {"creation_date": scan_result["creation_date"], "end_date": scan_result["end_date"], "status": scan_result["status"], "targets":[]}
    target_cursor = db["target"].find({"scan_hash": ObjectId(data["id"])})

    for target in target_cursor:
        target_doc = {"ip": target["ip"], "os": target["os"], "reports":[]}
        report_cursor = db["dynamicreport"].find({"target": ObjectId(target["_id"])})

        for report in report_cursor:
            open_state = {"static":"","dynamic":""}
            
            rep_opt = db["staticreport"].find_one({"target": ObjectId(target["_id"])})
            if(rep_opt):
                open_state["static"] = str(rep_opt)
            
            open_state["dynamic"] = report["dynamic_report"]
            
            target_doc["reports"].append(open_state)
        doc["targets"].append(target_doc)

    pprint(doc)

    return doc


def ExecCmd(cmd):
    client = MongoClient("127.0.0.1")
    db=client["ztp-dev"]
    match = cmd.split(" ")
    cmd = cmd.replace(match[0]+" "+match[1]+" ","")
    str_v = cmd
    json_dict = json.loads(str_v[1:-1])

    if(match[0] == "scan"):
        if(match[1] == "new"):
            return ScanNew(db, json_dict,str_v)
        elif(match[1] == "list"):
            return ScanList(db, json_dict)
        elif(match[1] == "status"):
            return ScanStatus(db, json_dict)
        elif(match[1] == "delete"):
            return ScanDelete(db, json_dict)
        elif(match[1] == "stop"):
            return ScanStop(db, json_dict)
    elif(match[0] == "report"):
        if(match[1] == "get"):
            return ReportGet(db, json_dict)
    
""" The HTTP request handler """
class RequestHandler(BaseHTTPRequestHandler):

  def _send_cors_headers(self):
      """ Sets headers required for CORS """
      self.send_header("Access-Control-Allow-Origin", "*")
      self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
      self.send_header("Access-Control-Allow-Headers", "x-api-key,Content-Type")

  def send_dict_response(self, d):
      """ Sends a dictionary (JSON) back to the client """
      self.wfile.write(bytes(dumps(d), "utf8"))

  def do_OPTIONS(self):
      self.send_response(200)
      self._send_cors_headers()
      self.end_headers()

  def do_GET(self):
      self.send_response(200)
      self._send_cors_headers()
      self.end_headers()

      response = {}
      response["status"] = "OK"
      self.send_dict_response(response)

  def do_POST(self):
    self.send_response(200)
    self._send_cors_headers()
    self.send_header("Content-Type", "application/json")
    self.end_headers()

    dataLength = int(self.headers["Content-Length"])
    data = self.rfile.read(dataLength)

    #coming_data = json.loads(data.decode('utf-8'))["data"]

    response = {}
    response["status"] = "OK"

    try:
        son_data = json.loads(data.decode('utf-8'))
    except json.decoder.JSONDecodeError:
        self.send_error('Invalid JSON', 401)
        return

    path = self.path
    
    if path == '/scan/new':
        status_id = ExecCmd("scan new "+ "'"+data.decode('utf-8')+"'")
        self.send_dict_response(status_id)

    elif path == '/report/get':
        report = ExecCmd("report get "+ "'"+data.decode('utf-8')+"'")
        self.send_dict_response(report)

    elif path == '/scan/list':
        scan_list = ExecCmd("scan list "+ "'"+data.decode('utf-8')+"'")
        self.send_dict_response(scan_list)

    elif path == '/scan/status':
        scan_status = ExecCmd("scan status "+ "'"+data.decode('utf-8')+"'")
        self.send_dict_response(scan_status)

    elif path == '/scan/delete':
        scan_delete = ExecCmd("scan delete "+ "'"+data.decode('utf-8')+"'")
        self.send_dict_response({"success":"deleted!"})

    elif path == '/scan/stop':
        scan_stop = ExecCmd("scan stop "+ "'"+data.decode('utf-8')+"'")
        self.send_dict_response({"success":"stopped!"})

    #self.send_dict_response(response)


print("Starting server")
httpd = HTTPServer(("127.0.0.1", 8001), RequestHandler)
print("Hosting server on port 8001")
httpd.serve_forever()