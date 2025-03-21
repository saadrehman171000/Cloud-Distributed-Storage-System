#!/usr/bin/env python3
import logging
import time
import sys
import os
import threading

# Add scripts directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.node_manager import NodeManager
from scripts.node_monitor import NodeMonitor
from scripts.performance_monitor import PerformanceMonitor

def simulate_node_failure(node_name):
    """Simulate a node failure by cordoning and draining"""
    try:
        from kubernetes import client, config
        v1 = client.CoreV1Api()
        
        # Cordon the node (mark as unschedulable)
        body = {
            "spec": {
                "unschedulable": True
            }
        }
        v1.patch_node(node_name, body)
        
        # Drain the node (evict all pods)
        pods = v1.list_pod_for_all_namespaces(field_selector=f'spec.nodeName={node_name}').items
        for pod in pods:
            if pod.metadata.namespace != 'kube-system':  # Don't evict system pods
                v1.delete_namespaced_pod(
                    pod.metadata.name,
                    pod.metadata.namespace
                )
        
        return True
    except Exception as e:
        logging.error(f"Error simulating node failure: {e}")
        return False

def test_monitoring():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Initialize components
    node_manager = NodeManager()
    node_monitor = NodeMonitor()
    perf_monitor = PerformanceMonitor()
    
    # Start monitoring threads
    monitor_thread = threading.Thread(target=node_monitor.monitor_system, daemon=True)
    perf_thread = threading.Thread(target=perf_monitor.collect_metrics, daemon=True)
    
    monitor_thread.start()
    perf_thread.start()
    
    # Test pod failure
    logger.info("\nTesting pod failure detection...")
    workers = node_manager.get_worker_pods()
    if workers:
        test_pod = workers[0]
        pod_name = test_pod.metadata.name
        
        # Force pod failure
        node_manager.shutdown_node(pod_name)
        logger.info(f"Forced failure of pod: {pod_name}")
        
        # Wait for monitoring to detect failure
        time.sleep(35)
        
        # Check if pod was detected as unhealthy
        unhealthy = node_monitor.check_pod_health()
        if pod_name in unhealthy:
            logger.info("✅ Pod failure detection working")
        else:
            logger.error("❌ Pod failure detection failed")

    # Test node failure with proper simulation
    logger.info("\nTesting node failure detection...")
    nodes = node_manager.v1.list_node(label_selector='role=worker').items
    if nodes:
        test_node = nodes[0]
        node_name = test_node.metadata.name
        
        # Simulate node failure
        logger.info(f"Simulating failure for node: {node_name}")
        if simulate_node_failure(node_name):
            logger.info("Node failure simulation successful")
        else:
            logger.error("Node failure simulation failed")
        
        time.sleep(35)
        unhealthy = node_monitor.check_node_health()
        if node_name in unhealthy:
            logger.info("✅ Node failure detection working")
        else:
            logger.error("❌ Node failure detection failed")

    # Test metrics collection
    logger.info("\nMetrics Summary:")
    logger.info("----------------")
    pods = node_manager.get_worker_pods()
    for pod in pods:
        name = pod.metadata.name
        status = pod.status.phase
        restarts = pod.status.container_statuses[0].restart_count if pod.status.container_statuses else 0
        logger.info(f"Pod: {name}, Status: {status}, Restarts: {restarts}")
    
    logger.info("\nAccess monitoring dashboards at:")
    logger.info("- Grafana: http://localhost:30002")
    logger.info("- Prometheus: http://localhost:30003")
    logger.info("- Uchiwa: http://localhost:30001")

if __name__ == "__main__":
    test_monitoring() 