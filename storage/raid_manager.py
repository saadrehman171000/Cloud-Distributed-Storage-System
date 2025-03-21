import numpy as np
from PIL import Image
import os

class RAIDManager:
    def __init__(self, raid_level=5):
        self.raid_level = raid_level
        self.segment_size = 1024 * 1024  # 1MB segments
        
    def segment_image(self, image_path):
        """Segment image into three parts with parity"""
        img = Image.open(image_path)
        img_array = np.array(img)
        
        # Calculate segment sizes ensuring they're equal
        height = img_array.shape[0]
        segment_height = height // 3
        remainder = height % 3
        
        # Adjust segments to handle uneven division
        if remainder == 0:
            R1 = img_array[:segment_height]
            R2 = img_array[segment_height:2*segment_height]
            R3 = img_array[2*segment_height:]
        else:
            # Pad the array to make it divisible by 3
            pad_amount = (3 - remainder)
            padded_array = np.pad(img_array, ((0, pad_amount), (0, 0), (0, 0)) if len(img_array.shape) == 3 
                                else ((0, pad_amount), (0, 0)))
            new_height = padded_array.shape[0]
            segment_height = new_height // 3
            
            R1 = padded_array[:segment_height]
            R2 = padded_array[segment_height:2*segment_height]
            R3 = padded_array[2*segment_height:]
        
        # Calculate parity based on RAID level
        if self.raid_level == 5:
            parity = np.bitwise_xor(np.bitwise_xor(R1, R2), R3)  # XOR for RAID 5
            return R1, R2, R3, parity
        else:  # RAID 6
            parity1 = np.bitwise_xor(np.bitwise_xor(R1, R2), R3)
            # For RAID 6, using a different operation for second parity
            parity2 = np.bitwise_xor(np.bitwise_xor(R1, R2), np.roll(R3, 1, axis=0))
            return R1, R2, R3, parity1, parity2
    
    def reconstruct_image(self, segments, failed_segments=None):
        """Reconstruct image from available segments"""
        if self.raid_level == 5:
            R1, R2, R3, parity = segments
            if failed_segments:
                # Reconstruct failed segment using XOR
                if 'R1' in failed_segments:
                    R1 = np.bitwise_xor(np.bitwise_xor(R2, R3), parity)
                elif 'R2' in failed_segments:
                    R2 = np.bitwise_xor(np.bitwise_xor(R1, R3), parity)
                elif 'R3' in failed_segments:
                    R3 = np.bitwise_xor(np.bitwise_xor(R1, R2), parity)
                    
        else:  # RAID 6
            R1, R2, R3, parity1, parity2 = segments
            if failed_segments and len(failed_segments) <= 2:
                if 'R1' in failed_segments and 'R2' in failed_segments:
                    # Reconstruct R1 and R2 using R3 and parities
                    R1 = np.bitwise_xor(np.bitwise_xor(R3, parity1), parity2)
                    R2 = np.bitwise_xor(np.bitwise_xor(R1, R3), parity1)
                # Add other RAID 6 recovery scenarios as needed
                
        # Combine segments
        reconstructed = np.vstack((R1, R2, R3))
        
        # Convert back to uint8 if needed
        if reconstructed.dtype != np.uint8:
            reconstructed = reconstructed.astype(np.uint8)
            
        return Image.fromarray(reconstructed) 