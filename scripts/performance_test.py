#!/usr/bin/env python3
import time
import logging
import threading
import sys
import os

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Update imports to use correct paths
from scripts.node_manager import NodeManager
from scripts.node_monitor import NodeMonitor
from storage.raid_tester import RAIDTester

def test_recovery_performance():
    logger = logging.getLogger(__name__)
    node_manager = NodeManager()
    
    # Test recovery time
    start_time = time.time()
    success = node_manager.test_node_failure_recovery()
    recovery_time = time.time() - start_time
    
    if success:
        logger.info(f"✅ Recovery Time: {recovery_time:.2f} seconds")
    else:
        logger.error("❌ Recovery failed")
    return recovery_time if success else None

def test_concurrent_failures():
    logger = logging.getLogger(__name__)
    node_manager = NodeManager()
    
    # Get worker pods
    workers = node_manager.get_worker_pods()
    if len(workers) < 2:
        logger.error("Not enough workers for concurrent failure test")
        return False
        
    # Test two simultaneous failures
    test_pods = workers[:2]
    threads = []
    
    start_time = time.time()
    
    for pod in test_pods:
        thread = threading.Thread(
            target=node_manager.shutdown_node,
            args=(pod.metadata.name,)
        )
        threads.append(thread)
        thread.start()
    
    # Wait for all recoveries
    for thread in threads:
        thread.join()
        
    recovery_time = time.time() - start_time
    logger.info(f"Concurrent Recovery Time: {recovery_time:.2f} seconds")
    return recovery_time

def test_raid_performance():
    logger = logging.getLogger(__name__)
    raid_tester = RAIDTester()
    
    try:
        # Test RAID recovery speed
        start_time = time.time()
        
        # Run RAID tests (using the correct method name)
        results = raid_tester.run_tests()  # Changed from test_all_images() to run_tests()
        
        recovery_time = time.time() - start_time
        
        # Log results
        logger.info("RAID Test Results:")
        logger.info(f"RAID 5 - Success: {results['raid5']['success']}, Failed: {results['raid5']['failed']}")
        logger.info(f"RAID 6 - Success: {results['raid6']['success']}, Failed: {results['raid6']['failed']}")
        logger.info(f"✅ RAID Recovery Time: {recovery_time:.2f} seconds")
        
        return recovery_time
    except Exception as e:
        logger.error(f"❌ RAID test failed: {str(e)}")
        return None

def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Performance Tests")
    logger.info("==========================")
    
    results = {}
    
    # Single node recovery
    logger.info("\n1. Testing Single Node Recovery")
    results['single'] = test_recovery_performance()
    
    # Concurrent failures
    logger.info("\n2. Testing Concurrent Failures")
    results['concurrent'] = test_concurrent_failures()
    
    # RAID recovery
    logger.info("\n3. Testing RAID Recovery")
    results['raid'] = test_raid_performance()
    
    # Summary
    logger.info("\nPerformance Summary")
    logger.info("==================")
    for test, time in results.items():
        if time is not None:
            logger.info(f"{test.title()} Recovery: {time:.2f}s")
        else:
            logger.error(f"{test.title()} Recovery: Failed")

if __name__ == "__main__":
    main() 