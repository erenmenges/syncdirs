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
            raise ValueError(f"Source directory does not exist: {source_dir}")
        
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
            filename='sync_manager.log',    # Log file name
            level=logging.INFO,             # Log level
            format='%(asctime)s - %(levelname)s - %(message)s'  # Log message format
        )

    def sync_files(self, changes: Dict[str, str]) -> None:
        """
        Main method that processes file changes and syncs them to target directories
        """
        # Record start time and log beginning of sync
        self.sync_stats['start_time'] = datetime.now()
        self.logger.info(f"Starting sync operation with {len(changes)} changes")

        # Process each changed file
        for rel_path, change_type in changes.items():
            # Convert relative path to full path in source directory
            source_path = os.path.join(self.source_dir, rel_path)
            
            # Generate full paths for this file in all target directories
            target_paths = [os.path.join(target_dir, rel_path) 
                          for target_dir in self.target_dirs]
            
            try:
                # Handle file updates (modified or created files)
                if change_type in ('modified', 'created'):
                    self._handle_file_update(source_path, target_paths, rel_path)
                # Handle file deletions
                elif change_type == 'deleted':
                    self._handle_file_deletion(target_paths, rel_path)
                    
            except Exception as e:
                # Track and log any failures
                self.sync_stats['failed_operations'] += 1
                self.logger.error(f"Error syncing {rel_path}: {str(e)}")

        # Record end time and log completion
        self.sync_stats['end_time'] = datetime.now()
        self.logger.info("Sync operation completed")

    def _handle_file_update(self, source_path: str, target_paths: List[str], 
                          rel_path: str) -> None:
        """
        Handles updating or creating files, including conflict resolution
        """
        # Find which target paths already have this file
        existing_targets = [path for path in target_paths if os.path.exists(path)]
        
        # If file exists in any targets, need to check for conflicts
        if existing_targets:
            # Combine source and existing target files for conflict resolution
            conflicting_files = [source_path] + existing_targets
            winner, losers = self.conflict_resolver.resolve_conflict(conflicting_files)
            
            self.sync_stats['conflicts_resolved'] += 1
            
            # If source file won the conflict
            if winner == source_path:
                # Copy source to all targets
                for target_path in target_paths:
                    if FileOperations.copy_file(source_path, target_path):
                        self.sync_stats['files_synced'] += 1
            # If a target file won the conflict
            else:
                # Copy winning target back to source
                FileOperations.copy_file(winner, source_path)
                # Copy winning target to other targets (except itself)
                for target_path in target_paths:
                    if target_path != winner:
                        if FileOperations.copy_file(winner, target_path):
                            self.sync_stats['files_synced'] += 1
        
        # No existing targets, simply copy source to all targets
        else:
            for target_path in target_paths:
                if FileOperations.copy_file(source_path, target_path):
                    self.sync_stats['files_synced'] += 1

    def _handle_file_deletion(self, target_paths: List[str], rel_path: str) -> None:
        """
        Handles deleting files from target directories
        """
        # Delete file from each target directory
        for target_path in target_paths:
            if FileOperations.delete_file(target_path):
                self.sync_stats['files_synced'] += 1
                self.logger.info(f"Deleted {rel_path} from {target_path}")

    def generate_summary_report(self) -> Dict:
        """
        Creates a report of what happened during the sync
        """
        # Calculate total duration if start and end times exist
        duration = None
        if self.sync_stats['start_time'] and self.sync_stats['end_time']:
            duration = (self.sync_stats['end_time'] - 
                       self.sync_stats['start_time']).total_seconds()

        # Compile all statistics into a report dictionary
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

        # Log each statistic
        self.logger.info("Sync Summary:")
        for key, value in report.items():
            self.logger.info(f"{key}: {value}")

        return report
