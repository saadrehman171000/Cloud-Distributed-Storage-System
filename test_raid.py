import unittest
from storage.raid_manager import RAIDManager
from scripts.node_manager import NodeManager
import numpy as np
from PIL import Image
import os
import shutil

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

    def setUp(self):
        """Setup before each test"""
        # Clean directories
        shutil.rmtree(self.test_dir)
        shutil.rmtree(self.result_dir)
        os.makedirs(self.test_dir)
        os.makedirs(self.result_dir)

    def test_raid5_recovery(self):
        """Test RAID 5 recovery"""
        # Get test image
        test_image = "Imagedata/test/sample1.jpg"
        segments = self.raid_manager.segment_image(test_image)
        parity = self.raid_manager.calculate_parity_raid5(segments)
        
        # Test recovery
        available_segments = segments[:2]
        recovered = self.raid_manager.recover_raid5(available_segments, parity)
        self.assertEqual(len(recovered), 3)

    def test_raid6_recovery(self):
        """Test RAID 6 recovery"""
        test_image = "Imagedata/test/sample1.jpg"
        segments = self.raid_manager.segment_image(test_image)
        parities = self.raid_manager.calculate_parity_raid6(segments)
        
        # Test recovery
        available_segments = [segments[0]]
        recovered = self.raid_manager.recover_raid6(available_segments, parities)
        self.assertEqual(len(recovered), 3)

    def test_node_failure(self):
        """Test node failure and recovery"""
        result = self.node_manager.simulate_node_failure("worker-node-1")
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main() 