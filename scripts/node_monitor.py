#!/usr/bin/env python3
import logging
import time
from kubernetes import client, config
from prometheus_client import start_http_server, Gauge

class NodeMonitor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        config.load_kube_config()
        self.v1 = client.CoreV1Api()
        self.custom = client.CustomObjectsApi()
        
        # Prometheus metrics
        self.node_cpu_usage = Gauge('node_cpu_usage', 'CPU usage by node', ['node'])
        self.node_memory_usage = Gauge('node_memory_usage', 'Memory usage by node', ['node'])
        self.node_status = Gauge('node_status', 'Node status (1=healthy, 0=unhealthy)', ['node'])
        self.pod_status = Gauge('pod_status', 'Pod status (1=running, 0=failed)', ['pod'])
        self.pod_restarts = Gauge('pod_restarts', 'Pod restart count', ['pod'])
        
        # Start Prometheus metrics server
        start_http_server(8000)
        
    def get_node_metrics(self, node_name):
        try:
            # Get node metrics using metrics API
            metrics = self.v1.list_node().items
            for node in metrics:
                if node.metadata.name == node_name:
                    cpu_percent = self._get_cpu_percent(node)
                    memory_percent = self._get_memory_percent(node)
                    
                    # Update Prometheus metrics
                    self.node_cpu_usage.labels(node=node_name).set(cpu_percent)
                    self.node_memory_usage.labels(node=node_name).set(memory_percent)
                    
                    return cpu_percent, memory_percent
            return None, None
        except Exception as e:
            self.logger.error(f"Failed to get metrics for node {node_name}: {e}")
            return None, None
            
    def _get_cpu_percent(self, node):
        try:
            allocatable = node.status.allocatable.get('cpu', '0')
            capacity = node.status.capacity.get('cpu', '0')
            if allocatable and capacity:
                return (float(capacity) - float(allocatable)) / float(capacity) * 100
            return 0
        except:
            return 0
            
    def _get_memory_percent(self, node):
        try:
            allocatable = self._convert_to_bytes(node.status.allocatable.get('memory', '0Ki'))
            capacity = self._convert_to_bytes(node.status.capacity.get('memory', '0Ki'))
            if allocatable and capacity:
                return (capacity - allocatable) / capacity * 100
            return 0
        except:
            return 0
            
    def _convert_to_bytes(self, memory_str):
        units = {'Ki': 1024, 'Mi': 1024**2, 'Gi': 1024**3, 'Ti': 1024**4}
        number = float(''.join([c for c in memory_str if c.isdigit() or c == '.']))
        unit = ''.join([c for c in memory_str if c.isalpha()])
        return number * units.get(unit, 1)
            
    def check_node_health(self):
        try:
            nodes = self.v1.list_node(label_selector='role=worker')
            unhealthy_nodes = []
            
            for node in nodes.items:
                node_name = node.metadata.name
                node_status = "Ready"
                cpu_usage, memory_usage = self.get_node_metrics(node_name)
                
                for condition in node.status.conditions:
                    if condition.type == "Ready":
                        if condition.status != "True":
                            node_status = "NotReady"
                            unhealthy_nodes.append(node_name)
                            self.node_status.labels(node=node_name).set(0)
                        else:
                            self.node_status.labels(node=node_name).set(1)
                            
                self.logger.info(f"Node {node_name} status: {node_status}, CPU: {cpu_usage}%, Memory: {memory_usage}%")
                
            return unhealthy_nodes
        except Exception as e:
            self.logger.error(f"Error checking node health: {e}")
            return []
            
    def check_pod_health(self):
        try:
            pods = self.v1.list_namespaced_pod(namespace='cloud-storage')
            unhealthy_pods = []
            
            for pod in pods.items:
                pod_name = pod.metadata.name
                pod_status = pod.status.phase
                restart_count = pod.status.container_statuses[0].restart_count if pod.status.container_statuses else 0
                
                # Update metrics
                self.pod_status.labels(pod=pod_name).set(1 if pod_status == 'Running' else 0)
                self.pod_restarts.labels(pod=pod_name).set(restart_count)
                
                if pod_status != 'Running':
                    unhealthy_pods.append(pod_name)
                    self.logger.warning(f"Pod {pod_name} is {pod_status}")
                
            return unhealthy_pods
        except Exception as e:
            self.logger.error(f"Error checking pod health: {e}")
            return []
            
    def monitor_system(self, interval=30):
        while True:
            try:
                # Check both nodes and pods
                unhealthy_nodes = self.check_node_health()
                unhealthy_pods = self.check_pod_health()
                
                if unhealthy_nodes:
                    self.logger.warning(f"Unhealthy nodes detected: {unhealthy_nodes}")
                    self.trigger_recovery(unhealthy_nodes)
                    
                if unhealthy_pods:
                    self.logger.warning(f"Unhealthy pods detected: {unhealthy_pods}")
                    self.trigger_pod_recovery(unhealthy_pods)
                    
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
            time.sleep(interval)
            
    def trigger_recovery(self, unhealthy_nodes):
        """Trigger automated recovery for unhealthy nodes"""
        try:
            from scripts.node_manager import NodeManager
            manager = NodeManager()
            
            for node in unhealthy_nodes:
                self.logger.info(f"Initiating recovery for node: {node}")
                manager.recover_node(node)
        except Exception as e:
            self.logger.error(f"Error triggering recovery: {e}")
            
    def trigger_pod_recovery(self, unhealthy_pods):
        try:
            from scripts.node_manager import NodeManager
            manager = NodeManager()
            
            for pod in unhealthy_pods:
                if 'worker-deployment' in pod:
                    self.logger.info(f"Initiating recovery for pod: {pod}")
                    manager.restart_node(pod)
        except Exception as e:
            self.logger.error(f"Error triggering pod recovery: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    monitor = NodeMonitor()
    monitor.monitor_system() 