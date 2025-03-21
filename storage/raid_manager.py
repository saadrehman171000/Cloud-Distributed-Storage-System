import numpy as np
from PIL import Image
import os

class RAIDManager:
    def __init__(self, storage_path):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
        
    def segment_image(self, image_path):
        """Split image into R1, R2, R3 segments"""
        img = Image.open(image_path)
        img_array = np.array(img)
        
        # Calculate segment sizes
        height = img_array.shape[0]
        segment_height = height // 3
        
        # Create segments
        R1 = img_array[:segment_height]
        R2 = img_array[segment_height:2*segment_height]
        R3 = img_array[2*segment_height:]
        
        return R1, R2, R3
        
    def calculate_parity_raid5(self, segments):
        """Calculate RAID 5 parity using XOR"""
        R1, R2, R3 = segments
        parity = np.bitwise_xor(np.bitwise_xor(R1, R2), R3)
        return parity
        
    def calculate_parity_raid6(self, segments):
        """Calculate RAID 6 dual parity"""
        R1, R2, R3 = segments
        P = np.bitwise_xor(np.bitwise_xor(R1, R2), R3)  # First parity
        Q = np.roll(np.bitwise_xor(np.bitwise_xor(R1, R2), R3), 1, axis=0)  # Second parity
        return P, Q
        
    def recover_raid5(self, available_segments, parity):
        """Recover data using RAID 5: R1+R2+R3"""
        if len(available_segments) < 2:
            raise ValueError("Need at least 2 segments for RAID 5 recovery")
            
        # XOR available segments with parity to recover missing segment
        recovered = parity.copy()
        for segment in available_segments:
            recovered = np.bitwise_xor(recovered, segment)
        return recovered
        
    def recover_raid6(self, available_segments, parities):
        """Recover data using RAID 6: R1+R2-R3"""
        P, Q = parities
        if len(available_segments) < 1:
            raise ValueError("Need at least 1 segment for RAID 6 recovery")
            
        # Use both parities to recover up to two failed segments
        if len(available_segments) == 1:
            # Complex recovery using both parities
            S = available_segments[0]
            R1 = np.bitwise_xor(P, np.bitwise_xor(S, Q))
            R2 = np.bitwise_xor(P, np.bitwise_xor(R1, S))
            return [R1, R2]
        else:
            # Simple recovery using P parity
            return self.recover_raid5(available_segments, P)

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