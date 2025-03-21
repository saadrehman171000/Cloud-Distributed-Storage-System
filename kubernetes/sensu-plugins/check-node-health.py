#!/usr/bin/env python3
import sys
from kubernetes import client, config

def check_node_health():
    try:
        config.load_incluster_config()
        v1 = client.CoreV1Api()
        nodes = v1.list_node()
        unhealthy = 0
        
        for node in nodes.items:
            for condition in node.status.conditions:
                if condition.type == "Ready" and condition.status != "True":
                    unhealthy += 1
                    print(f"Node {node.metadata.name} is not ready")
        
        if unhealthy > 0:
            print(f"WARNING: {unhealthy} nodes are unhealthy")
            sys.exit(1)
        print("OK: All nodes are healthy")
        sys.exit(0)
    except Exception as e:
        print(f"CRITICAL: {str(e)}")
        sys.exit(2)

if __name__ == "__main__":
    check_node_health() 