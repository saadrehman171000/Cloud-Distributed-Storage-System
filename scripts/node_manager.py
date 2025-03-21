import kubernetes
from kubernetes import client, config
import time
import logging
import threading
import queue

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
        
        self.recovery_queue = queue.Queue()
        self.recovery_lock = threading.Lock()
        self.max_concurrent_recoveries = 1
        self.recovering_nodes = set()
    
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

    def _perform_recovery(self, node_name):
        """Internal method to perform node recovery"""
        try:
            self.logger.info(f"Performing recovery for node: {node_name}")
            
            # Get pods on the node
            pods = self.v1.list_namespaced_pod(
                namespace=self.namespace,
                field_selector=f'spec.nodeName={node_name}'
            ).items
            
            # Evacuate pods from the node
            for pod in pods:
                if pod.metadata.name:
                    self.logger.info(f"Evacuating pod {pod.metadata.name} from node {node_name}")
                    self.v1.delete_namespaced_pod(
                        name=pod.metadata.name,
                        namespace=self.namespace
                    )
            
            # Wait for pods to be rescheduled
            time.sleep(30)
            
            return True
        except Exception as e:
            self.logger.error(f"Error in node recovery: {e}")
            return False

    def recover_node(self, node_name):
        """Public method to recover a node"""
        with self.recovery_lock:
            if len(self.recovering_nodes) >= self.max_concurrent_recoveries:
                self.logger.warning(f"Max concurrent recoveries reached. Queueing {node_name}")
                self.recovery_queue.put(node_name)
                return False
                
            self.recovering_nodes.add(node_name)
            
        try:
            success = self._perform_recovery(node_name)
            return success
        finally:
            with self.recovery_lock:
                self.recovering_nodes.remove(node_name)
                if not self.recovery_queue.empty():
                    next_node = self.recovery_queue.get()
                    threading.Thread(target=self.recover_node, args=(next_node,)).start() 