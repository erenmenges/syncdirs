import os
import shutil
import logging
from Watcher import Watcher

class FileOperations:
    # Add class-specific logger
    logger = logging.getLogger('FileOperations')
    log_level = "basic"
    watcher = None  # Class-level Watcher instance
    
    @staticmethod
    def set_log_level(level):
        if level in ["basic", "debug"]:
            FileOperations.log_level = level
            # Configure logger level
            if level == "debug":
                FileOperations.logger.setLevel(logging.DEBUG)
            else:
                FileOperations.logger.setLevel(logging.INFO)
                
            # Add handler if not present
            if not FileOperations.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                FileOperations.logger.addHandler(handler)
                
            FileOperations.logger.info(f"Log level set to: {level}")

    @staticmethod
    def initialize_watcher():
        if FileOperations.watcher is None:
            FileOperations.watcher = Watcher(log_level=FileOperations.log_level)
    
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
            if FileOperations.log_level == "basic":
                FileOperations.logger.info("Copying file")
            else:
                FileOperations.logger.debug(f"Copying file from {source} to {target}")
            
            if not os.path.exists(source):
                FileOperations.logger.error("Source file does not exist")
                return False
                
            # Create target directory if it doesn't exist
            os.makedirs(os.path.dirname(target), exist_ok=True)
            
            # Use shutil.copy2 for efficient copying with metadata preservation
            shutil.copy2(source, target)
            
            # Verify the copy
            if os.path.exists(target):
                if FileOperations.log_level == "debug":
                    target_size = os.path.getsize(target)
                    source_size = os.path.getsize(source)
                    FileOperations.logger.debug(f"Target file size: {target_size} bytes")
                    if target_size != source_size:
                        FileOperations.logger.error(f"File size mismatch! Source: {source_size}, Target: {target_size}")
                        return False
            
            return True
            
        except (IOError, OSError) as e:
            FileOperations.logger.error("Copy failed")
            if FileOperations.log_level == "debug":
                FileOperations.logger.debug(f"Copy error details: {str(e)}")
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
            if FileOperations.log_level == "basic":
                FileOperations.logger.info("Deleting file")
            else:
                FileOperations.logger.debug(f"Deleting file: {file_path}")
            
            if not os.path.exists(file_path):
                FileOperations.logger.error("File not found")  # More specific basic error
                return False
            
            if not os.access(file_path, os.W_OK):
                FileOperations.logger.error("Permission denied")  # Handle permission errors specifically
                return False
                
            os.remove(file_path)
            return True
                
        except PermissionError as e:
            FileOperations.logger.error("Permission denied while deleting file")
            if FileOperations.log_level == "debug":
                FileOperations.logger.debug(f"Permission error details: {str(e)}")
            return False
        except OSError as e:
            FileOperations.logger.error("Failed to delete file")
            if FileOperations.log_level == "debug":
                FileOperations.logger.debug(f"Delete error details: {str(e)}")
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
            if FileOperations.log_level == "basic":
                FileOperations.logger.info("Validating file")
            else:
                FileOperations.logger.debug(f"Validating file: {file_path}")
            
            if not os.path.exists(file_path):
                FileOperations.logger.error("File not found")
                return False
            
            # Initialize watcher if needed
            FileOperations.initialize_watcher()
            actual_hash = FileOperations.watcher.get_file_hash(file_path)
            
            if actual_hash == expected_hash:
                if FileOperations.log_level == "debug":
                    FileOperations.logger.debug(f"[FileOperations] Hash match - Expected: {expected_hash}, Actual: {actual_hash}")
                return True
            else:
                if FileOperations.log_level == "debug":
                    FileOperations.logger.debug(f"[FileOperations] Hash mismatch - Expected: {expected_hash}, Actual: {actual_hash}")
                return False
                
        except (IOError, OSError) as e:
            FileOperations.logger.error("Validation failed")  # Simplified error in basic mode
            if FileOperations.log_level == "debug":
                FileOperations.logger.debug(f"[FileOperations] Validation error details: {str(e)}")
            return False
