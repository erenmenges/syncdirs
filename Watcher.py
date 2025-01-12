import os
import hashlib
from datetime import datetime

class Watcher:
    def __init__(self):
        self.file_metadata = {}  # {file_path: {'hash': hash_value, 'last_modified': timestamp}}
        self.last_scanned_directory = None
        self.last_scan_time = None
    
    def get_file_hash(self, file_path):
        """Calculate MD5 hash of file contents."""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            buf = f.read(4096)
            while buf:
                hasher.update(buf)
                buf = f.read(4096)
        return hasher.hexdigest()
    
    def scan_directories(self, directory):
        """
        Scan directory for files and update file_metadata.
        
        Args:
            directory (str): Path to directory to scan
            
        Returns:
            dict: Dictionary of changed files with their change types
        """
        changes = {}
        
        # Update scan information
        self.last_scanned_directory = os.path.abspath(directory)
        self.last_scan_time = datetime.now()
        
        # Walk through directory
        for root, _, files in os.walk(directory):
            for filename in files:
                file_path = os.path.join(root, filename)
                
                try:
                    # Get current file stats
                    current_timestamp = os.path.getmtime(file_path)
                    current_hash = self.get_file_hash(file_path)
                    
                    # Check if file is new or modified
                    if file_path not in self.file_metadata:
                        changes[file_path] = 'created'
                        self.file_metadata[file_path] = {
                            'hash': current_hash,
                            'last_modified': current_timestamp
                        }
                    else:
                        old_metadata = self.file_metadata[file_path]
                        if (current_hash != old_metadata['hash'] or 
                            current_timestamp != old_metadata['last_modified']):
                            changes[file_path] = 'modified'
                            self.file_metadata[file_path].update({
                                'hash': current_hash,
                                'last_modified': current_timestamp
                            })
                except (IOError, OSError) as e:
                    print(f"Error processing file {file_path}: {e}")
                    continue
        
        # Check for deleted files
        existing_files = set()
        for root, _, files in os.walk(directory):
            for filename in files:
                existing_files.add(os.path.join(root, filename))
        
        # Find deleted files
        tracked_files = set(self.file_metadata.keys())
        deleted_files = tracked_files - existing_files
        
        for deleted_file in deleted_files:
            changes[deleted_file] = 'deleted'
            del self.file_metadata[deleted_file]
        
        return changes
