from scripts.node_manager import NodeManager
from storage.raid_tester import RAIDTester
import time
import logging

def main():
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Initialize components
    node_manager = NodeManager()
    raid_tester = RAIDTester()
    
    # Test node failure and recovery
    logger.info("Testing node failure and recovery...")
    node_manager.test_node_failure_recovery()
    
    # Test RAID implementation
    logger.info("Testing RAID implementation...")
    results = raid_tester.run_tests()
    
    # Print results
    logger.info("Test Results:")
    logger.info(f"RAID 5 - Success: {results['raid5']['success']}, Failed: {results['raid5']['failed']}")
    logger.info(f"RAID 6 - Success: {results['raid6']['success']}, Failed: {results['raid6']['failed']}")

if __name__ == "__main__":
    main() 