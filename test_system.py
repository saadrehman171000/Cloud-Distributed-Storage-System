import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from scripts.node_monitor import NodeMonitor
from scripts.node_manager import NodeManager
from scripts.performance_monitor import PerformanceMonitor
from storage.raid_tester import RAIDTester
import os
from storage.raid_manager import RAIDManager
from PIL import Image
import numpy as np
from statistics import mean

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
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

def verify_raid_recovery(original_image, recovered_image):
    """Verify recovered image matches original"""
    orig = np.array(Image.open(original_image))
    recv = np.array(Image.open(recovered_image))
    
    # Compare shapes first
    if orig.shape != recv.shape:
        logger.error(f"Shape mismatch: original {orig.shape} vs recovered {recv.shape}")
        return 1.0  # Return max difference
    
    # Compare content (normalized difference)
    diff = np.abs(orig.astype(float) - recv.astype(float)).mean() / 255.0
    logger.debug(f"Normalized pixel difference: {diff}")
    return diff

def get_all_images():
    """Get all images from Imagedata folder"""
    images = []
    for root, _, files in os.walk("Imagedata"):
        for file in files:
            if file.endswith(('.jpg', '.jpeg')):  # Only process jpg files, skip masks for now
                images.append(os.path.join(root, file))
    return images

def process_single_image(raid_manager, image_path):
    """Process a single image with both RAID 5 and RAID 6"""
    results = {
        'path': image_path,
        'raid5_success': False,
        'raid6_success': False,
        'errors': [],
        'processing_time': None
    }
    
    try:
        # 1. Test RAID 5
        segments = raid_manager.segment_image(image_path)
        parity = raid_manager.calculate_parity_raid5(segments)
        
        # Simulate one segment loss
        available_segments = segments[:2]
        recovered = raid_manager.recover_raid5(available_segments, parity)
        
        # Save and verify
        recovered_path = os.path.join("test_results", f"raid5_{os.path.basename(image_path)}")
        recovered_full = raid_manager.reconstruct_image(recovered)
        raid_manager.save_image(recovered_full, recovered_path)
        
        # Verify recovery (allow up to 20% difference)
        diff = verify_raid_recovery(image_path, recovered_path)
        results['raid5_success'] = diff < 0.2
        
        # 2. Test RAID 6
        parities = raid_manager.calculate_parity_raid6(segments)
        available_segments = [segments[0]]
        recovered = raid_manager.recover_raid6(available_segments, parities)
        
        # Save and verify
        recovered_path = os.path.join("test_results", f"raid6_{os.path.basename(image_path)}")
        recovered_full = raid_manager.reconstruct_image(recovered)
        raid_manager.save_image(recovered_full, recovered_path)
        
        # Verify recovery (allow up to 30% difference for RAID 6)
        diff = verify_raid_recovery(image_path, recovered_path)
        results['raid6_success'] = diff < 0.3
        
        # Calculate processing time
        start_time = time.time()
        results['processing_time'] = time.time() - start_time
        
    except Exception as e:
        results['errors'].append(str(e))
        logger.error(f"Failed processing {image_path}: {e}")
    
    return results

def test_raid_functionality():
    # Initialize managers
    raid_manager = RAIDManager("./test_storage")
    node_manager = NodeManager()
    
    # Get all test images
    test_images = get_all_images()
    logger.info(f"Found {len(test_images)} images to test")
    
    # Process images in parallel
    results = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(process_single_image, raid_manager, img) for img in test_images]
        
        # Show progress bar
        with tqdm(total=len(test_images), desc="Processing images") as pbar:
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                pbar.update(1)
    
    # Print summary
    successful_raid5 = sum(1 for r in results if r['raid5_success'])
    successful_raid6 = sum(1 for r in results if r['raid6_success'])
    failed = sum(1 for r in results if r['errors'])
    
    logger.info(f"\nResults Summary:")
    logger.info(f"Total images processed: {len(test_images)}")
    logger.info(f"RAID 5 successful recoveries: {successful_raid5}")
    logger.info(f"RAID 6 successful recoveries: {successful_raid6}")
    logger.info(f"Failed processing: {failed}")
    
    # Test node failure
    logger.info("\nTesting node failure simulation...")
    node_manager.simulate_node_failure("worker-node-1")

    # Add performance metrics
    processing_times = []
    for result in results:
        if 'processing_time' in result:
            processing_times.append(result['processing_time'])
    
    if processing_times:
        avg_time = mean(processing_times)
        logger.info(f"Average processing time per image: {avg_time:.2f} seconds")
        logger.info(f"Processing speed: {1/avg_time:.2f} images/second")

if __name__ == "__main__":
    # Create directories
    os.makedirs("test_results", exist_ok=True)
    os.makedirs("test_storage", exist_ok=True)
    
    test_raid_functionality() 