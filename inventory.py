# This is version Point2N Branch, developed by arrfour

import os
import json
from utils import human_readable_size

class InventoryManager:
    def __init__(self, output_file):
        self.output_file = output_file
        self.inventory = self.load_inventory()

    def save_inventory(self):
        """Saves the current inventory to the output file in the local folder."""
        try:
            # Ensure the output file path is in the local folder
            local_path = os.path.join(os.getcwd(), self.output_file)
            print(f"DEBUG: Saving inventory to local path: {local_path}")

            with open(local_path, "w") as f:
                json.dump(self.inventory, f, indent=4)

            print(f"DEBUG: Inventory successfully saved to {local_path}")
        except Exception as e:
            print(f"Error saving inventory: {e}")

    def load_inventory(self):
        """Loads the inventory from the output file in the local folder."""
        try:
            # Ensure the output file path is in the local folder
            local_path = os.path.join(os.getcwd(), self.output_file)
            if os.path.exists(local_path):
                print(f"DEBUG: Loading inventory from local path: {local_path}")

                with open(local_path, "r") as f:
                    return json.load(f)
            else:
                print(f"DEBUG: {local_path} does not exist. Initializing empty inventory.")
        except Exception as e:
            print(f"Error loading inventory: {e}")
        return []

    def merge_inventory(self, new_inventory):
        """Merges new inventory data into the existing inventory."""
        try:
            # Debug log: Start merging
            print(f"DEBUG: Merging {len(new_inventory)} new items into inventory.")

            inventory_dict = {item["full_path"]: item for item in self.inventory}
            for new_item in new_inventory:
                inventory_dict[new_item["full_path"]] = new_item

            self.inventory = list(inventory_dict.values())

            # Debug log: Merge complete
            print(f"DEBUG: Merge complete. Total inventory size: {len(self.inventory)}")

            self.save_inventory()
        except Exception as e:
            print(f"Error merging inventory: {e}")

    def get_summary_statistics(self):
        total_files = len(self.inventory)
        total_size = sum(item["file_size_bytes"] for item in self.inventory)
        return total_files, human_readable_size(total_size)