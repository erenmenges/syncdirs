import os
import shutil
import logging
from Watcher import Watcher

class FileOperations:
    @staticmethod
    def copy_file(source, target):
        """
        Copy a file from source to target path.
        
        Args:
            source (str): Path to source file
            target (str): Path to target destination
            
        Returns:
            bool: True if copy successful, False otherwise
        """
        try:
            logging.info(f"[FileOperations] Attempting to copy file from {source} to {target}")
            
            if not os.path.exists(source):
                logging.error(f"[FileOperations] Source file does not exist: {source}")
                return False
                
            # Log file sizes before copy
            source_size = os.path.getsize(source)
            logging.info(f"[FileOperations] Source file size: {source_size} bytes")
            
            # Create target directory if it doesn't exist
            os.makedirs(os.path.dirname(target), exist_ok=True)
            
            # Use explicit open and write to ensure content is copied
            with open(source, 'rb') as src_file:
                with open(target, 'wb') as dst_file:
                    dst_file.write(src_file.read())
            
            # Verify the copy
            if os.path.exists(target):
                target_size = os.path.getsize(target)
                logging.info(f"[FileOperations] Target file size: {target_size} bytes")
                if target_size != source_size:
                    logging.error(f"[FileOperations] File size mismatch! Source: {source_size}, Target: {target_size}")
                    return False
            
            # Copy metadata (timestamps, permissions)
            shutil.copystat(source, target)
            
            logging.info(f"[FileOperations] Successfully copied file from {source} to {target}")
            return True
            
        except (IOError, OSError) as e:
            logging.error(f"[FileOperations] Error copying file from {source} to {target}: {e}")
            return False

    @staticmethod
    def delete_file(file_path):
        """
        Delete a file at the specified path.
        
        Args:
            file_path (str): Path to file to delete
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            logging.info(f"[FileOperations] Attempting to delete file: {file_path}")
            
            if os.path.exists(file_path):
                os.remove(file_path)
                logging.info(f"[FileOperations] Successfully deleted file: {file_path}")
                return True
            else:
                logging.warning(f"[FileOperations] File not found for deletion: {file_path}")
                return False
        except (IOError, OSError) as e:
            logging.error(f"[FileOperations] Error deleting file {file_path}: {e}")
            return False

    @staticmethod
    def validate_file(file_path, expected_hash):
        """
        Validate a file by comparing its hash with expected hash.
        Uses Watcher's hashing method for consistency.
        
        Args:
            file_path (str): Path to file to validate
            expected_hash (str): Expected MD5 hash value
            
        Returns:
            bool: True if hashes match, False otherwise
        """
        try:
            logging.info(f"[FileOperations] Validating file: {file_path}")
            
            if not os.path.exists(file_path):
                logging.error(f"[FileOperations] File not found for validation: {file_path}")
                return False
                
            watcher = Watcher()
            actual_hash = watcher.get_file_hash(file_path)
            
            if actual_hash == expected_hash:
                logging.info(f"[FileOperations] File validation successful: {file_path}")
                logging.debug(f"[FileOperations] Hash match - Expected: {expected_hash}, Actual: {actual_hash}")
                return True
            else:
                logging.warning(f"[FileOperations] File validation failed: {file_path}")
                logging.debug(f"[FileOperations] Hash mismatch - Expected: {expected_hash}, Actual: {actual_hash}")
                return False
                
        except (IOError, OSError) as e:
            logging.error(f"[FileOperations] Error validating file {file_path}: {e}")
            return False
