import kubernetes
from kubernetes import client, config
import time
import logging

class NodeManager:
    def __init__(self, namespace="cloud-storage"):
        # Load kubernetes configuration
        config.load_kube_config()
        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.namespace = namespace
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def get_worker_pods(self):
        """Get all worker pods"""
        return self.v1.list_namespaced_pod(
            namespace=self.namespace,
            label_selector="role=worker"
        ).items
    
    def shutdown_node(self, pod_name, sleep_time=30):
        """Simulate node failure by deleting the pod"""
        try:
            self.logger.info(f"Shutting down node: {pod_name}")
            self.v1.delete_namespaced_pod(
                name=pod_name,
                namespace=self.namespace
            )
            time.sleep(sleep_time)  # Wait for specified time
            return True
        except Exception as e:
            self.logger.error(f"Error shutting down node {pod_name}: {str(e)}")
            return False
    
    def restart_node(self, pod_name):
        """Restart a node by recreating the pod"""
        try:
            self.logger.info(f"Restarting node: {pod_name}")
            # Pod will be automatically recreated by the deployment controller
            return True
        except Exception as e:
            self.logger.error(f"Error restarting node {pod_name}: {str(e)}")
            return False

    def test_node_failure_recovery(self):
        """Test node failure and recovery scenario"""
        # Get worker pods
        workers = self.get_worker_pods()
        if not workers:
            self.logger.error("No worker pods found")
            return False
        
        # Select first worker for test
        test_pod = workers[0]
        pod_name = test_pod.metadata.name
        
        # Shutdown node
        self.logger.info(f"Testing failure recovery for node: {pod_name}")
        if self.shutdown_node(pod_name):
            time.sleep(5)  # Wait for shutdown
            
            # Check if pod is recreated
            new_pods = self.get_worker_pods()
            if len(new_pods) == len(workers):
                self.logger.info("Node recovery successful")
                return True
            else:
                self.logger.error("Node recovery failed")
                return False 