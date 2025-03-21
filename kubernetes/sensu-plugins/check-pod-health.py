#!/usr/bin/env python3
import sys
from kubernetes import client, config

def check_pod_health():
    try:
        config.load_incluster_config()
        v1 = client.CoreV1Api()
        pods = v1.list_namespaced_pod('cloud-storage')
        unhealthy = 0
        
        for pod in pods.items:
            if pod.status.phase != 'Running':
                unhealthy += 1
                print(f"Pod {pod.metadata.name} is in {pod.status.phase} state")
        
        if unhealthy > 0:
            print(f"WARNING: {unhealthy} pods are not running")
            sys.exit(1)
        print("OK: All pods are running")
        sys.exit(0)
    except Exception as e:
        print(f"CRITICAL: {str(e)}")
        sys.exit(2)

if __name__ == "__main__":
    check_pod_health() 