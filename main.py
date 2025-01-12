import os
import time
import threading
import argparse
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List
from Watcher import Watcher
from SyncManager import SyncManager
from ConflictResolver import ResolutionPolicy

# Add logging configuration at the top
logging.basicConfig(
    level=logging.INFO,
    format='[%(name)s] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

class DirectorySynchronizer:
    def __init__(self, directories: List[str], resolution_policy: ResolutionPolicy = ResolutionPolicy.MANUAL):
        """
        Initialize the directory synchronizer with a list of directories to keep in sync.
        The first directory in the list will be the initial source.
        """
        self.logger = logging.getLogger('MAIN')
        self.logger.info('Initializing DirectorySynchronizer')
        
        # Validate directories
        for directory in directories:
            if not os.path.exists(directory):
                self.logger.error(f'Directory does not exist: {directory}')
                raise ValueError(f"Directory does not exist: {directory}")
            
        self.logger.info(f'Validated {len(directories)} directories')
        
        self.directories = [os.path.abspath(d) for d in directories]
        self.watchers = {dir_path: Watcher() for dir_path in self.directories}
        self.resolution_policy = resolution_policy
        self.running = False
        self.lock = threading.Lock()
        self.sync_condition = threading.Condition(self.lock)
        self.is_syncing = False
        
        self.logger.info(f'Using resolution policy: {resolution_policy}')
        
    def _initialize_metadata(self):
        """Initialize metadata for the first directory and sync others with it."""
        self.logger.info('Initializing metadata')
        source_dir = self.directories[0]
        target_dirs = self.directories[1:]
        
        self.logger.info(f'Scanning source directory: {source_dir}')
        self.watchers[source_dir].scan_directories(source_dir)
        
        # Initial sync of other directories
        self.logger.info('Starting initial sync of target directories')
        sync_manager = SyncManager(source_dir, target_dirs, self.resolution_policy)
        initial_changes = {
            os.path.relpath(file_path, source_dir): 'created'
            for file_path in self.watchers[source_dir].file_metadata.keys()
        }
        
        self.logger.info(f'Found {len(initial_changes)} files to sync initially')
        sync_manager.sync_files(initial_changes)
        
        # Initialize metadata for other directories
        self.logger.info('Initializing metadata for target directories')
        for directory in target_dirs:
            self.logger.info(f'Scanning target directory: {directory}')
            self.watchers[directory].scan_directories(directory)
    
    def _watch_directory(self, directory: str):
        """Watch a single directory for changes."""
        self.logger.info(f'Starting watcher for directory: {directory}')
        watcher = self.watchers[directory]
        
        while self.running:
            try:
                # Wait if sync is in progress
                with self.sync_condition:
                    while self.is_syncing and self.running:
                        self.logger.debug(f'Waiting for sync to complete on {directory}')
                        self.sync_condition.wait()
                    
                    if not self.running:
                        self.logger.info(f'Stopping watcher for directory: {directory}')
                        break
                
                # Move scanning outside the lock to prevent blocking other watchers
                self.logger.debug(f'Scanning for changes in {directory}')
                changes = watcher.scan_directories(directory)
                
                if changes:
                    self.logger.info(f'Detected {len(changes)} changes in {directory}')
                    with self.sync_condition:
                        self.is_syncing = True
                    self._handle_changes(directory, changes)
                    
                # Add a small delay between scans to prevent excessive CPU usage
                time.sleep(0.3)
                        
            except Exception as e:
                self.logger.error(f'Error watching directory {directory}: {e}')
                time.sleep(1)  # Prevent rapid-fire errors
    
    def _handle_changes(self, source_dir: str, changes: dict):
        """Handle changes detected in a directory by syncing to all other directories."""
        self.logger.info(f'Handling changes from {source_dir}')
        target_dirs = [d for d in self.directories if d != source_dir]
        sync_manager = SyncManager(source_dir, target_dirs, self.resolution_policy)
        
        try:
            # Convert absolute paths to relative paths for sync manager
            relative_changes = {
                os.path.relpath(file_path, source_dir): change_type
                for file_path, change_type in changes.items()
            }
            
            self.logger.info(f'Syncing {len(relative_changes)} changes to {len(target_dirs)} target directories')
            for path, change_type in relative_changes.items():
                self.logger.debug(f'Change detected: {change_type} - {path}')
            
            # Perform the sync
            sync_manager.sync_files(relative_changes)
            
            # Update metadata for all directories after sync
            self.logger.info('Updating metadata for all directories after sync')
            for directory in self.directories:
                self.logger.debug(f'Refreshing metadata for {directory}')
                self.watchers[directory].scan_directories(directory)
                
        except Exception as e:
            self.logger.error(f'Error during sync operation: {e}')
        finally:
            # Move this block outside the with statement to properly clear sync state
            self.is_syncing = False
            with self.sync_condition:
                self.sync_condition.notify_all()
                self.logger.debug('Sync state cleared')
    
    def start(self):
        """Start the directory synchronization process."""
        self.logger.info('Starting directory synchronization')
        self._initialize_metadata()
        
        self.logger.info('Starting directory watchers')
        self.running = True
        
        # Start watching all directories concurrently
        with ThreadPoolExecutor(max_workers=len(self.directories)) as executor:
            self.logger.info(f'Created thread pool with {len(self.directories)} workers')
            watch_futures = [
                executor.submit(self._watch_directory, directory)
                for directory in self.directories
            ]
            
        try:
            # Wait for all watchers to complete (they won't unless there's an error)
            for future in watch_futures:
                future.result()
        except KeyboardInterrupt:
            self.logger.info('Received keyboard interrupt')
            self.stop()
    
    def stop(self):
        """Stop the directory synchronization process."""
        self.logger.info('Stopping directory synchronization')
        with self.sync_condition:
            self.running = False
            self.sync_condition.notify_all()
        self.logger.info('Directory synchronization stopped')

def main():
    logger = logging.getLogger('MAIN')
    logger.info('Starting Directory Synchronization Tool')
    
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Directory Synchronization Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
    # Sync with manual conflict resolution (default):
    python main.py /path/to/source /path/to/target1 /path/to/target2

    # Sync with newest-wins policy:
    python main.py -p newest /path/to/source /path/to/target1 /path/to/target2
        '''
    )

    parser.add_argument('-p', '--policy',
                        choices=['manual', 'newest'],
                        default='manual',
                        help='Conflict resolution policy (default: manual)')
    
    parser.add_argument('directories',
                        nargs='+',
                        help='Directories to sync. First directory is the source.')

    args = parser.parse_args()
    logger.info(f'Parsed command line arguments: {args}')

    # Validate minimum number of directories
    if len(args.directories) < 2:
        logger.error('Not enough directories specified')
        parser.error("At least two directories (source and one target) are required")

    # Convert policy string to ResolutionPolicy enum
    policy_map = {
        'manual': ResolutionPolicy.MANUAL,
        'newest': ResolutionPolicy.NEWEST_WINS
    }
    resolution_policy = policy_map[args.policy]
    logger.info(f'Using resolution policy: {resolution_policy}')

    try:
        # Initialize and start the synchronizer
        logger.info('Creating DirectorySynchronizer instance')
        synchronizer = DirectorySynchronizer(args.directories, resolution_policy)
        synchronizer.start()
    except KeyboardInterrupt:
        logger.info('Received keyboard interrupt')
        if 'synchronizer' in locals():
            synchronizer.stop()
        logger.info('Synchronization stopped by user')
    except Exception as e:
        logger.error(f'Fatal error: {e}')
        return 1
    return 0

if __name__ == "__main__":
    exit(main())
