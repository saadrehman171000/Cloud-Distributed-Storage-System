import logging
import threading
import time
from scripts.node_monitor import NodeMonitor
from scripts.node_manager import NodeManager
from scripts.performance_monitor import PerformanceMonitor
from storage.raid_tester import RAIDTester
import os
from storage.raid_manager import RAIDManager
from PIL import Image
import numpy as np

def main():
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Initialize components
    node_monitor = NodeMonitor()
    node_manager = NodeManager()
    raid_tester = RAIDTester()
    perf_monitor = PerformanceMonitor()
    
    # Start monitoring threads
    threading.Thread(target=node_monitor.monitor_nodes, daemon=True).start()
    threading.Thread(target=perf_monitor.collect_metrics, daemon=True).start()
    
    # Run tests
    logger.info("Testing node failure and recovery...")
    node_manager.test_failure_recovery()
    
    logger.info("Testing RAID implementation...")
    raid_tester.test_all_images()
    
    # Keep main thread running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")

def test_raid_functionality():
    # Initialize managers
    raid_manager = RAIDManager("./test_storage")
    node_manager = NodeManager()
    
    # Test image segmentation and recovery
    test_image = "./test_images/sample.jpg"
    
    # 1. Test RAID 5
    print("Testing RAID 5...")
    segments = raid_manager.segment_image(test_image)
    parity = raid_manager.calculate_parity_raid5(segments)
    
    # Simulate one segment loss
    available_segments = segments[:2]  # Remove one segment
    recovered = raid_manager.recover_raid5(available_segments, parity)
    
    # 2. Test RAID 6
    print("Testing RAID 6...")
    parities = raid_manager.calculate_parity_raid6(segments)
    
    # Simulate two segment loss
    available_segments = [segments[0]]  # Keep only one segment
    recovered = raid_manager.recover_raid6(available_segments, parities)
    
    # 3. Test node failure and recovery
    print("Testing node failure simulation...")
    node_manager.simulate_node_failure("test-node-1")

if __name__ == "__main__":
    test_raid_functionality() 