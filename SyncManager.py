import os
import logging
from typing import List, Dict
from datetime import datetime
from ConflictResolver import ConflictResolver, ResolutionPolicy
from FileOperations import FileOperations

class SyncManager:
    def __init__(self, source_dir: str, target_dirs: List[str], 
                 resolution_policy: ResolutionPolicy = ResolutionPolicy.MANUAL):
        """
        Constructor that initializes the sync manager with directories to sync
        and how to handle conflicts
        """
        # Verify source directory exists before proceeding
        if not os.path.exists(source_dir):
            raise ValueError(f"[SyncManager] Source directory does not exist: {source_dir}")
        
        # Store the directories and create conflict resolver instance
        self.source_dir = source_dir              # Directory to sync from
        self.target_dirs = target_dirs            # List of directories to sync to
        self.conflict_resolver = ConflictResolver(resolution_policy)  # Handles file conflicts
        
        # Initialize dictionary to track sync statistics
        self.sync_stats = {
            'files_synced': 0,        # Count of files successfully synced
            'conflicts_resolved': 0,   # Count of conflicts resolved
            'failed_operations': 0,    # Count of failed operations
            'start_time': None,        # When sync started
            'end_time': None          # When sync ended
        }
        
        # Set up logging configuration
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            filename='sync_manager.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - [SyncManager] %(message)s'
        )
        self.logger.info(f"Initialized SyncManager with source: {source_dir}, targets: {target_dirs}")
        self.logger.info(f"Using resolution policy: {resolution_policy}")

    def sync_files(self, changes: Dict[str, str]) -> None:
        """
        Main method that processes file changes and syncs them to target directories
        """
        self.sync_stats['start_time'] = datetime.now()
        self.logger.info(f"Starting sync operation with {len(changes)} changes to process")
        
        for rel_path, change_type in changes.items():
            self.logger.info(f"Processing change: {change_type} for file: {rel_path}")
            source_path = os.path.join(self.source_dir, rel_path)
            target_paths = [os.path.join(target_dir, rel_path) 
                          for target_dir in self.target_dirs]
            
            try:
                if change_type in ('modified', 'created'):
                    self.logger.info(f"Handling {change_type} operation for {rel_path}")
                    self._handle_file_update(source_path, target_paths, rel_path)
                elif change_type == 'deleted':
                    self.logger.info(f"Handling deletion operation for {rel_path}")
                    self._handle_file_deletion(target_paths, rel_path)
                    
            except Exception as e:
                self.sync_stats['failed_operations'] += 1
                self.logger.error(f"Operation failed for {rel_path}: {str(e)}")
                self.logger.exception("Detailed error information:")

        self.sync_stats['end_time'] = datetime.now()
        self.logger.info(f"Sync operation completed. Duration: {self.sync_stats['end_time'] - self.sync_stats['start_time']}")

    def _handle_file_update(self, source_path: str, target_paths: List[str], 
                          rel_path: str) -> None:
        """
        Handles updating or creating files, including conflict resolution
        """
        existing_targets = [path for path in target_paths if os.path.exists(path)]
        
        if existing_targets:
            self.logger.info(f"Found {len(existing_targets)} existing copies of {rel_path}")
            conflicting_files = [source_path] + existing_targets
            self.logger.info(f"Initiating conflict resolution for {rel_path}")
            winner, losers = self.conflict_resolver.resolve_conflict(conflicting_files)
            
            self.sync_stats['conflicts_resolved'] += 1
            self.logger.info(f"Conflict resolved for {rel_path}. Winner: {winner}")
            
            if winner == source_path:
                self.logger.info(f"Source file won conflict for {rel_path}, copying to all targets")
                for target_path in target_paths:
                    self.logger.info(f"Copying {rel_path} to target: {target_path}")
                    if FileOperations.copy_file(source_path, target_path):
                        self.sync_stats['files_synced'] += 1
                        self.logger.info(f"Successfully copied {rel_path} to {target_path}")
            else:
                self.logger.info(f"Target file won conflict for {rel_path}, synchronizing all copies")
                self.logger.info(f"Copying winning version back to source: {source_path}")
                FileOperations.copy_file(winner, source_path)
                
                for target_path in target_paths:
                    if target_path != winner:
                        self.logger.info(f"Copying winning version to target: {target_path}")
                        if FileOperations.copy_file(winner, target_path):
                            self.sync_stats['files_synced'] += 1
                            self.logger.info(f"Successfully copied {rel_path} to {target_path}")
        
        else:
            self.logger.info(f"No existing copies found for {rel_path}, performing fresh copy")
            for target_path in target_paths:
                self.logger.info(f"Copying {rel_path} to new target: {target_path}")
                if FileOperations.copy_file(source_path, target_path):
                    self.sync_stats['files_synced'] += 1
                    self.logger.info(f"Successfully created new copy at {target_path}")

    def _handle_file_deletion(self, target_paths: List[str], rel_path: str) -> None:
        """
        Handles deleting files from target directories
        """
        self.logger.info(f"Processing deletion of {rel_path} from {len(target_paths)} targets")
        for target_path in target_paths:
            self.logger.info(f"Attempting to delete {rel_path} from {target_path}")
            if FileOperations.delete_file(target_path):
                self.sync_stats['files_synced'] += 1
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
