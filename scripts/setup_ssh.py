import subprocess
import os

def setup_ssh_access():
    """Setup SSH access across all nodes"""
    
    # Generate SSH key pair if not exists
    if not os.path.exists(os.path.expanduser('~/.ssh/id_rsa')):
        subprocess.run(['ssh-keygen', '-t', 'rsa', '-b', '4096', '-f', 
                       os.path.expanduser('~/.ssh/id_rsa'), '-N', ''])
    
    # Get list of nodes
    nodes = subprocess.run(['kubectl', 'get', 'nodes', '-o', 'wide', '--no-headers'],
                         capture_output=True, text=True).stdout.split('\n')
    
    # Copy SSH key to each node
    for node in nodes:
        if node.strip():
            node_name = node.split()[0]
            node_ip = node.split()[5]  # Internal IP
            print(f"Setting up SSH access for node: {node_name} ({node_ip})")
            
            # Copy SSH key
            subprocess.run(['kubectl', 'cp', 
                          os.path.expanduser('~/.ssh/id_rsa.pub'),
                          f'{node_name}:/root/.ssh/authorized_keys'])

if __name__ == "__main__":
    setup_ssh_access() 