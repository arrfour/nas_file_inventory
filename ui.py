# This is version Point2N Branch, developed by arrfour

from utils import clear_screen, print_header, header_fg, text_fg, highlight_fg, paginate_output, human_readable_size, format_relative_time
from inventory import InventoryManager
from scanner import start_scan, discover_drives, discover_network_hosts
import os
from pathlib import Path
from colorama import Style
from datetime import datetime

def scan_menu(inventory_manager):
    """Displays the scan menu."""
    default_folder = Path.home() / "OneDrive" / "Documents"

    while True:
        clear_screen()
        print_header("Scan Menu")
        print(text_fg + f"1. Scan default folder (Current: {default_folder})" + Style.RESET_ALL)
        print(text_fg + "2. Discover and choose from available drives" + Style.RESET_ALL)
        print(text_fg + "3. Discover and choose from network hosts" + Style.RESET_ALL)
        print(text_fg + "4. Enter a custom path to scan" + Style.RESET_ALL)
        print(text_fg + "x. Back to Main Menu" + Style.RESET_ALL)

        choice = input(highlight_fg + "Enter your choice: " + Style.RESET_ALL).strip().lower()

        if choice == "1":
            start_scan(str(default_folder), inventory_manager)
        elif choice == "2":
            drives = discover_drives()
            if not drives:
                print(text_fg + "No drives found." + Style.RESET_ALL)
            else:
                print(header_fg + "Available Drives:" + Style.RESET_ALL)
                for i, drive in enumerate(drives, start=1):
                    print(text_fg + f"  {i}. {drive}" + Style.RESET_ALL)
                drive_choice = input(highlight_fg + "Select a drive to scan: " + Style.RESET_ALL).strip()
                if drive_choice.isdigit() and 1 <= int(drive_choice) <= len(drives):
                    selected_drive = drives[int(drive_choice) - 1]
                    start_scan(selected_drive, inventory_manager)
                else:
                    print(text_fg + "Invalid selection. Please try again." + Style.RESET_ALL)
        elif choice == "3":
            hosts = discover_network_hosts()
            if not hosts:
                print(text_fg + "No network hosts found." + Style.RESET_ALL)
            else:
                print(header_fg + "Available Network Hosts:" + Style.RESET_ALL)
                for i, host in enumerate(hosts, start=1):
                    print(text_fg + f"  {i}. {host}" + Style.RESET_ALL)
                host_choice = input(highlight_fg + "Select a host to scan: " + Style.RESET_ALL).strip()
                if host_choice.isdigit() and 1 <= int(host_choice) <= len(hosts):
                    selected_host = hosts[int(host_choice) - 1]
                    print(text_fg + f"Selected host: {selected_host}. Implement share discovery here." + Style.RESET_ALL)
                    # Placeholder for share discovery and selection
                else:
                    print(text_fg + "Invalid selection. Please try again." + Style.RESET_ALL)
        elif choice == "4":
            custom_path = input(highlight_fg + "Enter the custom path to scan: " + Style.RESET_ALL).strip()
            if os.path.isdir(custom_path):
                start_scan(custom_path, inventory_manager)
            else:
                print(text_fg + "Invalid path. Please try again." + Style.RESET_ALL)
        elif choice == "x":
            break
        else:
            print(text_fg + "Invalid choice. Please try again." + Style.RESET_ALL)

def inventory_menu(inventory_manager):
    """Displays the inventory menu."""
    while True:
        clear_screen()
        print_header("Inventory Menu")
        print(text_fg + "1. Summary statistics" + Style.RESET_ALL)
        print(text_fg + "2. Search files by name" + Style.RESET_ALL)
        print(text_fg + "3. Filter files by extension" + Style.RESET_ALL)
        print(text_fg + "4. Display largest files" + Style.RESET_ALL)
        print(text_fg + "5. Group files by directory" + Style.RESET_ALL)
        print(text_fg + "6. Group files by hostname and drive" + Style.RESET_ALL)
        print(text_fg + "x. Back to Main Menu" + Style.RESET_ALL)

        choice = input(highlight_fg + "Enter your choice: " + Style.RESET_ALL).strip().lower()

        if choice == "1":
            total_files, total_size = inventory_manager.get_summary_statistics()
            total_hosts = len(set(item.get("hostname", "Unknown Host") for item in inventory_manager.inventory))
            most_recent_file = max(inventory_manager.inventory, key=lambda x: x.get("last_modified_timestamp", 0), default=None)

            if most_recent_file:
                recent_file_name = most_recent_file["file_name"][:30] + ("..." if len(most_recent_file["file_name"]) > 30 else "")
                recent_file_size = human_readable_size(most_recent_file["file_size_bytes"])
                recent_file_date = datetime.fromtimestamp(most_recent_file["last_modified_timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
                recent_file_relative = format_relative_time(most_recent_file["last_modified_iso"])
            else:
                recent_file_name = "N/A"
                recent_file_size = "N/A"
                recent_file_date = "N/A"
                recent_file_relative = "N/A"

            print(header_fg + "Summary Statistics".center(50, "=") + Style.RESET_ALL)
            print(highlight_fg + f"Total Inventory Size: {total_size}".ljust(50) + Style.RESET_ALL)
            print(highlight_fg + f"Total Files: {total_files}".ljust(50) + Style.RESET_ALL)
            print(highlight_fg + f"Total Hosts: {total_hosts}".ljust(50) + Style.RESET_ALL)
            print(highlight_fg + "Most Recent File:".ljust(50) + Style.RESET_ALL)
            print(text_fg + f"  Name: {recent_file_name}".ljust(50) + Style.RESET_ALL)
            print(text_fg + f"  Size: {recent_file_size}".ljust(50) + Style.RESET_ALL)
            print(text_fg + f"  Date: {recent_file_date}".ljust(50) + Style.RESET_ALL)
            print(text_fg + f"  Relative Time: {recent_file_relative}".ljust(50) + Style.RESET_ALL)
            print(header_fg + "=" * 50 + Style.RESET_ALL)

            input(highlight_fg + "Press Enter to return to the menu..." + Style.RESET_ALL)
        elif choice == "2":
            search_term = input(highlight_fg + "Enter the file name or partial name to search: " + Style.RESET_ALL).strip()
            results = [item for item in inventory_manager.inventory if search_term.lower() in item["file_name"].lower()]
            lines = [f"{item['file_name']} ({human_readable_size(item['file_size_bytes'])}) - {item['full_path']}" for item in results]
            paginate_output(lines)
        elif choice == "3":
            extension = input(highlight_fg + "Enter the file extension to filter by (e.g., .txt): " + Style.RESET_ALL).strip()
            results = [item for item in inventory_manager.inventory if item["file_extension"].lower() == extension.lower()]
            lines = [f"{item['file_name']} ({human_readable_size(item['file_size_bytes'])}) - {item['full_path']}" for item in results]
            paginate_output(lines)
        elif choice == "4":
            top_n = int(input(highlight_fg + "Enter the number of largest files to display: " + Style.RESET_ALL).strip())
            sorted_files = sorted(inventory_manager.inventory, key=lambda x: x["file_size_bytes"], reverse=True)
            lines = [f"{item['file_name']} ({human_readable_size(item['file_size_bytes'])}) - {item['full_path']}" for item in sorted_files[:top_n]]
            paginate_output(lines)
        elif choice == "5":
            directory_groups = {}
            for item in inventory_manager.inventory:
                directory = os.path.dirname(item["full_path"])
                if directory not in directory_groups:
                    directory_groups[directory] = {"count": 0, "size": 0}
                directory_groups[directory]["count"] += 1
                directory_groups[directory]["size"] += item["file_size_bytes"]
            lines = [f"{directory}: {stats['count']} file(s), {human_readable_size(stats['size'])}" for directory, stats in directory_groups.items()]
            paginate_output(lines)
        elif choice == "6":
            grouped_data = {}
            for item in inventory_manager.inventory:
                full_path = item.get("full_path", "")
                drive = os.path.splitdrive(full_path)[0] if os.name == 'nt' else "/"
                hostname = item.get("hostname", "Unknown Host")
                if hostname not in grouped_data:
                    grouped_data[hostname] = {}
                if drive not in grouped_data[hostname]:
                    grouped_data[hostname][drive] = {"count": 0, "size": 0}
                grouped_data[hostname][drive]["count"] += 1
                grouped_data[hostname][drive]["size"] += item.get("file_size_bytes", 0)
            lines = []
            for hostname, drives in grouped_data.items():
                lines.append(f"Hostname: {hostname}")
                for drive, stats in drives.items():
                    lines.append(f"  Drive: {drive} - {stats['count']} file(s), {human_readable_size(stats['size'])}")
            paginate_output(lines)
        elif choice == "x":
            break
        else:
            print(text_fg + "Invalid choice. Please try again." + Style.RESET_ALL)

def inventory_management_menu(inventory_manager):
    """Displays the inventory management menu."""
    while True:
        clear_screen()
        print_header("Inventory Management Menu")
        print(text_fg + "1. Remove a drive or host" + Style.RESET_ALL)
        print(text_fg + "2. Reload inventory" + Style.RESET_ALL)
        print(text_fg + "x. Back to Main Menu" + Style.RESET_ALL)

        choice = input(highlight_fg + "Enter your choice: " + Style.RESET_ALL).strip().lower()

        if choice == "1":
            remove_drive_or_host(inventory_manager)
        elif choice == "2":
            inventory_manager.load_inventory()
            print(text_fg + "✔ Inventory successfully reloaded." + Style.RESET_ALL)
        elif choice == "x":
            break
        else:
            print(text_fg + "Invalid choice. Please try again." + Style.RESET_ALL)

def remove_drive_or_host(inventory_manager):
    """Allows the user to remove a drive or an entire host's entries from the inventory."""
    hosts = set(item["hostname"] for item in inventory_manager.inventory if "hostname" in item)
    drives = set(os.path.splitdrive(item["full_path"])[0] for item in inventory_manager.inventory if os.name == 'nt')

    print(header_fg + "Available Hosts:" + Style.RESET_ALL)
    hosts_list = list(hosts)
    for i, host in enumerate(hosts_list, start=1):
        print(text_fg + f"  {i}. {host}" + Style.RESET_ALL)

    print(header_fg + "Available Drives:" + Style.RESET_ALL)
    drives_list = list(drives)
    for i, drive in enumerate(drives_list, start=1):
        print(text_fg + f"  {i + len(hosts_list)}. {drive}" + Style.RESET_ALL)

    choice = input(highlight_fg + "Enter the number of the host or drive to remove: " + Style.RESET_ALL).strip()
    if choice.isdigit():
        choice = int(choice)
        if 1 <= choice <= len(hosts_list):
            selected_host = hosts_list[choice - 1]
            inventory_manager.inventory = [item for item in inventory_manager.inventory if item["hostname"] != selected_host]
            inventory_manager.save_inventory()
            print(text_fg + f"✔ Host {selected_host} and its files have been removed from the inventory." + Style.RESET_ALL)
        elif len(hosts_list) < choice <= len(hosts_list) + len(drives_list):
            selected_drive = drives_list[choice - len(hosts_list) - 1]
            inventory_manager.inventory = [item for item in inventory_manager.inventory if not item["full_path"].startswith(selected_drive)]
            inventory_manager.save_inventory()
            print(text_fg + f"✔ Drive {selected_drive} and its files have been removed from the inventory." + Style.RESET_ALL)
        else:
            print(text_fg + "Invalid selection. Please try again." + Style.RESET_ALL)
    else:
        print(text_fg + "Invalid input. Please enter a number." + Style.RESET_ALL)

def display_main_menu(inventory_manager):
    while True:
        clear_screen()
        total_files, total_size = inventory_manager.get_summary_statistics()
        print_header("Main Menu")
        print(text_fg + f"Inventory: {total_files} files, {total_size}" + Style.RESET_ALL)
        print(text_fg + "1. Scan for new files" + Style.RESET_ALL)
        print(text_fg + "2. View inventory" + Style.RESET_ALL)
        print(text_fg + "3. Manage inventory" + Style.RESET_ALL)
        print(text_fg + "x. Exit" + Style.RESET_ALL)

        choice = input(highlight_fg + "Enter your choice: " + Style.RESET_ALL).strip().lower()
        if choice == "1":
            scan_menu(inventory_manager)
        elif choice == "2":
            inventory_menu(inventory_manager)
        elif choice == "3":
            inventory_management_menu(inventory_manager)
        elif choice == "x":
            clear_screen()
            print(highlight_fg + "Thanks for using the app!" + Style.RESET_ALL)
            break
        else:
            print(text_fg + "Invalid choice. Please try again." + Style.RESET_ALL)