import os
import json
from pathlib import Path
import datetime
from tqdm import tqdm  # For progress bar
from colorama import Fore, Back, Style

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

def extract_metadata(file_path):
    """Extracts basic metadata for a given file."""
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
            "full_path": file_path
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

def traverse_and_extract(root_dir):
    """Traverses the directory and extracts metadata for each file."""
    inventory = []
    total_size = 0
    all_files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(root_dir) for f in filenames]

    for file_path in tqdm(all_files, desc="Processing files", unit="file"):
        metadata = extract_metadata(file_path)
        if metadata:
            inventory.append(metadata)
            total_size += metadata["file_size_bytes"]

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

def display_summary_statistics(inventory):
    """Displays summary statistics of the file inventory."""
    if not inventory:
        print(text_fg + "No data available in the inventory." + Style.RESET_ALL)
        return

    total_files = len(inventory)
    total_size = sum(item["file_size_bytes"] for item in inventory)
    extensions = {}
    for item in inventory:
        ext = item["file_extension"].lower()
        extensions[ext] = extensions.get(ext, 0) + 1

    lines = [
        highlight_fg + f"Total files: {total_files}" + Style.RESET_ALL,
        highlight_fg + f"Total size: {human_readable_size(total_size)}" + Style.RESET_ALL,
        header_fg + "File count by extension:" + Style.RESET_ALL
    ]
    lines.extend([text_fg + f"  {ext}: {count}" + Style.RESET_ALL for ext, count in sorted(extensions.items())])

    paginate_output(lines)

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

def display_inventory_menu(inventory):
    """Interactive menu to display inventory data."""
    while True:
        # Reload inventory at the start of the menu
        inventory[:] = load_existing_inventory(output_file)

        print_header("Inventory Display Menu", inventory)
        print(header_fg + "┌───────────────────────────────┐")
        print(text_fg + "│ 1. Summary statistics         │")
        print(text_fg + "│ 2. Search files by name       │")
        print(text_fg + "│ 3. Filter files by extension  │")
        print(text_fg + "│ 4. Display largest files      │")
        print(text_fg + "│ 5. Group files by directory   │")
        print(text_fg + "│ x. Exit                       │")
        print(header_fg + "└───────────────────────────────┘" + Style.RESET_ALL)
        choice = input(highlight_fg + "Enter your choice: " + Style.RESET_ALL).strip().lower()

        if choice == "1":
            print_header("Summary Statistics", inventory)
            display_summary_statistics(inventory)
        elif choice == "2":
            print_header("Search Files by Name", inventory)
            search_term = input(highlight_fg + "Enter the file name or partial name to search: " + Style.RESET_ALL).strip()
            search_files_by_name(inventory, search_term)
        elif choice == "3":
            print_header("Filter Files by Extension", inventory)
            extension = input(highlight_fg + "Enter the file extension to filter by (e.g., .txt): " + Style.RESET_ALL).strip()
            filter_files_by_extension(inventory, extension)
        elif choice == "4":
            print_header("Largest Files", inventory)
            top_n = int(input(highlight_fg + "Enter the number of largest files to display: " + Style.RESET_ALL).strip())
            display_largest_files(inventory, top_n)
        elif choice == "5":
            print_header("Group Files by Directory", inventory)
            group_files_by_directory(inventory)
        elif choice == "x":
            print_header("File Inventory Dashboard", inventory)
            break
        else:
            print(text_fg + "Invalid choice. Please try again." + Style.RESET_ALL)

        print_footer_with_scan()

def display_dashboard(inventory):
    """Displays a dashboard summary of the inventory."""
    os.system('cls' if os.name == 'nt' else 'clear')
    print(header_bg + header_fg + "=" * 50)
    print(text_fg + "File Inventory Dashboard".center(50) + Style.RESET_ALL)
    print(header_bg + header_fg + "=" * 50 + Style.RESET_ALL)

    if not inventory:
        print(text_fg + "No data available in the inventory." + Style.RESET_ALL)
        return

    # Calculate size by drive
    size_by_drive = {}
    for item in inventory:
        drive = os.path.splitdrive(item["full_path"])[0]
        size_by_drive[drive] = size_by_drive.get(drive, 0) + item["file_size_bytes"]

    # Find the most recent file
    most_recent_file = max(inventory, key=lambda x: x["last_modified_timestamp"], default=None)

    # Display size by drive
    print(highlight_fg + "Size by drive:")
    for drive, size in size_by_drive.items():
        print(text_fg + f"  {drive}: {human_readable_size(size)}" + Style.RESET_ALL)

    if most_recent_file:
        print(highlight_fg + "Most recent file:")
        print(text_fg + f"  {most_recent_file['file_name']} ({human_readable_size(most_recent_file['file_size_bytes'])})")
        print(text_fg + f"  Last modified: {most_recent_file['last_modified_iso']}")
        print(text_fg + f"  Path: {most_recent_file['full_path']}" + Style.RESET_ALL)

    # Display the most recent scan timestamp
    scan_file = "last_scan.json"
    try:
        if os.path.exists(scan_file):
            with open(scan_file, "r") as f:
                last_scan = json.load(f).get("last_scan")
                relative_time = format_relative_time(last_scan)
                print(highlight_fg + f"Most recent scan: {relative_time}" + Style.RESET_ALL)
        else:
            print(text_fg + "Most recent scan: No scan data available." + Style.RESET_ALL)
    except Exception as e:
        print(text_fg + f"Error reading scan data: {e}" + Style.RESET_ALL)

    print(header_bg + header_fg + "=" * 50 + Style.RESET_ALL)

def update_last_scan():
    """Updates the timestamp of the most recent scan."""
    scan_file = "last_scan.json"
    try:
        with open(scan_file, "w") as f:
            json.dump({"last_scan": datetime.datetime.now().isoformat()}, f)
    except Exception as e:
        print(text_fg + f"Error updating scan data: {e}" + Style.RESET_ALL)

def scan_menu(output_file):
    """Menu for scanning files and updating the inventory."""
    while True:
        # Reload inventory at the start of the menu
        existing_inventory = load_existing_inventory(output_file)

        default_source_folder = Path.home() / "OneDrive" / "Documents"  # Dynamically determine the default path
        available_paths = [str(default_source_folder)] + discover_drives()  # Add default and discovered drives

        print_header("Scan Menu")
        print(highlight_fg + "Available paths:")
        for i, path in enumerate(available_paths, start=1):
            print(text_fg + f"  {i}. {path}")
        print(text_fg + f"  {len(available_paths) + 1}. Enter a custom path")
        print(text_fg + f"  x. Exit" + Style.RESET_ALL)

        choice = input(highlight_fg + "Enter your choice: " + Style.RESET_ALL).strip().lower()

        if choice.isdigit():
            choice = int(choice)
            if 1 <= choice <= len(available_paths):
                source_folder = available_paths[choice - 1]
            elif choice == len(available_paths) + 1:
                source_folder = input(highlight_fg + "Enter the full path to the folder you want to scan: " + Style.RESET_ALL).strip()
                if not os.path.isdir(source_folder):
                    print(text_fg + f"Error: The path '{source_folder}' is not valid. Please try again." + Style.RESET_ALL)
                    continue
            else:
                print(text_fg + "Invalid choice. Please try again." + Style.RESET_ALL)
                continue

            # Start scanning the selected folder
            print_header("Scanning Folder", None)
            print(highlight_fg + f"Starting metadata extraction from: {source_folder}" + Style.RESET_ALL)
            existing_inventory = load_existing_inventory(output_file)
            new_inventory, total_size = traverse_and_extract(source_folder)
            updated_inventory = merge_inventories(existing_inventory, new_inventory)

            with open(output_file, "w") as f:
                json.dump(updated_inventory, f, indent=4)

            print(text_fg + f"✔ Metadata extracted and saved to: {output_file}" + Style.RESET_ALL)
            print(text_fg + f"✔ Total data size: {human_readable_size(total_size)}" + Style.RESET_ALL)

            # Reload the inventory after the scan
            reloaded_inventory = load_existing_inventory(output_file)
            print(text_fg + "✔ Inventory reloaded successfully after the scan." + Style.RESET_ALL)

            # Update the last scan timestamp
            update_last_scan()
        elif choice == "x":
            print_header("File Inventory Dashboard", load_existing_inventory(output_file))
            break
        else:
            print(text_fg + "Invalid choice. Please try again." + Style.RESET_ALL)

        print_footer_with_scan()

def inventory_management_menu(inventory, output_file):
    """Menu for managing the inventory, such as removing a drive and its files."""
    while True:
        # Reload inventory at the start of the menu
        inventory[:] = load_existing_inventory(output_file)

        print_header("Inventory Management Menu", inventory)
        print(header_fg + "\u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510")
        print(text_fg + "\u2502 1. Remove a drive and its files from inventory \u2502")
        print(text_fg + "\u2502 2. Reload inventory file                 \u2502")
        print(text_fg + "\u2502 x. Exit                                \u2502")
        print(header_fg + "\u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518" + Style.RESET_ALL)

        # Display discovered drives
        drives = sorted(set(item["full_path"].split("\\")[0] + "\\" for item in inventory))
        print(highlight_fg + "Discovered drives in inventory:" + Style.RESET_ALL)
        for drive in drives:
            print(text_fg + f"  {drive}" + Style.RESET_ALL)

        choice = input(highlight_fg + "Enter your choice: " + Style.RESET_ALL).strip().lower()

        if choice == "1":
            print(highlight_fg + "Available drives in inventory:" + Style.RESET_ALL)
            for i, drive in enumerate(drives, start=1):
                print(text_fg + f"  {i}. {drive}" + Style.RESET_ALL)

            drive_choice = input(highlight_fg + "Enter the number of the drive to remove: " + Style.RESET_ALL).strip()

            if drive_choice.isdigit() and 1 <= int(drive_choice) <= len(drives):
                drive_to_remove = drives[int(drive_choice) - 1]

                updated_inventory = [item for item in inventory if not item["full_path"].startswith(drive_to_remove)]

                with open(output_file, "w") as f:
                    json.dump(updated_inventory, f, indent=4)

                print(text_fg + f"\u2714 Drive {drive_to_remove} and its files have been removed from the inventory." + Style.RESET_ALL)
                inventory[:] = updated_inventory  # Update the in-memory inventory
            else:
                print(text_fg + "Invalid choice. Please try again." + Style.RESET_ALL)

        elif choice == "2":
            # Reload the inventory file
            reloaded_inventory = load_existing_inventory(output_file)
            inventory[:] = reloaded_inventory  # Update the in-memory inventory
            print(text_fg + "\u2714 Inventory file reloaded successfully." + Style.RESET_ALL)

        elif choice == "x":
            break
        else:
            print(text_fg + "Invalid choice. Please try again." + Style.RESET_ALL)

def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

if __name__ == "__main__":
    output_file = "file_inventory.json"

    # Clear the terminal screen
    clear_screen()

    # Load existing inventory
    existing_inventory = load_existing_inventory(output_file)

    while True:
        # Display dashboard
        display_dashboard(existing_inventory)

        print("\nMain Menu:")
        print("1. Scan for new files and update inventory")
        print("2. Display existing inventory")
        print("3. Inventory management")  # New option
        print("x. Exit")
        main_choice = input("Enter your choice: ").strip().lower()

        if main_choice == "1":
            # Open the scan menu
            scan_menu(output_file)

        elif main_choice == "2":
            # Display existing inventory
            if existing_inventory:
                display_inventory_menu(existing_inventory)
            else:
                print(text_fg + "No inventory data available." + Style.RESET_ALL)

        elif main_choice == "3":
            # Open the inventory management menu
            inventory_management_menu(existing_inventory, output_file)

        elif main_choice == "x":
            clear_screen()
            print(highlight_fg + "Thanks for using my silly app! -arrfour" + Style.RESET_ALL)
            break

        else:
            print(text_fg + "Invalid choice. Please try again." + Style.RESET_ALL)

