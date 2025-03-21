#!/usr/bin/env python3
import os
import sys
from kubernetes import client, config

def check_node_health():
    config.load_kube_config()
    v1 = client.CoreV1Api()
    
    try:
        nodes = v1.list_node()
        ready_nodes = 0
        total_nodes = len(nodes.items)
        
        for node in nodes.items:
            for condition in node.status.conditions:
                if condition.type == "Ready" and condition.status == "True":
                    ready_nodes += 1
                    break
        
        if ready_nodes == total_nodes:
            print(f"OK: All {total_nodes} nodes are healthy")
            sys.exit(0)
        else:
            print(f"WARNING: {ready_nodes}/{total_nodes} nodes are healthy")
            sys.exit(1)
    except Exception as e:
        print(f"CRITICAL: Failed to check node health - {str(e)}")
        sys.exit(2)

if __name__ == "__main__":
    check_node_health() 