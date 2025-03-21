#!/usr/bin/env python3
import psutil
import sys

def collect_metrics():
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        print(f"system.cpu.usage {cpu_percent}")
        print(f"system.memory.used_percent {memory.percent}")
        print(f"system.disk.used_percent {disk.percent}")
        sys.exit(0)
    except Exception as e:
        print(f"CRITICAL: {str(e)}")
        sys.exit(2)

if __name__ == "__main__":
    collect_metrics() 