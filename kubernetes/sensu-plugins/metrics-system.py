#!/usr/bin/env python3
import psutil
import time

def get_system_metrics():
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Format metrics in Nagios perfdata format (without % signs)
    metrics = [
        f"cpu_percent={cpu_percent}",
        f"memory_percent={memory.percent}",
        f"disk_percent={disk.percent}"
    ]
    
    # Print check output in Nagios format
    # Format: STATUS - Message | metric1=value1 metric2=value2
    print("OK - System metrics collected | " + " ".join(metrics))

if __name__ == "__main__":
    get_system_metrics() 