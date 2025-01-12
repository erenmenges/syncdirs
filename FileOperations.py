import os
import shutil
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
            # Create target directory if it doesn't exist
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copy2(source, target)
            return True
        except (IOError, OSError) as e:
            print(f"Error copying file from {source} to {target}: {e}")
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
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except (IOError, OSError) as e:
            print(f"Error deleting file {file_path}: {e}")
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
            watcher = Watcher()
            actual_hash = watcher.get_file_hash(file_path)
            return actual_hash == expected_hash
        except (IOError, OSError) as e:
            print(f"Error validating file {file_path}: {e}")
            return False
