# File Inventory Application

## Recent Updates

- **NFIv2N Branch development based on V0.2**
  - Broken Summary Statistics function
  - various bugs, work in progress

- **Version 0.2**:
  - Added a feature to display the "most recent scan" in a human-readable, relative format (e.g., "5 minutes ago", "2 days ago").

## Version

This is version 0.2 of the File Inventory Application.

## Overview

The **File Inventory Application** is a Python-based tool designed to scan directories, extract metadata about files, and display useful insights in a visually appealing terminal interface. The app features:

- **File Metadata Extraction**: Collects details such as file name, size, extension, and last modified date.
- **Interactive Menus**: Allows users to navigate through options like summary statistics, file searches, and grouping by directory.
- **Dynamic Dashboard**: Displays total files, total size, size by drive, most recent file, and last scan timestamp.
- **Dynamic Theming**: Supports customizable color palettes via a JSON configuration file for a flexible and user-defined UI.

## Features

- **Scan Directories**: Traverse directories and extract metadata for all files.
- **Display Inventory**: View file statistics, search files, filter by extension, and more.
- **Persistent Data**: Saves inventory data to a JSON file for future use.
- **Last Scan Tracking**: Records and displays the timestamp of the most recent scan.
- **Customizable Colors**: Modify the UI theme by editing the `colors.json` file.

## Requirements

- **Python 3.7 or higher**
- **Required Libraries**:
  - `tqdm`: For progress bars during file scanning.
  - `colorama`: For terminal color enhancements.

## Installation

1. Clone or download this repository to your local machine.
2. Install the required Python libraries:

   ```bash
   pip install tqdm colorama
   ```

3. Ensure you have the necessary permissions to access the directories you want to scan.

## Usage

1. Run the application:

   ```bash
   python extract_metadata.py
   ```

2. Follow the interactive menus to:
   - Scan directories and update the inventory.
   - View file inventory statistics and details.
   - Search, filter, or group files.
   - Customize the UI theme by editing the `colors.json` file.
3. Exit the application by selecting the `x` option in any menu.

## Assumptions

- The application dynamically determines the default source folder based on the current user's home directory. For example, it defaults to `~/OneDrive/Documents` on systems where OneDrive is configured.
- The application assumes the user has access to the directories they want to scan.
- The application is designed for Windows but can be adapted for other operating systems.

## File Structure

- `extract_metadata.py`: Main application script.
- `file_inventory.json`: Stores the scanned file inventory data.
- `last_scan.json`: Tracks the timestamp of the most recent scan.
- `colors.json`: Defines the color palette for the application's UI.

## License

This project is licensed under the MIT License. Feel free to use and modify it as needed.

## Acknowledgments

- **Colorama**: For terminal color enhancements.
- **TQDM**: For progress bar functionality.

---

*Hope you enjoy using the File Inventory Application!*
*"Ever wondered where all your disk space went? Meet the File Inventory Application – your friendly neighborhood file detective! It scans, sorts, and spills the beans on your files, all while looking sharp with customizable colors. Think of it as Marie Kondo for your hard drive – if Marie Kondo loved JSON and progress bars. 🎉"*
