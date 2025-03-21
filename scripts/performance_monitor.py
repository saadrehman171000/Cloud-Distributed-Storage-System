#!/usr/bin/env python3
import psutil
import time
from prometheus_client import Gauge, start_http_server

class PerformanceMonitor:
    def __init__(self):
        self.raid_recovery_time = Gauge('raid_recovery_time', 'Time taken for RAID recovery')
        self.node_recovery_time = Gauge('node_recovery_time', 'Time taken for node recovery')
        self.system_cpu_usage = Gauge('system_cpu_usage', 'System CPU usage')
        self.system_memory_usage = Gauge('system_memory_usage', 'System memory usage')
        
        start_http_server(8001)
        
    def collect_metrics(self):
        while True:
            self.system_cpu_usage.set(psutil.cpu_percent())
            self.system_memory_usage.set(psutil.virtual_memory().percent)
            time.sleep(5) 