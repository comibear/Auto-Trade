import os 

def log(data):
    open("./Trading_log.log", "a").write(data + "\n")
    return