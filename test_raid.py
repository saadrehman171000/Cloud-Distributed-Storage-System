from storage.raid_manager import RAIDManager
import os

def test_raid_5():
    raid_manager = RAIDManager(raid_level=5)
    
    # Test with an image from your dataset
    image_path = "Imagedata/test/sample_image.jpg"  # Update with actual path
    
    # Segment the image
    segments = raid_manager.segment_image(image_path)
    
    # Simulate node failure by removing one segment
    failed_segments = ['R1']
    
    # Reconstruct the image
    reconstructed = raid_manager.reconstruct_image(segments, failed_segments)
    
    # Save reconstructed image
    reconstructed.save('reconstructed_image.jpg')

if __name__ == "__main__":
    test_raid_5() 