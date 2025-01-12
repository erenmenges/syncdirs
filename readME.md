# Syncdirs

A robust, multi-threaded Python application that provides real-time, decentralized synchronization between multiple directories. The tool continuously monitors specified directories for changes and ensures they stay synchronized, without requiring a central source of truth.

## Table of Contents

- [Description](#description)
- [Key Features](#key-features)
- [Limitations](#limitations)
- [Warning](#warning)
- [Installation and Usage](#installation-and-usage)

## Description

This tool enables decentralized, bidirectional synchronization across multiple directories, automatically detecting and propagating file changes (creation, modification, and deletion) in real-time. Any directory can initiate changes, and all changes are propagated to other directories in the sync network. It features automatic conflict resolution, extensive logging capabilities, and a thread-safe architecture for reliable performance.

## Key Features

- Continuous monitoring of directory changes using efficient file system watchers
- Immediate propagation of file creations, modifications, and deletions
- Support for multiple target directories with concurrent synchronization
- Two conflict resolution modes:
  - **Manual Mode**: User-guided resolution with detailed file information
  - **Newest-Wins Mode**: Automatic resolution based on timestamp comparison
- Detailed conflict logging for audit trails
- Multi-threaded design for parallel file operations
- Thread-safe synchronization mechanisms
- File integrity verification using MD5 hashing
- Support for nested directory structures
- Command-line interface with flexible configuration options

## Limitations

- **Platform Specific**: Some file system operations may behave differently across operating systems, only tested on MacOS
- **Symbolic Links**: Limited handling of symbolic links and special file types
- **Concurrent Access**: Does not lock files during synchronization, which may lead to race conditions if files are actively being modified

## Warning

Although it is THOROUGHLY tested and IT WORKS PROPERLY, this project is a work in progress and may not be ready for production use. Test it yourself before using it. Some parts are not yet tested for a real-world scenario. Please reach out for any security concerns.

## Installation and Usage

1. Clone the repository:

```bash
git https://github.com/erenmenges/syncdirs.git
cd syncdirs
```

2. Create and activate a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate
```

3. Usage

```bash
python main.py /path/to/source /path/to/target1 /path/to/target2 /path/to/target3
```

Options
-p, --policy: Choose conflict resolution policy
    manual: Prompt for user input when conflicts occur (default)
    newest: Automatically keep the newest file
--debug: Enable detailed debug logging

Examples:

```bash
# Sync three directories with manual conflict resolution
python main.py /path/to/dir1 /path/to/dir2 /path/to/dir3

# Sync multiple directories using newest-wins policy
python main.py -p newest /path/to/source /path/to/target1 /path/to/target2

# Enable debug logging
python main.py --debug /path/to/dir1 /path/to/dir2
```
