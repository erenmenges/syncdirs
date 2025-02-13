import os
import logging
from typing import List, Dict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from ConflictResolver import ConflictResolver, ResolutionPolicy
from FileOperations import FileOperations
import threading

class SyncManager:
    def __init__(self, source_dir: str, target_dirs: List[str], 
                 resolution_policy: ResolutionPolicy = ResolutionPolicy.MANUAL,
                 logging_level: str = 'basic',
                 max_workers: int = None):
        """
        Constructor that initializes the sync manager with directories to sync
        and how to handle conflicts
        Args:
            source_dir: Directory to sync from
            target_dirs: List of directories to sync to
            resolution_policy: How to handle conflicts
            logging_level: Logging detail level ('basic' or 'debug')
            max_workers: Maximum number of worker threads
        """
        # Verify source directory exists before proceeding
        if not os.path.exists(source_dir):
            raise ValueError(f"[SyncManager] Source directory does not exist: {source_dir}")
        
        # Store the directories and create conflict resolver instance
        self.source_dir = source_dir
        self.target_dirs = target_dirs
        self.conflict_resolver = ConflictResolver(resolution_policy)
        
        # Initialize dictionary to track sync statistics
        self.sync_stats = {
            'files_synced': 0,
            'files_deleted': 0,
            'conflicts_resolved': 0,
            'failed_operations': 0,
            'start_time': None,
            'end_time': None
        }
        
        # Set up logging configuration
        self.logger = logging.getLogger(__name__)
        self.logging_level = logging_level.lower()
        
        # Set logging level based on parameter
        log_level = logging.INFO if self.logging_level == 'basic' else logging.DEBUG
        
        logging.basicConfig(
            filename='sync_manager.log',
            level=log_level,
            format='%(asctime)s - %(levelname)s - [SyncManager] %(message)s'
        )
        
        # Basic level logging for initialization
        self.logger.info(f"Initialized SyncManager with source: {source_dir}")
        if self.logging_level == 'debug':
            self.logger.debug(f"Target directories: {target_dirs}")
            self.logger.debug(f"Using resolution policy: {resolution_policy}")
            self.logger.debug(f"Logging level set to: {logging_level}")

        # Add thread-safe counters
        self._stats_lock = threading.Lock()

        # Calculate default max workers if none specified
        if max_workers is None:
            max_workers = min(32, (os.cpu_count() or 1) * 4)
        self.max_workers = max_workers

    def _increment_stat(self, stat_name: str) -> None:
        """Thread-safe method to increment a stat counter"""
        with self._stats_lock:
            self.sync_stats[stat_name] += 1

    def sync_files(self, changes: Dict[str, str]) -> None:
        """
        Main method that processes file changes and syncs them to target directories
        using concurrent operations
        """
        self.sync_stats['start_time'] = datetime.now()
        self.logger.info(f"Starting sync operation with {len(changes)} changes")
        
        # Single ThreadPoolExecutor for all operations
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            
            for rel_path, change_type in changes.items():
                if self.logging_level == 'debug':
                    self.logger.debug(f"Processing change: {change_type} for file: {rel_path}")
                
                source_path = os.path.join(self.source_dir, rel_path)
                target_paths = [os.path.join(target_dir, rel_path) 
                                for target_dir in self.target_dirs]
                
                # Submit the task to the executor
                future = executor.submit(
                    self._process_change,
                    change_type,
                    source_path,
                    target_paths,
                    rel_path,
                    executor  # Pass the existing executor
                )
                futures.append(future)
            
            # Process results and collect errors
            errors = []
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    self._increment_stat('failed_operations')
                    errors.append(str(e))
                    self.logger.error(f"Operation failed: {str(e)}")
                    if self.logging_level == 'debug':
                        self.logger.exception("Detailed error information:")
            
            if errors:
                self.logger.error(f"Sync completed with {len(errors)} errors")

        self.sync_stats['end_time'] = datetime.now()
        self.logger.info(f"Sync operation completed. Duration: {self.sync_stats['end_time'] - self.sync_stats['start_time']}")

    def _process_change(self, change_type: str, source_path: str, 
                       target_paths: List[str], rel_path: str,
                       executor: ThreadPoolExecutor) -> None:
        """
        Processes a single file change operation
        """
        try:
            if change_type in ('modified', 'created'):
                if self.logging_level == 'debug':
                    self.logger.debug(f"Handling {change_type} operation for {rel_path}")
                self._handle_file_update(source_path, target_paths, rel_path, executor)
            elif change_type == 'deleted':
                if self.logging_level == 'debug':
                    self.logger.debug(f"Handling deletion operation for {rel_path}")
                self._handle_file_deletion(target_paths, rel_path, executor)
        except Exception as e:
            self.logger.error(f"Failed to process change for {rel_path}: {str(e)}")
            raise

    def _handle_file_update(self, source_path: str, target_paths: List[str], 
                          rel_path: str, executor: ThreadPoolExecutor) -> None:
        """
        Handles updating or creating files, including conflict resolution
        """
        existing_targets = [path for path in target_paths if os.path.exists(path)]
        
        if existing_targets:
            if self.logging_level == 'debug':
                self.logger.debug(f"Found {len(existing_targets)} existing copies of {rel_path}")
                self.logger.debug(f"Initiating conflict resolution for {rel_path}")
            
            conflicting_files = [source_path] + existing_targets
            winner, losers = self.conflict_resolver.resolve_conflict(conflicting_files)
            
            self._increment_stat('conflicts_resolved')
            self.logger.info(f"Resolved conflict for {rel_path}")
            
            if winner == source_path:
                if self.logging_level == 'debug':
                    self.logger.debug(f"Source file won conflict for {rel_path}")
                for target_path in target_paths:
                    executor.submit(self._copy_file, source_path, target_path)
            else:
                if self.logging_level == 'debug':
                    self.logger.debug(f"Target file won conflict for {rel_path}")
                executor.submit(self._copy_file, winner, source_path)
                
                for target_path in target_paths:
                    if target_path != winner:
                        executor.submit(self._copy_file, winner, target_path)
        
        else:
            if self.logging_level == 'debug':
                self.logger.debug(f"No existing copies found for {rel_path}")
            for target_path in target_paths:
                executor.submit(self._copy_file, source_path, target_path)

    def _copy_file(self, source: str, target: str) -> None:
        """
        Helper method to copy a file and update stats
        """
        if FileOperations.copy_file(source, target):
            self._increment_stat('files_synced')
            if self.logging_level == 'debug':
                self.logger.debug(f"Successfully copied {source} to {target}")

    def _handle_file_deletion(self, target_paths: List[str], rel_path: str,
                             executor: ThreadPoolExecutor) -> None:
        """
        Handles deleting files from target directories concurrently
        """
        self.logger.info(f"Processing deletion of {rel_path} from {len(target_paths)} targets")
        
        for target_path in target_paths:
            executor.submit(self._delete_file, target_path, rel_path)

    def _delete_file(self, target_path: str, rel_path: str) -> None:
        """
        Helper method to delete a file and update stats
        """
        self.logger.info(f"Attempting to delete {rel_path} from {target_path}")
        if FileOperations.delete_file(target_path):
            self._increment_stat('files_deleted')
            self.logger.info(f"Successfully deleted {rel_path} from {target_path}")
        else:
            self.logger.warning(f"Failed to delete {rel_path} from {target_path}")

    def generate_summary_report(self) -> Dict:
        """
        Creates a report of what happened during the sync
        """
        self.logger.info("Generating sync summary report")
        
        duration = None
        if self.sync_stats['start_time'] and self.sync_stats['end_time']:
            duration = (self.sync_stats['end_time'] - 
                       self.sync_stats['start_time']).total_seconds()
            self.logger.info(f"Total sync duration: {duration} seconds")

        report = {
            'start_time': self.sync_stats['start_time'],
            'end_time': self.sync_stats['end_time'],
            'duration_seconds': duration,
            'files_synced': self.sync_stats['files_synced'],
            'files_deleted': self.sync_stats['files_deleted'],
            'conflicts_resolved': self.sync_stats['conflicts_resolved'],
            'failed_operations': self.sync_stats['failed_operations'],
            'source_directory': self.source_dir,
            'target_directories': self.target_dirs
        }

        self.logger.info("=== Sync Summary ===")
        for key, value in report.items():
            self.logger.info(f"{key}: {value}")
        self.logger.info("==================")

        return report
