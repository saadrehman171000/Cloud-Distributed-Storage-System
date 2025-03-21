import numpy as np
from PIL import Image
import os
import logging

class RAIDManager:
    def __init__(self, storage_path):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
    def segment_image(self, image_path):
        """Split image into R1, R2, R3 segments"""
        self.logger.info(f"Segmenting image: {image_path}")
        img = Image.open(image_path)
        img_array = np.array(img)
        
        # Store original shape for reconstruction
        self._original_shape = img_array.shape
        
        # Calculate segment height (ensure divisible by 3)
        height = img_array.shape[0]
        segment_height = (height + 2) // 3
        target_height = segment_height * 3
        
        # Pad image if needed
        if height != target_height:
            padding = target_height - height
            if len(img_array.shape) == 3:  # Color image
                pad_width = ((0, padding), (0, 0), (0, 0))
            else:  # Grayscale image
                pad_width = ((0, padding), (0, 0))
            img_array = np.pad(img_array, pad_width, mode='constant')
        
        # Split into three equal segments
        R1 = img_array[:segment_height]
        R2 = img_array[segment_height:2*segment_height]
        R3 = img_array[2*segment_height:]
        
        self.logger.debug(f"Original shape: {img_array.shape}")
        self.logger.debug(f"Segment shapes: R1={R1.shape}, R2={R2.shape}, R3={R3.shape}")
        
        return [R1, R2, R3]  # Return as list for consistent handling
        
    def calculate_parity_raid5(self, segments):
        """Calculate RAID 5 parity using XOR"""
        R1, R2, R3 = segments
        parity = np.bitwise_xor(np.bitwise_xor(R1, R2), R3)
        return parity
        
    def calculate_parity_raid6(self, segments):
        """Calculate RAID 6 dual parity"""
        R1, R2, R3 = segments
        
        # P parity - simple XOR
        P = np.bitwise_xor(np.bitwise_xor(R1, R2), R3)
        
        # Q parity - diagonal XOR with rotations
        Q1 = np.roll(R1, 1, axis=0)
        Q2 = np.roll(R2, 2, axis=0)
        Q3 = np.roll(R3, 3, axis=0)
        Q = np.bitwise_xor(np.bitwise_xor(Q1, Q2), Q3)
        
        return P, Q
        
    def recover_raid5(self, available_segments, parity):
        """Recover data using RAID 5"""
        if len(available_segments) < 2:
            raise ValueError("Need at least 2 segments for RAID 5 recovery")
        
        # Recover missing segment
        recovered = parity.copy()
        for segment in available_segments:
            recovered = np.bitwise_xor(recovered, segment)
        
        # Return all segments in correct order
        segments = list(available_segments)
        segments.append(recovered)
        return segments
        
    def recover_raid6(self, available_segments, parities):
        """Recover data using RAID 6"""
        P, Q = parities
        if len(available_segments) < 1:
            raise ValueError("Need at least 1 segment for RAID 6 recovery")
        
        S = available_segments[0]  # Known segment
        
        # First recover R1 using P and S
        R1 = np.bitwise_xor(P, np.bitwise_xor(S, Q))
        
        # Recover R2 using diagonal parity
        Q1 = np.roll(R1, 1, axis=0)
        Q3 = np.roll(S, 3, axis=0)
        Q2 = np.bitwise_xor(Q, np.bitwise_xor(Q1, Q3))
        R2 = np.roll(Q2, -2, axis=0)  # Reverse the roll
        
        # Verify recovery using P parity
        P_verify = np.bitwise_xor(np.bitwise_xor(R1, R2), S)
        if not np.array_equal(P_verify, P):
            self.logger.warning("RAID 6 recovery verification failed")
            # Try alternative recovery
            R2 = np.bitwise_xor(P, np.bitwise_xor(R1, S))
        
        # Return segments in order
        return [R1, R2, S]

    def reconstruct_image(self, segments):
        """Reconstruct image from segments"""
        try:
            # Convert segments to list if it's a numpy array
            if isinstance(segments, np.ndarray):
                if len(segments.shape) == 3:
                    segments = [segments]
                else:
                    raise ValueError(f"Invalid segment shape: {segments.shape}")
            
            # Stack segments vertically
            full_image = np.vstack(segments)
            
            # Trim to original shape if needed
            if hasattr(self, '_original_shape'):
                full_image = full_image[:self._original_shape[0]]
                if len(self._original_shape) > 2:
                    full_image = full_image[:, :self._original_shape[1], :self._original_shape[2]]
                else:
                    full_image = full_image[:, :self._original_shape[1]]
            
            # Ensure uint8 type
            if full_image.dtype != np.uint8:
                full_image = full_image.astype(np.uint8)
            
            return Image.fromarray(full_image)
            
        except Exception as e:
            self.logger.error(f"Failed to reconstruct image: {e}")
            raise

    def save_image(self, image_data, output_path):
        """Save image data to file"""
        try:
            # Convert array to image
            if isinstance(image_data, np.ndarray):
                image = Image.fromarray(image_data.astype('uint8'))
            else:
                image = image_data
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save image
            image.save(output_path)
            return True
        except Exception as e:
            self.logger.error(f"Failed to save image: {e}")
            return False 