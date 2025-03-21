import logging
import threading
import time
from scripts.node_monitor import NodeMonitor
from scripts.node_manager import NodeManager
from scripts.performance_monitor import PerformanceMonitor
from storage.raid_tester import RAIDTester

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

if __name__ == "__main__":
    main() 