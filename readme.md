# Cloud Distributed Storage System

This project implements a cloud storage and data recovery system utilizing Kubernetes, Docker, Sensu, Prometheus, and RAID configurations (RAID 5 & RAID 6). The goal is to provide a distributed, fault-tolerant, and scalable cloud storage solution with automated node failure recovery and monitoring capabilities.

## Features

- **Cloud Infrastructure**: Configured with Kubernetes to manage a distributed storage system with 6 nodes (1 master and 5 worker nodes).
- **Fault Tolerance**: Implemented RAID 5 and RAID 6 configurations to provide redundancy and recovery from node failures.
- **Monitoring and Observability**: Integrated with **Sensu** for health monitoring and **Grafana** for visualizing system metrics (CPU, memory, disk usage, network traffic).
- **Automated Data Recovery**: Data recovery is triggered automatically in case of node failure using RAID’s parity information.
- **Real-Time Dashboards**: Prometheus is used for metrics collection, and Grafana displays system metrics in real-time.

## Setup Instructions

### 1. Clone the Repository

Clone the repository to your local machine:

```bash
git clone https://github.com/saadrehman171000/Cloud-Distributed-Storage-System.git
cd Cloud-Distributed-Storage-System

### 2. Kubernetes and Docker Setup
Follow the steps below to set up the Kubernetes cluster using Docker:

#### Create a Kubernetes Namespace:

```bash
kubectl create namespace cloud-storage


# Kubernetes and Docker Setup
# Follow the steps below to set up the Kubernetes cluster using Docker:

# Create a Kubernetes Namespace
kubectl create namespace cloud-storage

# Apply Kubernetes Deployments
kubectl apply -f kubernetes/cluster-deployment.yaml -n cloud-storage

# Verify the Deployments
kubectl get pods -n cloud-storage
kubectl get deployments -n cloud-storage

# Sensu Monitoring Setup
# Sensu is used to monitor the health of the nodes and the system’s status.

# Apply Sensu Backend
kubectl apply -f sensu/sensu-backend.yaml -n cloud-storage

# Apply SSH Configuration
# To enable secure remote access between nodes, apply the SSH configuration
kubectl apply -f kubernetes/ssh-config.yaml -n cloud-storage

# Apply Uchiwa Dashboard
# Set up the Uchiwa dashboard for real-time visualization of Sensu events
kubectl apply -f sensu/uchiwa-dashboard.yaml -n cloud-storage

# Verify All Services
# Check the status of the services to ensure that everything is running correctly
kubectl get services -n cloud-storage

# RAID Configuration
# The cloud storage system uses RAID 5 and RAID 6 to provide fault tolerance and automatic recovery of data in case of node failure.

# RAID Setup
# Segment Image Data
# Images are segmented into parts and stored across the worker nodes in a RAID array.
# The following code segments an image:

python -c "
from storage.raid_manager import RAIDManager
raid = RAIDManager('storage_path')
raid.segment_image('test_image.jpg')
"

# RAID Recovery
# The recovery process involves using the parity data from the remaining nodes to reconstruct data from a failed node.

# Run RAID Recovery Test
# To test the RAID recovery logic, use the following command
python test_raid.py

# Monitoring Dashboards
# 1. Grafana Dashboards
# Grafana is used to visualize real-time system metrics such as:
# CPU Usage, Memory Usage, Disk Usage, Network Traffic

# You can access the Grafana dashboard at http://localhost:31000 to monitor the system's performance.

# 2. Prometheus Metrics
# Prometheus collects metrics from all nodes and provides insights into the system's status and RAID recovery process.
# Access the Prometheus metrics at http://localhost:31001/graph.

# Testing
# 1. Node Failure Simulation
# To simulate node failure, run the following test:
python test_system.py

# This test will simulate the failure of a worker node and initiate the data recovery process.

# 2. Performance Metrics
# Monitor the performance metrics, including processing speed, recovery time, and system load, using the Grafana dashboard at http://localhost:31000/d/performance/.

# Contributing
# Feel free to fork this repository, submit issues, and create pull requests.
# Contributions are always welcome to improve the system.

# License
# This project is licensed under the MIT License - see the LICENSE file for details.
