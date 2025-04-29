import os
import json

def build_directory_tree(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    for item in data:
        full_path = item.get('full_path')
        if full_path and os.path.exists(full_path):
            print(f"Skipping existing path: {full_path}")
            continue
        
        # Create the directory structure
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        print(f"Created directory structure for: {full_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python build_tree.py <json_file>")
    else:
        build_directory_tree(sys.argv[1])
