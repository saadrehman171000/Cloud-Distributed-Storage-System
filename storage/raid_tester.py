from .raid_manager import RAIDManager
import os
import logging
from PIL import Image
import numpy as np
from datetime import datetime

class RAIDTester:
    def __init__(self, image_dir="Imagedata/test", output_dir="test_results"):
        self.image_dir = image_dir
        self.output_dir = output_dir
        self.raid5 = RAIDManager(raid_level=5)
        self.raid6 = RAIDManager(raid_level=6)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Create output directory
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def test_raid5_recovery(self, image_path):
        """Test RAID 5 recovery with single node failure"""
        try:
            # Segment image
            segments = self.raid5.segment_image(image_path)
            
            # Simulate node failure (R1 segment)
            failed_segments = ['R1']
            
            # Reconstruct image
            reconstructed = self.raid5.reconstruct_image(segments, failed_segments)
            
            # Save reconstructed image
            filename = os.path.basename(image_path)
            output_path = os.path.join(self.output_dir, f"raid5_recovered_{filename}")
            reconstructed.save(output_path)
            
            return True, output_path
        except Exception as e:
            self.logger.error(f"RAID 5 recovery failed: {str(e)}")
            return False, None
    
    def test_raid6_recovery(self, image_path):
        """Test RAID 6 recovery with two node failures"""
        try:
            # Segment image
            segments = self.raid6.segment_image(image_path)
            
            # Simulate two node failures
            failed_segments = ['R1', 'R2']
            
            # Reconstruct image
            reconstructed = self.raid6.reconstruct_image(segments, failed_segments)
            
            # Save reconstructed image
            filename = os.path.basename(image_path)
            output_path = os.path.join(self.output_dir, f"raid6_recovered_{filename}")
            reconstructed.save(output_path)
            
            return True, output_path
        except Exception as e:
            self.logger.error(f"RAID 6 recovery failed: {str(e)}")
            return False, None

    def run_tests(self):
        """Run tests on all images in the test directory"""
        results = {
            'raid5': {'success': 0, 'failed': 0},
            'raid6': {'success': 0, 'failed': 0}
        }
        
        for image_file in os.listdir(self.image_dir):
            if image_file.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_path = os.path.join(self.image_dir, image_file)
                self.logger.info(f"Testing with image: {image_file}")
                
                # Test RAID 5
                raid5_success, _ = self.test_raid5_recovery(image_path)
                if raid5_success:
                    results['raid5']['success'] += 1
                else:
                    results['raid5']['failed'] += 1
                
                # Test RAID 6
                raid6_success, _ = self.test_raid6_recovery(image_path)
                if raid6_success:
                    results['raid6']['success'] += 1
                else:
                    results['raid6']['failed'] += 1
        
        return results 