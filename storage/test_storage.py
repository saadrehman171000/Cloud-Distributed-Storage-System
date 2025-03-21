from raid_manager import RAIDManager
import os

def test_storage_system():
    # Initialize RAID manager
    raid = RAIDManager(raid_level=5)
    
    # Test directory for sample images
    test_dir = "test_images"
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
        
    # Create a sample image for testing
    import numpy as np
    from PIL import Image
    
    # Create a test image (100x100 pixels)
    test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    test_img = Image.fromarray(test_image)
    test_img.save(f"{test_dir}/test.jpg")
    
    # Test RAID 5 storage
    segments = raid.segment_image(f"{test_dir}/test.jpg")
    print("Image segmented successfully")
    
    # Simulate node failure
    failed_segments = ['R1']
    reconstructed = raid.reconstruct_image(segments, failed_segments)
    reconstructed.save(f"{test_dir}/reconstructed.jpg")
    print("Image reconstructed successfully")

if __name__ == "__main__":
    test_storage_system() 