import os
import hashlib
import logging
from datetime import datetime

class Watcher:
    def __init__(self):
        """Initialize the Watcher with logging configuration."""
        self.file_metadata = {}  # {file_path: {'hash': hash_value, 'last_modified': timestamp}}
        self.last_scanned_directory = None
        self.last_scan_time = None
        
        # Set up logger for the Watcher class
        self.logger = logging.getLogger('Watcher')
        self.logger.info('Initializing Watcher')
    
    def get_file_hash(self, file_path):
        """Calculate MD5 hash of file contents."""
        self.logger.debug(f'Calculating hash for file: {file_path}')
        hasher = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                buf = f.read(4096)
                while buf:
                    hasher.update(buf)
                    buf = f.read(4096)
            file_hash = hasher.hexdigest()
            self.logger.debug(f'Hash calculated for {file_path}: {file_hash}')
            return file_hash
        except (IOError, OSError) as e:
            self.logger.error(f'Error calculating hash for {file_path}: {str(e)}')
            raise
    
    def scan_directories(self, directory):
        """
        Scan directory for files and update file_metadata.
        
        Args:
            directory (str): Path to directory to scan
            
        Returns:
            dict: Dictionary of changed files with their change types
        """
        self.logger.info(f'Starting directory scan: {directory}')
        changes = {}
        
        # Update scan information
        self.last_scanned_directory = os.path.abspath(directory)
        self.last_scan_time = datetime.now()
        self.logger.debug(f'Scan started at: {self.last_scan_time}')
        
        try:
            # Walk through directory
            for root, _, files in os.walk(directory):
                self.logger.debug(f'Scanning directory: {root}')
                for filename in files:
                    file_path = os.path.join(root, filename)
                    self.logger.debug(f'Processing file: {filename}')
                    
                    try:
                        # Get current file stats
                        current_timestamp = os.path.getmtime(file_path)
                        self.logger.debug(f'File timestamp: {datetime.fromtimestamp(current_timestamp)}')
                        
                        current_hash = self.get_file_hash(file_path)
                        
                        # Check if file is new or modified
                        if file_path not in self.file_metadata:
                            self.logger.info(f'New file detected: {file_path}')
                            changes[file_path] = 'created'
                            self.file_metadata[file_path] = {
                                'hash': current_hash,
                                'last_modified': current_timestamp
                            }
                        else:
                            old_metadata = self.file_metadata[file_path]
                            # Compare hash to detect modifications
                            if current_hash != old_metadata['hash']:
                                self.logger.info(f'Modified file detected: {file_path}')
                                self.logger.debug(f'Old hash: {old_metadata["hash"]}')
                                self.logger.debug(f'New hash: {current_hash}')
                                changes[file_path] = 'modified'
                                self.file_metadata[file_path].update({
                                    'hash': current_hash,
                                    'last_modified': current_timestamp
                                })
                            else:
                                self.logger.debug(f'No changes detected for: {file_path}')
                                
                    except (IOError, OSError) as e:
                        self.logger.error(f'Error processing file {file_path}: {str(e)}')
                        continue
            
            # Check for deleted files
            self.logger.debug('Checking for deleted files')
            existing_files = set()
            for root, _, files in os.walk(directory):
                for filename in files:
                    existing_files.add(os.path.join(root, filename))
            
            # Find deleted files
            tracked_files = set(self.file_metadata.keys())
            deleted_files = tracked_files - existing_files
            
            for deleted_file in deleted_files:
                self.logger.info(f'Deleted file detected: {deleted_file}')
                changes[deleted_file] = 'deleted'
                del self.file_metadata[deleted_file]
            
            # Log summary of changes
            self.logger.info(f'Scan completed. Found {len(changes)} changes:')
            for file_path, change_type in changes.items():
                self.logger.info(f'- {change_type}: {file_path}')
            
            return changes
            
        except Exception as e:
            self.logger.error(f'Error during directory scan: {str(e)}')
            self.logger.exception('Detailed error information:')
            raise
