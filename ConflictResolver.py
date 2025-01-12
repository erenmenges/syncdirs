import os
import logging
from datetime import datetime
from enum import Enum
from typing import List, Tuple

class ResolutionPolicy(Enum):
    NEWEST_WINS = "newest_file_wins"
    MANUAL = "manual"

class ConflictResolver:
    def __init__(self, resolution_policy: ResolutionPolicy = ResolutionPolicy.MANUAL):
        """Initialize ConflictResolver with a resolution policy."""
        self.resolution_policy = resolution_policy
        self.logger = logging.getLogger(__name__)
        
        # Set up logging
        logging.basicConfig(
            filename='conflict_resolution.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def resolve_conflict(self, conflicting_files: List[str]) -> Tuple[str, List[str]]:
        """
        Main method to resolve conflicts between multiple files.
        Uses automatic resolution for NEWEST_WINS policy and manual resolution for MANUAL policy.
        
        Args:
            conflicting_files: List of paths to conflicting files
            
        Returns:
            Tuple containing (winning_path, list_of_losing_paths)
        """
        if len(conflicting_files) < 2:
            raise ValueError("At least two files are required for conflict resolution")
            
        if not all(os.path.exists(path) for path in conflicting_files):
            raise FileNotFoundError("One or more files do not exist")

        if self.resolution_policy == ResolutionPolicy.NEWEST_WINS:
            winner, losers = self._resolve_by_timestamp(conflicting_files)
        elif self.resolution_policy == ResolutionPolicy.MANUAL:
            winner, losers = self._resolve_manually(conflicting_files)
        else:
            raise ValueError(f"Unknown resolution policy: {self.resolution_policy}")

        self.log_resolution(conflicting_files, winner)
        return winner, losers

    def _resolve_manually(self, conflicting_files: List[str]) -> Tuple[str, List[str]]:
        """
        Helper method to resolve conflicts manually by prompting user input.
        
        Args:
            conflicting_files: List of paths to conflicting files
            
        Returns:
            Tuple containing (chosen_path, list_of_rejected_paths)
        """
        print("\nConflict detected!")
        print("\nConflicting files:")
        
        for idx, file_path in enumerate(conflicting_files, start=1):
            print(f"\nOption {idx}:")
            print(f"Path: {file_path}")
            print(f"Last modified: {datetime.fromtimestamp(os.path.getmtime(file_path))}")
        
        while True:
            choice = input(f"\nWhich file do you want to keep? (1-{len(conflicting_files)}): ")
            try:
                choice_idx = int(choice)
                if 1 <= choice_idx <= len(conflicting_files):
                    break
                print(f"Please enter a number between 1 and {len(conflicting_files)}")
            except ValueError:
                print("Please enter a valid number")

        winner = conflicting_files[choice_idx - 1]
        losers = [f for f in conflicting_files if f != winner]
        return winner, losers

    def log_resolution(self, conflicting_files: List[str], winning_path: str) -> None:
        """
        Log details of the conflict resolution.
        
        Args:
            conflicting_files: List of paths to conflicting files
            winning_path: Path to the file that was chosen
        """
        self.logger.info("Conflict Resolution:")
        for idx, file_path in enumerate(conflicting_files, start=1):
            self.logger.info(f"File {idx}: {file_path}")
        self.logger.info(f"Winner: {winning_path}")
        self.logger.info(f"Resolution Policy: {self.resolution_policy.value}")
        self.logger.info("-" * 50)

    def _resolve_by_timestamp(self, conflicting_files: List[str]) -> Tuple[str, List[str]]:
        """
        Resolve conflict by choosing the newest file from multiple files.
        
        Args:
            conflicting_files: List of paths to conflicting files
            
        Returns:
            Tuple containing (newest_path, list_of_older_paths)
        """
        # Create list of tuples (file_path, modification_time)
        files_with_times = [(f, os.path.getmtime(f)) for f in conflicting_files]
        
        # Sort by modification time in descending order
        files_with_times.sort(key=lambda x: x[1], reverse=True)
        
        # The first file is the newest (winner)
        winner = files_with_times[0][0]
        
        # All other files are losers
        losers = [f[0] for f in files_with_times[1:]]
        
        return winner, losers
