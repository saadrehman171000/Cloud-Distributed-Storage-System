import kubernetes
from kubernetes import client, config
import time
import logging
import threading
import queue
from storage.raid_manager import RAIDManager
import os
import numpy as np

class NodeManager:
    def __init__(self, namespace="cloud-storage"):
        # Load kubernetes configuration
        config.load_kube_config()
        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.namespace = namespace
        
        # Add storage path
        self.storage_path = "/storage"
        os.makedirs(self.storage_path, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.recovery_queue = queue.Queue()
        self.recovery_lock = threading.Lock()
        self.max_concurrent_recoveries = 1
        self.recovering_nodes = set()
        
        self.raid_manager = RAIDManager(self.storage_path)
    
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

    def simulate_node_failure(self, node_name):
        """Simulate a node failure and trigger recovery"""
        try:
            # Get pod name from node
            pods = self.v1.list_namespaced_pod(
                namespace=self.namespace,
                label_selector=f"role=worker"
            ).items
            
            if not pods:
                raise ValueError("No worker pods found")
            
            pod_name = pods[0].metadata.name
            self.logger.info(f"Selected pod {pod_name} for failure simulation")
            
            # Restrict access to the node
            self.restrict_node_access(node_name)
            
            # Shutdown the pod
            self.shutdown_node(pod_name)
            
            # Start recovery process
            self.recover_node_data(node_name)
            
            self.logger.info(f"Node failure simulation completed for {node_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to simulate node failure: {e}")
            return False

    def restrict_node_access(self, node_name):
        """Restrict access during recovery"""
        try:
            # Add node to recovering set
            with self.recovery_lock:
                self.recovering_nodes.add(node_name)
                
            # Cordon the node in Kubernetes
            self.v1.patch_node(node_name, {
                "spec": {
                    "unschedulable": True
                }
            })
            
            self.logger.info(f"Access restricted for node {node_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to restrict node access: {e}")
            return False

    def recover_node_data(self, node_name):
        """Recover data using appropriate RAID level"""
        try:
            # Get node storage info
            node_storage = self.get_node_storage(node_name)
            
            for image_path in node_storage.get('images', []):
                # Get available segments from other nodes
                available_segments = self.get_available_segments(image_path)
                
                if len(available_segments) >= 2:  # RAID 5 recovery
                    parity = self.get_parity(image_path)
                    recovered = self.raid_manager.recover_raid5(available_segments, parity)
                else:  # RAID 6 recovery
                    parities = self.get_parities(image_path)
                    recovered = self.raid_manager.recover_raid6(available_segments, parities)
                    
                # Save recovered data
                self.save_recovered_data(node_name, image_path, recovered)
                
            self.logger.info(f"Data recovery completed for node {node_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to recover node data: {e}")
            return False 

    def get_node_storage(self, node_name):
        """Get storage information for a node"""
        try:
            # Get node's storage path
            storage_path = os.path.join(self.storage_path, node_name)
            
            # Get list of images stored on the node
            images = []
            if os.path.exists(storage_path):
                for root, _, files in os.walk(storage_path):
                    images.extend([os.path.join(root, f) for f in files if f.endswith(('.jpg', '.png'))])
            
            return {
                'path': storage_path,
                'images': images
            }
        except Exception as e:
            self.logger.error(f"Failed to get node storage info: {e}")
            return None

    def get_available_segments(self, image_path):
        """Get available image segments from other nodes"""
        try:
            segments = []
            image_name = os.path.basename(image_path)
            
            # Check each node for segments
            for node in self.get_worker_pods():
                node_storage = self.get_node_storage(node.metadata.name)
                if node_storage:
                    segment_path = os.path.join(node_storage['path'], f"segment_{image_name}")
                    if os.path.exists(segment_path):
                        segments.append(np.load(segment_path))
            
            return segments
        except Exception as e:
            self.logger.error(f"Failed to get available segments: {e}")
            return []

    def get_parity(self, image_path):
        """Get RAID 5 parity for an image"""
        try:
            image_name = os.path.basename(image_path)
            parity_path = os.path.join(self.storage_path, 'parity', f"parity5_{image_name}.npy")
            if os.path.exists(parity_path):
                return np.load(parity_path)
            return None
        except Exception as e:
            self.logger.error(f"Failed to get parity: {e}")
            return None

    def get_parities(self, image_path):
        """Get RAID 6 parities for an image"""
        try:
            image_name = os.path.basename(image_path)
            parity_path = os.path.join(self.storage_path, 'parity')
            p1_path = os.path.join(parity_path, f"parity6_p_{image_name}.npy")
            p2_path = os.path.join(parity_path, f"parity6_q_{image_name}.npy")
            
            if os.path.exists(p1_path) and os.path.exists(p2_path):
                return np.load(p1_path), np.load(p2_path)
            return None, None
        except Exception as e:
            self.logger.error(f"Failed to get parities: {e}")
            return None, None

    def save_recovered_data(self, node_name, image_path, recovered_data):
        """Save recovered data back to node"""
        try:
            # Create node storage directory
            node_path = os.path.join(self.storage_path, node_name)
            os.makedirs(node_path, exist_ok=True)
            
            # Save recovered data
            output_path = os.path.join(node_path, os.path.basename(image_path))
            np.save(output_path, recovered_data)
            
            self.logger.info(f"Saved recovered data to {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save recovered data: {e}")
            return False 