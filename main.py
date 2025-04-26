# This is version Point2N Branch, developed by arrfour

import os
import json
from ui import display_main_menu
from inventory import InventoryManager
from utils import clear_screen
from colorama import Fore, Style

highlight_fg = Fore.YELLOW  # Define the highlight_fg variable

# Ensure necessary files exist
for file_name in ["file_inventory.json", "last_scan.json"]:
    if not os.path.exists(file_name):
        with open(file_name, "w") as f:
            if file_name == "file_inventory.json":
                json.dump([], f, indent=4)  # Initialize as empty list
            elif file_name == "last_scan.json":
                json.dump({"last_scan": None}, f, indent=4)  # Initialize with null last scan
        print(f"DEBUG: Created missing file: {file_name}")

if __name__ == "__main__":
    output_file = "file_inventory.json"

    # Initialize inventory manager
    inventory_manager = InventoryManager(output_file)

    # Display main menu
    display_main_menu(inventory_manager)

    # Exit message after main menu loop ends
    clear_screen()
    print(highlight_fg + "This is version Point2N Branch, developed by arrfour. Thanks for using my silly app!" + Style.RESET_ALL)