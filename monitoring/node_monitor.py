import subprocess
import json
import time

class NodeMonitor:
    def __init__(self, nodes):
        self.nodes = nodes
        self.status = {}
        
    def check_node_health(self, node_ip):
        """Check if node is responsive"""
        try:
            result = subprocess.run(
                ['ping', '-c', '1', node_ip],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False
            
    def monitor_nodes(self):
        """Monitor all nodes and update status"""
        for node in self.nodes:
            is_healthy = self.check_node_health(node['ip'])
            self.status[node['name']] = {
                'healthy': is_healthy,
                'last_checked': time.time()
            }
            
        return self.status
        
    def notify_sensu(self, node_status):
        """Send node status to Sensu API"""
        # Implementation for sending data to Sensu API
        pass 