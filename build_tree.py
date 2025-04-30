import os
import json

def build_directory_tree(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)

    tree = {}
    for item in data:
        full_path = item.get('full_path')
        if not full_path:
            continue

        path_parts = os.path.normpath(full_path).split(os.sep)
        current = tree
        for part in path_parts:
            if part not in current:
                current[part] = {}
            current = current[part]

    return tree

def print_tree(node, prefix=""):
    for name, child in node.items():
        print(f"{prefix}├── {name}/")
        print_tree(child, prefix + "│   ")

def save_tree_as_markdown(node, file_path, level=0):
    with open(file_path, "w") as f:
        def write_node(node, level):
            for name, child in node.items():
                f.write(f"{'  ' * level}- {name}/\n")
                write_node(child, level + 1)
        write_node(node, level)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python build_tree.py <json_file>")
    else:
        tree = build_directory_tree(sys.argv[1])
        print_tree(tree)

        # Save the tree structure as a Markdown file
        save_tree_as_markdown(tree, "folder_structure.md")
