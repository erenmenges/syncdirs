import os
import hashlib
import logging
from datetime import datetime
import collections

class Watcher:
    def __init__(self, log_level='basic'):
        """
        Initialize the Watcher with logging configuration.
        
        Args:
            log_level (str): Logging level - 'basic' or 'debug'. Defaults to 'basic'
        """
        self.file_metadata = {}
        self.last_scanned_directory = None
        self.last_scan_time = None
        
        # Set up logger for the Watcher class
        self.logger = logging.getLogger('Watcher')
        
        # Set logging level based on parameter
        if log_level.lower() == 'debug':
            self.logger.setLevel(logging.DEBUG)
        else:  # basic level
            self.logger.setLevel(logging.INFO)
            
        # Add handler if not already present
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            
        # Only log initialization in debug mode
        self.logger.debug('Initializing Watcher')
    
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
            self.logger.error(f'Error accessing file {file_path}')  # Simplified error message
            raise
    
    def scan_directories(self, directory):
        """
        Scan directory for files and update file_metadata.
        """
        self.logger.debug(f'Starting directory scan: {directory}')  # Moved to debug
        changes = {}
        existing_files = set()
        
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
                    existing_files.add(file_path)
                    self.logger.debug(f'Processing file: {filename}')
                    
                    try:
                        current_timestamp = os.path.getmtime(file_path)
                        self.logger.debug(f'File timestamp: {datetime.fromtimestamp(current_timestamp)}')
                        
                        current_hash = self.get_file_hash(file_path)
                        
                        if file_path not in self.file_metadata:
                            changes[file_path] = 'created'
                            self.file_metadata[file_path] = {
                                'hash': current_hash,
                                'last_modified': current_timestamp
                            }
                        else:
                            old_metadata = self.file_metadata[file_path]
                            if current_hash != old_metadata['hash']:
                                changes[file_path] = 'modified'
                                self.logger.debug(f'Old hash: {old_metadata["hash"]}')
                                self.logger.debug(f'New hash: {current_hash}')
                                self.file_metadata[file_path].update({
                                    'hash': current_hash,
                                    'last_modified': current_timestamp
                                })
                            else:
                                self.logger.debug(f'No changes detected for: {file_path}')
                                
                    except (IOError, OSError) as e:
                        self.logger.error(f'Error processing file {file_path}')  # Simplified error message
                        continue
            
            # Check for deleted files without a second walk
            self.logger.debug('Checking for deleted files')
            tracked_files = set(self.file_metadata.keys())
            deleted_files = tracked_files - existing_files
            
            for deleted_file in deleted_files:
                changes[deleted_file] = 'deleted'
                del self.file_metadata[deleted_file]
            
            # Log summary of changes
            if changes:
                change_counts = collections.Counter(changes.values())
                summary = ', '.join([f"{count} {change_type}" for change_type, count in change_counts.items()])
                self.logger.info(f'Changes detected: {len(changes)} files ({summary})')
                # Detailed changes only in debug mode
                for file_path, change_type in changes.items():
                    self.logger.debug(f'- {change_type}: {file_path}')
            
            return changes
            
        except Exception as e:
            self.logger.error('Error during directory scan')  # Simplified error message
            self.logger.debug(f'Detailed error: {str(e)}')  # Full error only in debug
            raise
