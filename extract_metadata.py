import os
import json
from pathlib import Path
import datetime
from tqdm import tqdm  # For progress bar
from colorama import Fore, Back, Style
import socket

# Add a function to load colors from a JSON configuration file
def load_colors(config_file="colors.json"):
    """Loads color settings from a JSON configuration file."""
    try:
        with open(config_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Warning: Color configuration file not found. Using default colors.")
        return {
            "header_bg": "WHITE",
            "header_fg": "BLUE",
            "text_fg": "RED",
            "highlight_fg": "CYAN"
        }
    except json.JSONDecodeError:
        print("Warning: Could not decode JSON. Using default colors.")
        return {
            "header_bg": "WHITE",
            "header_fg": "BLUE",
            "text_fg": "RED",
            "highlight_fg": "CYAN"
        }

# Load colors dynamically
COLORS = load_colors()

# Replace hardcoded colorama attributes with dynamic ones
header_bg = getattr(Back, COLORS["header_bg"], Back.WHITE)
header_fg = getattr(Fore, COLORS["header_fg"], Fore.BLUE)
text_fg = getattr(Fore, COLORS["text_fg"], Fore.RED)
highlight_fg = getattr(Fore, COLORS["highlight_fg"], Fore.CYAN)

def human_readable_size(size_bytes):
    """Converts bytes to a human-readable format."""
    if size_bytes == 0:
        return "0B"
    size_units = ["B", "KB", "MB", "GB", "TB"]
    i = int((len(str(size_bytes)) - 1) / 3)
    p = 1024 ** i
    s = round(size_bytes / p, 2)
    return f"{s} {size_units[i]}"

def extract_metadata(file_path, hostname):
    """Extracts basic metadata for a given file, including hostname."""
    try:
        file_name = os.path.basename(file_path)
        file_extension = os.path.splitext(file_name)[1]  # Get only the extension
        file_size_bytes = os.path.getsize(file_path)
        modified_timestamp = os.path.getmtime(file_path)  # Returns a Unix timestamp
        modified_date = datetime.datetime.fromtimestamp(modified_timestamp).isoformat()
        return {
            "file_name": file_name,
            "file_extension": file_extension,
            "file_size_bytes": file_size_bytes,
            "last_modified_timestamp": modified_timestamp,
            "last_modified_iso": modified_date,
            "full_path": file_path,
            "hostname": hostname
        }
    except Exception as e:
        print(f"Error extracting metadata for {file_path}: {e}")
        return None

def identify_potential_groups(metadata, source_folder):
    """Identifies potential application groupings based on file path."""
    for item in metadata:
        if item:
            relative_path = os.path.relpath(item["full_path"], source_folder)
            path_parts = relative_path.split(os.sep)
            item["potential_application_group"] = None  # Initialize

            # Example patterns - feel free to add more based on your NAS structure
            if "app" in [part.lower() for part in path_parts]:
                item["potential_application_group"] = "potential_application"
            elif "program files" in [part.lower() for part in path_parts]:
                item["potential_application_group"] = "potential_application"
            elif len(path_parts) > 1 and path_parts[-2].lower() in ["config", "configuration", "settings"]:
                item["potential_application_group"] = "potential_config"
            elif item["file_extension"].lower() in [".exe", ".app"] and len(path_parts) > 1:
                item["potential_application_group"] = f"potential_app_{path_parts[-2].lower()}"
            elif len(path_parts) > 1 and any(keyword in path_parts[-2].lower() for keyword in ["bundle", "package"]):
                item["potential_application_group"] = "potential_bundle"

def update_last_scan():
    """Updates the last scan timestamp in a JSON file."""
    scan_file = "last_scan.json"
    try:
        with open(scan_file, "w") as f:
            json.dump({"last_scan": datetime.datetime.now().isoformat()}, f, indent=4)
    except Exception as e:
        print(text_fg + f"Error updating last scan timestamp: {e}" + Style.RESET_ALL)

# Modify traverse_and_extract to handle errors silently and log them to a JSON file
def traverse_and_extract(root_dir, hostname):
    """Traverses the directory and extracts metadata for each file, including hostname."""
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

    # Save errors to a JSON file
    if error_log:
        error_log_file = "error_log.json"
        with open(error_log_file, "w") as f:
            json.dump(error_log, f, indent=4)
        print(text_fg + f"✔ Encountered {len(error_log)} errors. Details saved to: {error_log_file}" + Style.RESET_ALL)

    return inventory, total_size

def discover_drives():
    """Discovers available drives on Windows."""
    if os.name == 'nt':  # Windows-specific
        import string
        drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
        return drives
    else:
        # For non-Windows systems, return root as a default
        return ["/"]

def load_existing_inventory(output_file):
    """Loads existing inventory from the JSON file, if it exists."""
    if os.path.exists(output_file):
        try:
            with open(output_file, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Could not decode JSON from {output_file}. Starting with an empty inventory.")
            return []
    return []

def merge_inventories(existing_inventory, new_inventory):
    """Merges new inventory data into the existing inventory."""
    inventory_dict = {item["full_path"]: item for item in existing_inventory}  # Use file paths as keys

    for new_item in new_inventory:
        if new_item["full_path"] in inventory_dict:
            # Update existing entry
            inventory_dict[new_item["full_path"]].update(new_item)
        else:
            # Add new entry
            inventory_dict[new_item["full_path"]] = new_item

    return list(inventory_dict.values())

def paginate_output(lines, page_size=10):
    """Displays output in pages with single-key navigation options."""
    total_pages = (len(lines) + page_size - 1) // page_size  # Calculate total pages
    current_page = 0

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')  # Clear screen for each page
        start = current_page * page_size
        end = start + page_size
        print("\n".join(lines[start:end]))
        print(f"\nPage {current_page + 1} of {total_pages}")

        # Navigation options
        print("\nPress 'd' for next, 'a' for previous, 'x' to exit.")

        choice = input().strip().lower()

        if choice == "a" and current_page > 0:
            current_page -= 1
        elif choice == "d" and current_page < total_pages - 1:
            current_page += 1
        elif choice == "x":
            break
        else:
            print("Invalid choice. Please try again.")

# Update print_header function to use dynamic colors
def print_header(title, inventory=None):
    """Prints a formatted header with optional inventory data."""
    os.system('cls' if os.name == 'nt' else 'clear')  # Clear screen
    print(header_bg + header_fg + "=" * 50)
    print(f"{title.center(50)}")
    print("=" * 50 + Style.RESET_ALL)

    if inventory:
        total_files = len(inventory)
        total_size = sum(item["file_size_bytes"] for item in inventory)
        print(text_fg + f"Total files: {total_files}")
        print(text_fg + f"Total size: {human_readable_size(total_size)}" + Style.RESET_ALL)
        print(header_bg + header_fg + "=" * 50 + Style.RESET_ALL)

def format_relative_time(last_scan_iso):
    """Formats the last scan timestamp into a human-readable, relative time."""
    try:
        last_scan_time = datetime.datetime.fromisoformat(last_scan_iso)
        now = datetime.datetime.now()
        delta = now - last_scan_time

        if delta.total_seconds() < 60:
            return "just now"
        elif delta.total_seconds() < 3600:
            minutes = int(delta.total_seconds() // 60)
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        elif delta.total_seconds() < 86400:
            hours = int(delta.total_seconds() // 3600)
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        else:
            days = int(delta.total_seconds() // 86400)
            return f"{days} day{'s' if days > 1 else ''} ago"
    except Exception as e:
        return "unknown time"

# Update the print_footer_with_scan function to use the new relative time formatter
def print_footer_with_scan():
    """Prints a footer with the last scan timestamp and a custom message."""
    scan_file = "last_scan.json"
    last_scan = "No scan data available."
    try:
        if os.path.exists(scan_file):
            with open(scan_file, "r") as f:
                last_scan = json.load(f).get("last_scan", last_scan)
                relative_time = format_relative_time(last_scan)
                last_scan = f"Last scan: {relative_time}"
    except Exception as e:
        last_scan = f"Error reading scan data: {e}"

    print(header_bg + header_fg + "\n" + "=" * 50)
    print(highlight_fg + f"{last_scan}".center(50))
    print(text_fg + "Hope you like my work!".center(50) + Style.RESET_ALL)
    print(header_bg + header_fg + "=" * 50 + Style.RESET_ALL)

# Update display_summary_statistics to include recent hosts and dynamic details
def display_summary_statistics(inventory):
    """Displays summary statistics of the file inventory."""
    if not inventory:
        print(text_fg + "No data available in the inventory." + Style.RESET_ALL)
        return

    total_files = len(inventory)
    total_size = sum(item["file_size_bytes"] for item in inventory)
    extensions = {}
    hostnames = {}

    for item in inventory:
        ext = item["file_extension"].lower()
        extensions[ext] = extensions.get(ext, 0) + 1

        hostname = item.get("hostname", "Unknown Host")
        hostnames[hostname] = hostnames.get(hostname, 0) + 1

    # Sort extensions and hostnames by count, descending
    sorted_extensions = sorted(extensions.items(), key=lambda x: x[1], reverse=True)
    sorted_hostnames = sorted(hostnames.items(), key=lambda x: x[1], reverse=True)

    # Display header
    print(header_fg + "Summary Statistics".center(50, "=") + Style.RESET_ALL)

    # Display total files and size
    print(highlight_fg + f"Total Files: {total_files}".ljust(30) + f"Total Size: {human_readable_size(total_size)}" + Style.RESET_ALL)

    # Display top 5 extensions
    print(header_fg + "Top File Extensions:" + Style.RESET_ALL)
    for ext, count in sorted_extensions[:5]:
        print(text_fg + f"  {ext}: {count} file(s)" + Style.RESET_ALL)

    # Display recent hostnames
    print(header_fg + "Recent Hosts Scanned:" + Style.RESET_ALL)
    for hostname, count in sorted_hostnames[:5]:
        print(text_fg + f"  {hostname}: {count} file(s)" + Style.RESET_ALL)

    # Footer
    print(header_fg + "=" * 50 + Style.RESET_ALL)

def search_files_by_name(inventory, search_term):
    """Searches for files by name or partial name."""
    results = [item for item in inventory if search_term.lower() in item["file_name"].lower()]
    if results:
        lines = [highlight_fg + f"Found {len(results)} file(s) matching '{search_term}':" + Style.RESET_ALL]
        lines.extend([text_fg + f"  {item['file_name']} ({human_readable_size(item['file_size_bytes'])}) - {item['full_path']}" + Style.RESET_ALL for item in results])
        paginate_output(lines)
    else:
        print(text_fg + f"No files found matching '{search_term}'." + Style.RESET_ALL)

def filter_files_by_extension(inventory, extension):
    """Filters files by their extension."""
    results = [item for item in inventory if item["file_extension"].lower() == extension.lower()]
    if results:
        lines = [highlight_fg + f"Found {len(results)} file(s) with extension '{extension}':" + Style.RESET_ALL]
        lines.extend([text_fg + f"  {item['file_name']} ({human_readable_size(item['file_size_bytes'])}) - {item['full_path']}" + Style.RESET_ALL for item in results])
        paginate_output(lines)
    else:
        print(text_fg + f"No files found with extension '{extension}'." + Style.RESET_ALL)

def display_largest_files(inventory, top_n=10):
    """Displays the largest files in the inventory."""
    sorted_files = sorted(inventory, key=lambda x: x["file_size_bytes"], reverse=True)
    lines = [highlight_fg + f"Top {top_n} largest files:" + Style.RESET_ALL]
    lines.extend([text_fg + f"  {item['file_name']} ({human_readable_size(item['file_size_bytes'])}) - {item['full_path']}" + Style.RESET_ALL for item in sorted_files[:top_n]])
    paginate_output(lines)

def group_files_by_directory(inventory):
    """Groups files by their parent directory."""
    directory_groups = {}
    for item in inventory:
        directory = os.path.dirname(item["full_path"])
        if directory not in directory_groups:
            directory_groups[directory] = {"count": 0, "size": 0}
        directory_groups[directory]["count"] += 1
        directory_groups[directory]["size"] += item["file_size_bytes"]

    lines = [highlight_fg + "Files grouped by directory:" + Style.RESET_ALL]
    lines.extend([text_fg + f"  {directory}: {stats['count']} file(s), {human_readable_size(stats['size'])}" + Style.RESET_ALL for directory, stats in directory_groups.items()])
    paginate_output(lines)

def group_files_by_hostname_and_drive(inventory):
    """Groups files by hostname and drive."""
    grouped_data = {}

    for item in inventory:
        # Extract hostname and drive from the file path
        full_path = item.get("full_path", "")
        if os.name == 'nt':
            drive, _ = os.path.splitdrive(full_path)
        else:
            drive = "/"  # For non-Windows systems, use root as the drive

        hostname = os.uname().nodename if hasattr(os, 'uname') else "Unknown Host"

        # Initialize nested dictionary structure
        if hostname not in grouped_data:
            grouped_data[hostname] = {}
        if drive not in grouped_data[hostname]:
            grouped_data[hostname][drive] = {"count": 0, "size": 0}

        # Update counts and sizes
        grouped_data[hostname][drive]["count"] += 1
        grouped_data[hostname][drive]["size"] += item.get("file_size_bytes", 0)

    return grouped_data

def display_grouped_by_hostname_and_drive(inventory):
    """Displays files grouped by hostname and drive."""
    grouped_data = group_files_by_hostname_and_drive(inventory)

    lines = [highlight_fg + "Files grouped by hostname and drive:" + Style.RESET_ALL]
    for hostname, drives in grouped_data.items():
        lines.append(header_fg + f"Hostname: {hostname}" + Style.RESET_ALL)
        for drive, stats in drives.items():
            lines.append(text_fg + f"  Drive: {drive} - {stats['count']} file(s), {human_readable_size(stats['size'])}" + Style.RESET_ALL)

    paginate_output(lines)

def scan_remote_share(remote_path):
    """Scans a remote network share for files."""
    if not os.path.exists(remote_path):
        print(text_fg + f"The remote path {remote_path} is not accessible." + Style.RESET_ALL)
        return

    hostname = os.uname().nodename if hasattr(os, 'uname') else "Unknown Host"
    print_header(f"Scanning remote share: {remote_path}")
    existing_inventory = load_existing_inventory(output_file)
    new_inventory, total_size = traverse_and_extract(remote_path, hostname)
    updated_inventory = merge_inventories(existing_inventory, new_inventory)

    with open(output_file, "w") as f:
        json.dump(updated_inventory, f, indent=4)

    print(text_fg + f"✔ Metadata extracted and saved to: {output_file}" + Style.RESET_ALL)
    print(text_fg + f"✔ Total data size: {human_readable_size(total_size)}" + Style.RESET_ALL)
    update_last_scan()

def has_inventory_changed(output_file, last_modified_time):
    """Checks if the inventory file has been modified since the last check."""
    try:
        current_modified_time = os.path.getmtime(output_file)
        return current_modified_time > last_modified_time, current_modified_time
    except FileNotFoundError:
        return False, last_modified_time

def get_local_hostname():
    """Gets the local hostname."""
    try:
        return socket.gethostname()
    except Exception as e:
        return f"Unknown Host ({e})"

def get_network_hostname():
    """Attempts to determine the network hostname."""
    try:
        return socket.getfqdn()
    except Exception:
        return get_local_hostname()

# Update the start_scan function to capture both local and network hostnames
def start_scan(folder):
    """Starts the scanning process for a given folder."""
    print_header(f"Scanning: {folder}")
    local_hostname = get_local_hostname()
    network_hostname = get_network_hostname()
    hostname = f"{local_hostname} ({network_hostname})"

    existing_inventory = load_existing_inventory(output_file)
    new_inventory, total_size = traverse_and_extract(folder, hostname)
    updated_inventory = merge_inventories(existing_inventory, new_inventory)

    with open(output_file, "w") as f:
        json.dump(updated_inventory, f, indent=4)

    print(text_fg + f"✔ Metadata extracted and saved to: {output_file}" + Style.RESET_ALL)
    print(text_fg + f"✔ Total data size: {human_readable_size(total_size)}" + Style.RESET_ALL)
    update_last_scan()

# Update the remove_drive_from_inventory function to allow host-level removal
def remove_drive_or_host_from_inventory():
    """Removes a drive or an entire host's entries from the inventory."""
    global existing_inventory

    # Display available hosts and drives in the inventory
    hosts = set(item["hostname"] for item in existing_inventory if "hostname" in item)
    drives = set(os.path.splitdrive(item["full_path"])[0] for item in existing_inventory if os.name == 'nt')

    print(header_fg + "Available Hosts:" + Style.RESET_ALL)
    hosts_list = list(hosts)
    for i, host in enumerate(hosts_list, start=1):
        print(text_fg + f"  {i}. {host}" + Style.RESET_ALL)

    print(header_fg + "Available Drives:" + Style.RESET_ALL)
    drives_list = list(drives)
    for i, drive in enumerate(drives_list, start=1):
        print(text_fg + f"  {i + len(hosts_list)}. {drive}" + Style.RESET_ALL)

    # Prompt user to select a host or drive to remove
    choice = input(highlight_fg + "Enter the number of the host or drive to remove: " + Style.RESET_ALL).strip()
    if choice.isdigit():
        choice = int(choice)
        if 1 <= choice <= len(hosts_list):
            selected_host = hosts_list[choice - 1]
            existing_inventory = [item for item in existing_inventory if item["hostname"] != selected_host]
            print(text_fg + f"✔ Host {selected_host} and its files have been removed from the inventory." + Style.RESET_ALL)
        elif len(hosts_list) < choice <= len(hosts_list) + len(drives_list):
            selected_drive = drives_list[choice - len(hosts_list) - 1]
            existing_inventory = [item for item in existing_inventory if not item["full_path"].startswith(selected_drive)]
            print(text_fg + f"✔ Drive {selected_drive} and its files have been removed from the inventory." + Style.RESET_ALL)
        else:
            print(text_fg + "Invalid selection. Please try again." + Style.RESET_ALL)
    else:
        print(text_fg + "Invalid input. Please enter a number." + Style.RESET_ALL)

    # Save updated inventory
    with open(output_file, "w") as f:
        json.dump(existing_inventory, f, indent=4)

def display_main_menu():
    """Displays the main menu with breadcrumb navigation and inventory status."""
    global existing_inventory
    last_modified_time = os.path.getmtime(output_file) if os.path.exists(output_file) else 0

    while True:
        inventory_changed, last_modified_time = has_inventory_changed(output_file, last_modified_time)
        if inventory_changed:
            existing_inventory = load_existing_inventory(output_file)

        # Calculate inventory stats
        total_files = len(existing_inventory)
        total_size = sum(item["file_size_bytes"] for item in existing_inventory)
        unique_drives = set(os.path.splitdrive(item["full_path"])[0] for item in existing_inventory if os.name == 'nt')
        unique_hostnames = set(item["hostname"] for item in existing_inventory if "hostname" in item)

        # Format inventory status
        inventory_status = (
            f"Inventory: {'Empty' if total_files == 0 else f'{total_files} files, {human_readable_size(total_size)}'}\n"
            f"Drives: {len(unique_drives)}\n"
            f"Hostnames: {len(unique_hostnames)}\n"
        )

        # Get last scan info
        scan_file = "last_scan.json"
        last_scan = "No scan data available."
        try:
            if os.path.exists(scan_file):
                with open(scan_file, "r") as f:
                    last_scan = json.load(f).get("last_scan", last_scan)
                    relative_time = format_relative_time(last_scan)
                    last_scan = f"Last scan: {relative_time}"
        except Exception as e:
            last_scan = f"Error reading scan data: {e}"

        # Display header with inventory status
        print_header("Main Menu")
        print(text_fg + inventory_status + Style.RESET_ALL)
        print(highlight_fg + last_scan + Style.RESET_ALL)

        # Display menu options
        print(header_fg + "┌───────────────────────────────┐")
        print(text_fg + "│ 1. Scan for new files         │")
        print(text_fg + "│ 2. View inventory             │")
        print(text_fg + "│ 3. Manage inventory           │")
        print(text_fg + "│ x. Exit                       │")
        print(header_fg + "└───────────────────────────────┘" + Style.RESET_ALL)

        choice = input(highlight_fg + "Enter your choice: " + Style.RESET_ALL).strip().lower()

        if choice == "1":
            scan_menu()
        elif choice == "2":
            inventory_menu()
        elif choice == "3":
            inventory_management_menu()
        elif choice == "x":
            clear_screen()
            print(highlight_fg + "Thanks for using the app!" + Style.RESET_ALL)
            break
        else:
            print(text_fg + "Invalid choice. Please try again." + Style.RESET_ALL)

def scan_menu():
    """Displays the scan menu with inventory information and drive/host discovery."""
    global existing_inventory
    last_modified_time = os.path.getmtime(output_file) if os.path.exists(output_file) else 0

    while True:
        inventory_changed, last_modified_time = has_inventory_changed(output_file, last_modified_time)
        if inventory_changed:
            existing_inventory = load_existing_inventory(output_file)

        # Calculate inventory stats
        total_files = len(existing_inventory)
        total_size = sum(item["file_size_bytes"] for item in existing_inventory)
        unique_drives = set(os.path.splitdrive(item["full_path"])[0] for item in existing_inventory if os.name == 'nt')
        unique_hostnames = set(item["hostname"] for item in existing_inventory if "hostname" in item)

        # Format inventory status
        inventory_status = (
            f"Inventory: {'Empty' if total_files == 0 else f'{total_files} files, {human_readable_size(total_size)}'}\n"
            f"Drives: {len(unique_drives)}\n"
            f"Hostnames: {len(unique_hostnames)}\n"
        )

        print_header("Main Menu > Scan Menu")
        print(text_fg + inventory_status + Style.RESET_ALL)

        print(header_fg + "┌───────────────────────────────┐")
        print(text_fg + "│ 1. Scan default folder        │")
        print(text_fg + "│ 2. Scan custom folder         │")
        print(text_fg + "│ 3. Discover drives/hosts      │")
        print(text_fg + "│ x. Back to Main Menu          │")
        print(header_fg + "└───────────────────────────────┘" + Style.RESET_ALL)

        choice = input(highlight_fg + "Enter your choice: " + Style.RESET_ALL).strip().lower()

        if choice == "1":
            default_folder = Path.home() / "OneDrive" / "Documents"
            start_scan(str(default_folder))
        elif choice == "2":
            custom_folder = input(highlight_fg + "Enter the folder path to scan: " + Style.RESET_ALL).strip()
            if os.path.isdir(custom_folder):
                start_scan(custom_folder)
            else:
                print(text_fg + "Invalid folder path. Please try again." + Style.RESET_ALL)
        elif choice == "3":
            discover_targets_menu()
        elif choice == "x":
            break
        else:
            print(text_fg + "Invalid choice. Please try again." + Style.RESET_ALL)

def discover_targets_menu():
    """Displays a menu for discovering drives and network hosts."""
    while True:
        print_header("Main Menu > Scan Menu > Discover Targets")

        # Discover drives
        drives = discover_drives()
        print(header_fg + "Available Drives:" + Style.RESET_ALL)
        for i, drive in enumerate(drives, start=1):
            print(text_fg + f"  {i}. {drive}" + Style.RESET_ALL)

        # Placeholder for network hosts discovery (can be expanded later)
        print(header_fg + "Available Network Hosts:" + Style.RESET_ALL)
        print(text_fg + "  (Feature not yet implemented)" + Style.RESET_ALL)

        print(header_fg + "┌───────────────────────────────┐")
        print(text_fg + "│ Enter a number to scan target │")
        print(text_fg + "│ x. Back to Scan Menu          │")
        print(header_fg + "└───────────────────────────────┘" + Style.RESET_ALL)

        choice = input(highlight_fg + "Enter your choice: " + Style.RESET_ALL).strip().lower()

        if choice.isdigit() and 1 <= int(choice) <= len(drives):
            selected_drive = drives[int(choice) - 1]
            start_scan(selected_drive)
        elif choice == "x":
            break
        else:
            print(text_fg + "Invalid choice. Please try again." + Style.RESET_ALL)

def inventory_menu():
    """Displays the inventory menu with breadcrumb navigation."""
    global existing_inventory
    last_modified_time = os.path.getmtime(output_file) if os.path.exists(output_file) else 0

    while True:
        inventory_changed, last_modified_time = has_inventory_changed(output_file, last_modified_time)
        if inventory_changed:
            existing_inventory = load_existing_inventory(output_file)

        print_header("Main Menu > Inventory Menu")
        print(header_fg + "┌───────────────────────────────┐")
        print(text_fg + "│ 1. Summary statistics         │")
        print(text_fg + "│ 2. Search files by name       │")
        print(text_fg + "│ 3. Filter files by extension  │")
        print(text_fg + "│ 4. Display largest files      │")
        print(text_fg + "│ 5. Group files by directory   │")
        print(text_fg + "│ 6. Group files by hostname and drive │")
        print(text_fg + "│ x. Back to Main Menu          │")
        print(header_fg + "└───────────────────────────────┘" + Style.RESET_ALL)

        choice = input(highlight_fg + "Enter your choice: " + Style.RESET_ALL).strip().lower()

        if choice == "1":
            display_summary_statistics(existing_inventory)
        elif choice == "2":
            search_term = input(highlight_fg + "Enter the file name or partial name to search: " + Style.RESET_ALL).strip()
            search_files_by_name(existing_inventory, search_term)
        elif choice == "3":
            extension = input(highlight_fg + "Enter the file extension to filter by (e.g., .txt): " + Style.RESET_ALL).strip()
            filter_files_by_extension(existing_inventory, extension)
        elif choice == "4":
            top_n = int(input(highlight_fg + "Enter the number of largest files to display: " + Style.RESET_ALL).strip())
            display_largest_files(existing_inventory, top_n)
        elif choice == "5":
            group_files_by_directory(existing_inventory)
        elif choice == "6":
            display_grouped_by_hostname_and_drive(existing_inventory)
        elif choice == "x":
            break
        else:
            print(text_fg + "Invalid choice. Please try again." + Style.RESET_ALL)

def inventory_management_menu():
    """Displays the inventory management menu with breadcrumb navigation."""
    global existing_inventory
    last_modified_time = os.path.getmtime(output_file) if os.path.exists(output_file) else 0

    while True:
        inventory_changed, last_modified_time = has_inventory_changed(output_file, last_modified_time)
        if inventory_changed:
            existing_inventory = load_existing_inventory(output_file)

        print_header("Main Menu > Inventory Management Menu")
        print(header_fg + "┌───────────────────────────────┐")
        print(text_fg + "│ 1. Remove a drive or host     │")
        print(text_fg + "│ 2. Reload inventory           │")
        print(text_fg + "│ x. Back to Main Menu          │")
        print(header_fg + "└───────────────────────────────┘" + Style.RESET_ALL)

        choice = input(highlight_fg + "Enter your choice: " + Style.RESET_ALL).strip().lower()

        if choice == "1":
            remove_drive_or_host_from_inventory()
        elif choice == "2":
            reload_inventory()
        elif choice == "x":
            break
        else:
            print(text_fg + "Invalid choice. Please try again." + Style.RESET_ALL)

def reload_inventory():
    """Reloads the inventory from the JSON file."""
    global existing_inventory

    try:
        existing_inventory = load_existing_inventory(output_file)
        print(text_fg + "✔ Inventory successfully reloaded." + Style.RESET_ALL)
    except Exception as e:
        print(text_fg + f"Error reloading inventory: {e}" + Style.RESET_ALL)

def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

if __name__ == "__main__":
    output_file = "file_inventory.json"

    # Clear the terminal screen
    clear_screen()

    # Load existing inventory
    existing_inventory = load_existing_inventory(output_file)

    # Display main menu
    display_main_menu()

