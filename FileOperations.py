import os
import shutil
import logging
from Watcher import Watcher

class FileOperations:
    # Add log level class variable
    log_level = "basic"  # Can be "basic" or "debug"
    
    @staticmethod
    def set_log_level(level):
        """
        Set the logging level for FileOperations.
        
        Args:
            level (str): Logging level - either "basic" or "debug"
        """
        if level in ["basic", "debug"]:
            FileOperations.log_level = level
            logging.info(f"[FileOperations] Log level set to: {level}")

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
            # Basic level logging - only start of operation
            if FileOperations.log_level == "basic":
                logging.info(f"[FileOperations] Copying file")
            else:
                logging.debug(f"[FileOperations] Copying file from {source} to {target}")
            
            if not os.path.exists(source):
                logging.error(f"[FileOperations] Source file does not exist")  # Keep error in both modes
                return False
                
            # Debug level logging
            if FileOperations.log_level == "debug":
                source_size = os.path.getsize(source)
                logging.debug(f"[FileOperations] Source file size: {source_size} bytes")
            
            # Create target directory if it doesn't exist
            os.makedirs(os.path.dirname(target), exist_ok=True)
            
            # Use explicit open and write to ensure content is copied
            with open(source, 'rb') as src_file:
                with open(target, 'wb') as dst_file:
                    dst_file.write(src_file.read())
            
            # Verify the copy
            if os.path.exists(target):
                if FileOperations.log_level == "debug":
                    target_size = os.path.getsize(target)
                    source_size = os.path.getsize(source)
                    logging.debug(f"[FileOperations] Target file size: {target_size} bytes")
                    if target_size != source_size:
                        logging.error(f"[FileOperations] File size mismatch! Source: {source_size}, Target: {target_size}")
                        return False
            
            # Copy metadata (timestamps, permissions)
            shutil.copystat(source, target)
            
            # Success logging based on level
            if FileOperations.log_level == "debug":
                logging.debug(f"[FileOperations] Successfully copied file from {source} to {target}")
            
            return True
            
        except (IOError, OSError) as e:
            logging.error(f"[FileOperations] Copy failed")  # Simplified error in basic mode
            if FileOperations.log_level == "debug":
                logging.debug(f"[FileOperations] Copy error details: {str(e)}")
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
            # Basic level logging - only start of operation
            if FileOperations.log_level == "basic":
                logging.info(f"[FileOperations] Deleting file")
            else:
                logging.debug(f"[FileOperations] Deleting file: {file_path}")
            
            if os.path.exists(file_path):
                if FileOperations.log_level == "debug":
                    file_size = os.path.getsize(file_path)
                    logging.debug(f"[FileOperations] Deleting file of size: {file_size} bytes")
                
                os.remove(file_path)
                return True
            else:
                if FileOperations.log_level == "debug":
                    logging.debug(f"[FileOperations] File not found for deletion")
                return False
                
        except (IOError, OSError) as e:
            logging.error(f"[FileOperations] Delete failed")  # Simplified error in basic mode
            if FileOperations.log_level == "debug":
                logging.debug(f"[FileOperations] Delete error details: {str(e)}")
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
            # Basic level logging - only start of operation
            if FileOperations.log_level == "basic":
                logging.info(f"[FileOperations] Validating file")
            else:
                logging.debug(f"[FileOperations] Validating file: {file_path}")
            
            if not os.path.exists(file_path):
                logging.error(f"[FileOperations] File not found")  # Keep error in both modes
                return False
                
            watcher = Watcher()
            actual_hash = watcher.get_file_hash(file_path)
            
            if actual_hash == expected_hash:
                if FileOperations.log_level == "debug":
                    logging.debug(f"[FileOperations] Hash match - Expected: {expected_hash}, Actual: {actual_hash}")
                return True
            else:
                if FileOperations.log_level == "debug":
                    logging.debug(f"[FileOperations] Hash mismatch - Expected: {expected_hash}, Actual: {actual_hash}")
                return False
                
        except (IOError, OSError) as e:
            logging.error(f"[FileOperations] Validation failed")  # Simplified error in basic mode
            if FileOperations.log_level == "debug":
                logging.debug(f"[FileOperations] Validation error details: {str(e)}")
            return False
