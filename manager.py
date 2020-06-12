import re
import json
import os
import sys
from pymongo import MongoClient
from enum import Enum
from bson.json_util import loads
from bson.json_util import dumps
import signal
from pprint import pprint
from random import randint
import subprocess
from multiprocessing import Pipe
from bson import ObjectId

class ScanStatusType(Enum):
    FAILED = -1
    ONGOING = 1
    STOPPED = 2
    DONE = 3

def ScanNew(db, data,str_v):

    if(not data["ssh-username"] or not data["ssh-password"] or not data["targets"] ):
        return "Some fields are missing in the JSON!"
    rside, wside = os.pipe()
    
    #Child
    pid = os.fork()
    if(pid < 0):
        print("Pid is less than 0, something wrong!")
        sys.exit(1)

    if(pid == 0):
        os.close(rside)
        os.dup2(wside,1)
        os.dup2(wside, 2)
        #os.environ["LD_LIBRARY_PATH"] = "/your/cxxdriver/prefix/lib"
        subprocess.run(["/usr/local/bin/ztp",str_v.replace("'","")], env = os.environ)
        sys.exit(1)

    #Parent
    os.close(wside)
    pyrside = os.fdopen(rside)


    for line in pyrside:
        print("Child (stdout or stderr) said: <%s>"%line)

    pid, status = os.waitpid(pid,0)
    
    cursor = list(db["scan"].find().sort([('creation_date', -1)]).limit(1))[0]
    print("Scan started. Scan id is: ",cursor["_id"])
    scan_status_file = open('/etc/ztp/scan_outputs/scan_new','w')
    scan_status_file.write(str(cursor["_id"]))
    return str(cursor["_id"])


def ScanList(db, data):
    limit = 3
    if(data["limit"]):
        limit = data["limit"]
    scanArr = []

    scan_list_file = open('/etc/ztp/scan_outputs/scan_list','w')
    for scan in db["scan"].find().limit(int(limit)):
        scanArr.append(scan)
        print("Scan: ", scan)
        scan_list_file.write(str(scan)+"\n")

    return scanArr


def ScanStatus(db, data):
    if("id" not in data.keys()):
        print("bad request, id needed!")
        sys.exit(1)
    result = db["scan"].find_one({"_id": ObjectId(data["id"])})
    scan_status_file = open('/etc/ztp/scan_outputs/scan_status','w')
    scan_status_file.write(str(result))
    print("Scan Status: ", result)
    return str(result)


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


    scan_status_file = open('/etc/ztp/scan_outputs/report_scan.json','w')
    scan_status_file.write(str(doc))
    pprint(doc)

    return(str(doc))


def ExecCmd(cmd):
    client = MongoClient("127.0.0.1")
    db=client["ztp-dev"]
    match = cmd.split(" ")

    cmd = cmd.replace(match[0]+" "+match[1]+" ","")
    str_v = cmd
    json_dict = json.loads(str_v[1:-1])
    
    if(match[0] == "scan"):
        if(match[1] == "new"):
            return ScanNew(db, json_dict,str_v[1:-1])
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
    

cmd = 'scan new \'{\"ssh-username\":\"kaancaglan\",  \"ssh-password\":\"6al2a8yn\", \"ssh-port\":\"22\", \"targets\":[\"192.168.2.47\", \"192.168.2.147\"], \"excluding_functions\":[]}\''
cmd2 = 'scan list \'{\"limit\":\"2\"}\''
cmd3 = 'scan status \'{\"id\":\"5e760a08e3872b3b4f523e72\"}\''
cmd4 = 'scan delete \'{\"id\":\"5e7777a5e3872b68107e4f82\"}\''
cmd5 = 'report get \'{\"id\":\"5e777c74e3872b07477ec402\"}\''
cmd6 = 'scan stop \'{\"id\":\"5e777c74e3872b07477ec402\"}\''
#ExecCmd(cmd)
#ExecCmd(cmd)
