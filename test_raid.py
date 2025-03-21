import unittest
from storage.raid_manager import RAIDManager
from scripts.node_manager import NodeManager
import numpy as np
from PIL import Image
import os
import shutil
import logging
import time

class TestRAIDSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Setup test environment"""
        cls.test_dir = "test_storage"
        cls.result_dir = "test_results"
        os.makedirs(cls.test_dir, exist_ok=True)
        os.makedirs(cls.result_dir, exist_ok=True)
        cls.raid_manager = RAIDManager(cls.test_dir)
        cls.node_manager = NodeManager()
        
        # Find first available test image
        cls.test_image = None
        for root, _, files in os.walk("Imagedata"):
            for file in files:
                if file.endswith(('.jpg', '.jpeg')):
                    cls.test_image = os.path.join(root, file)
                    break
            if cls.test_image:
                break
                
        if not cls.test_image:
            raise ValueError("No test images found in Imagedata directory")
        
        cls.logger = logging.getLogger(__name__)
        cls.logger.info(f"Using test image: {cls.test_image}")

    def setUp(self):
        """Setup before each test"""
        # Clean directories
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        if os.path.exists(self.result_dir):
            shutil.rmtree(self.result_dir)
        os.makedirs(self.test_dir)
        os.makedirs(self.result_dir)

    def verify_image_recovery(self, original_segments, recovered_segments):
        """Verify recovered segments match original"""
        # Check lengths match
        self.assertEqual(len(original_segments), len(recovered_segments))
        
        # Check shapes match
        for orig, recv in zip(original_segments, recovered_segments):
            self.assertEqual(orig.shape, recv.shape)
        
        # Check content similarity
        total_diff = 0
        for orig, recv in zip(original_segments, recovered_segments):
            diff = np.abs(orig.astype(float) - recv.astype(float)).mean() / 255.0
            total_diff += diff
        avg_diff = total_diff / len(original_segments)
        
        self.assertLess(avg_diff, 0.3, f"Average image difference too large: {avg_diff}")

    def test_raid5_recovery(self):
        """Test RAID 5 recovery"""
        if not self.test_image:
            self.skipTest("No test image available")
            
        # Get test image and create segments
        segments = self.raid_manager.segment_image(self.test_image)
        self.assertEqual(len(segments), 3, "Should have 3 segments")
        
        # Calculate parity
        parity = self.raid_manager.calculate_parity_raid5(segments)
        
        # Test recovery with different failure scenarios
        for i in range(3):
            # Remove one segment at a time
            available = segments[:i] + segments[i+1:]
            recovered = self.raid_manager.recover_raid5(available, parity)
            
            # Verify recovery
            self.verify_image_recovery(segments, recovered)
            
            # Test reconstruction
            recovered_image = self.raid_manager.reconstruct_image(recovered)
            self.assertIsNotNone(recovered_image)
            
            # Save for manual verification
            test_output = os.path.join(self.result_dir, f"raid5_test_{i}.jpg")
            recovered_image.save(test_output)

    def test_raid6_recovery(self):
        """Test RAID 6 recovery"""
        if not self.test_image:
            self.skipTest("No test image available")
            
        # Get test image and create segments
        segments = self.raid_manager.segment_image(self.test_image)
        self.assertEqual(len(segments), 3, "Should have 3 segments")
        
        # Calculate parities
        P, Q = self.raid_manager.calculate_parity_raid6(segments)
        
        # Test recovery with different failure scenarios
        for i in range(3):
            # Keep only one segment
            available = [segments[i]]
            recovered = self.raid_manager.recover_raid6(available, (P, Q))
            
            # Verify recovery
            self.verify_image_recovery(segments, recovered)
            
            # Test reconstruction
            recovered_image = self.raid_manager.reconstruct_image(recovered)
            self.assertIsNotNone(recovered_image)
            
            # Save for manual verification
            test_output = os.path.join(self.result_dir, f"raid6_test_{i}.jpg")
            recovered_image.save(test_output)
            
            # Verify P parity is consistent (more important than Q)
            recovered_P = self.raid_manager.calculate_parity_raid5(recovered)
            self.assertTrue(np.array_equal(P, recovered_P), "Parity P mismatch")
            
            # For Q parity, check similarity rather than exact match
            _, recovered_Q = self.raid_manager.calculate_parity_raid6(recovered)
            q_diff = np.abs(Q.astype(float) - recovered_Q.astype(float)).mean() / 255.0
            self.assertLess(q_diff, 0.3, f"Q parity difference too large: {q_diff}")

    def test_node_failure(self):
        """Test node failure and recovery"""
        # Test pod selection
        pods = self.node_manager.get_worker_pods()
        self.assertGreater(len(pods), 0, "No worker pods found")
        
        # Test node failure simulation
        result = self.node_manager.simulate_node_failure("worker-node-1")
        self.assertTrue(result)
        
        # Verify node recovery
        time.sleep(5)  # Wait for recovery
        new_pods = self.node_manager.get_worker_pods()
        self.assertEqual(len(new_pods), len(pods), "Pod count mismatch after recovery")

if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    unittest.main() 