# Cloud Distributed Storage System

This project implements a cloud storage and data recovery system utilizing Kubernetes, Docker, Sensu, Prometheus, and RAID configurations (RAID 5 & RAID 6). The goal is to provide a distributed, fault-tolerant, and scalable cloud storage solution with automated node failure recovery and monitoring capabilities.

## Features

- **Cloud Infrastructure**: Configured with Kubernetes to manage a distributed storage system with 6 nodes (1 master and 5 worker nodes)
- **Fault Tolerance**: Implemented RAID 5 and RAID 6 configurations to provide redundancy and recovery from node failures
- **Monitoring and Observability**: Integrated with **Sensu** for health monitoring and **Grafana** for visualizing system metrics (CPU, memory, disk usage, network traffic)
- **Automated Data Recovery**: Data recovery is triggered automatically in case of node failure using RAID's parity information
- **Real-Time Dashboards**: Prometheus is used for metrics collection, and Grafana displays system metrics in real-time

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/saadrehman171000/Cloud-Distributed-Storage-System.git
cd Cloud-Distributed-Storage-System
```

### 2. Kubernetes and Docker Setup

Create a Kubernetes namespace and set up the cluster:

```bash
# Create namespace
kubectl create namespace cloud-storage

# Apply deployments
kubectl apply -f kubernetes/cluster-deployment.yaml -n cloud-storage

# Verify setup
kubectl get pods -n cloud-storage
kubectl get deployments -n cloud-storage
```

### 3. Monitoring Setup

Set up Sensu monitoring and dashboards:

```bash
# Apply Sensu backend
kubectl apply -f sensu/sensu-backend.yaml -n cloud-storage

# Configure SSH access
kubectl apply -f kubernetes/ssh-config.yaml -n cloud-storage

# Deploy Uchiwa dashboard
kubectl apply -f sensu/uchiwa-dashboard.yaml -n cloud-storage

# Verify services
kubectl get services -n cloud-storage
```

### 4. RAID Configuration

The system uses RAID 5 and RAID 6 for fault tolerance and automatic data recovery.

#### Image Segmentation
To segment and store images across worker nodes:

```python
from storage.raid_manager import RAIDManager
raid = RAIDManager('storage_path')
raid.segment_image('test_image.jpg')
```

#### RAID Recovery Testing
Test the RAID recovery functionality:

```bash
python test_raid.py
```

## Monitoring and Metrics

### Grafana Dashboards
Monitor system metrics in real-time:
- Access dashboard: http://localhost:31000
- Metrics include: CPU Usage, Memory Usage, Disk Usage, Network Traffic

### Prometheus Metrics
View detailed system metrics and RAID recovery status:
- Access metrics: http://localhost:31001/graph

## Testing

### Node Failure Simulation
```bash
python test_system.py
```
This simulates worker node failure and triggers the recovery process.

### Performance Monitoring
Track system performance metrics at:
http://localhost:31000/d/performance/
- Processing speed
- Recovery time
- System load

## Contributing

We welcome contributions! Feel free to:
- Fork the repository
- Submit issues
- Create pull requests

## License

This project is licensed under the MIT License - see the LICENSE file for details.
