# This is version Point2N Branch, developed by arrfour

import os
import json
import string
from tqdm import tqdm
from pathlib import Path
from utils import human_readable_size, print_header
import datetime
import socket

def extract_metadata(file_path, hostname):
    """Extracts basic metadata for a given file, including hostname."""
    try:
        file_name = os.path.basename(file_path)
        file_extension = os.path.splitext(file_name)[1]
        file_size_bytes = os.path.getsize(file_path)
        modified_timestamp = os.path.getmtime(file_path)
        modified_date = datetime.datetime.fromtimestamp(modified_timestamp).isoformat()

        # Determine hostname for the file
        if file_path.startswith("\\") or ":\\" in file_path:
            # Network path or drive letter
            target_hostname = file_path.split("\\")[2] if file_path.startswith("\\") else socket.gethostname()
        else:
            # Local path
            target_hostname = socket.gethostname()

        return {
            "file_name": file_name,
            "file_extension": file_extension,
            "file_size_bytes": file_size_bytes,
            "last_modified_timestamp": modified_timestamp,
            "last_modified_iso": modified_date,
            "full_path": file_path,
            "hostname": target_hostname
        }
    except Exception as e:
        return None

def traverse_and_extract(root_dir, hostname):
    """Traverses the directory and extracts metadata for each file."""
    inventory = []
    total_size = 0
    error_log = []
    all_files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(root_dir) for f in filenames]

    for file_path in tqdm(all_files, desc="Processing files", unit="file"):
        try:
            metadata = extract_metadata(file_path, hostname)
            if metadata:
                inventory.append(metadata)
                total_size += metadata["file_size_bytes"]
        except Exception as e:
            error_log.append({"file_path": file_path, "error": str(e)})

    if error_log:
        with open("error_log.json", "w") as f:
            json.dump(error_log, f, indent=4)

    return inventory, total_size

def start_scan(folder, inventory_manager):
    """Starts the scanning process for a given folder."""
    print_header(f"Scanning: {folder}")

    # Determine hostname based on the operating system
    if os.name == 'nt':  # Windows
        hostname = os.getenv('COMPUTERNAME', 'Unknown Host')
    elif os.name == 'posix':  # Linux or macOS
        try:
            hostname = socket.gethostname()
        except Exception as e:
            hostname = "Unknown Host"
    else:
        hostname = "Unknown Host"

    # Debug log: Hostname detection
    print(f"DEBUG: Detected hostname: {hostname}")

    # Debug log: Start scanning
    print(f"DEBUG: Starting scan for folder: {folder}")

    new_inventory, total_size = traverse_and_extract(folder, hostname)

    # Debug log: Scan results
    print(f"DEBUG: Scan completed. Files found: {len(new_inventory)}, Total size: {total_size}")

    if new_inventory:
        inventory_manager.merge_inventory(new_inventory)

        # Debug log: Inventory merged
        print(f"DEBUG: Inventory merged. Total files in inventory: {len(inventory_manager.inventory)}")

        inventory_manager.save_inventory()

        # Debug log: Inventory saved
        print(f"DEBUG: Inventory saved to {inventory_manager.output_file}")

        # Update last scan timestamp
        update_last_scan()

        print(f"✔ Metadata extracted and saved to: {inventory_manager.output_file}")
        print(f"✔ Total data size: {human_readable_size(total_size)}")
    else:
        print("No files were found during the scan.")

    # Debugging helper: Ensure `merge_inventory` is functioning correctly
    print(f"DEBUG: Final inventory size: {len(inventory_manager.inventory)}")

def update_last_scan():
    """Updates the last scan timestamp in a JSON file."""
    scan_file = "last_scan.json"
    try:
        now = datetime.datetime.now()
        with open(scan_file, "w") as f:
            json.dump({
                "last_scan_iso": now.isoformat(),
                "last_scan_human_readable": now.strftime("%Y-%m-%d %H:%M:%S")
            }, f, indent=4)
        print("DEBUG: Last scan timestamp updated.")
    except Exception as e:
        print(f"Error updating last scan timestamp: {e}")

def discover_drives():
    """Discovers available drives on the system."""
    if os.name == 'nt':  # Windows-specific
        return [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
    else:
        return ["/"]  # For non-Windows systems, return root as a default

def discover_network_hosts():
    """Placeholder for discovering network hosts."""
    # This is a placeholder implementation. Replace with actual network discovery logic.
    return ["Host1", "Host2", "Host3"]