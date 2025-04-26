# This is version Point2N Branch, developed by arrfour

import os
from colorama import Fore, Back, Style
import json
from datetime import datetime

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# Load colors dynamically
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

COLORS = load_colors()
header_bg = getattr(Back, COLORS["header_bg"], Back.WHITE)
header_fg = getattr(Fore, COLORS["header_fg"], Fore.BLUE)
text_fg = getattr(Fore, COLORS["text_fg"], Fore.RED)
highlight_fg = getattr(Fore, COLORS["highlight_fg"], Fore.CYAN)

def print_header(title):
    print("=" * 50)
    print(title.center(50))
    print("=" * 50)

def human_readable_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_units = ["B", "KB", "MB", "GB", "TB"]
    i = int((len(str(size_bytes)) - 1) / 3)
    p = 1024 ** i
    s = round(size_bytes / p, 2)
    return f"{s} {size_units[i]}"

def paginate_output(lines, page_size=10):
    """Displays output in pages with single-key navigation options."""
    total_pages = (len(lines) + page_size - 1) // page_size  # Calculate total pages
    current_page = 0

    while True:
        clear_screen()  # Clear screen for each page
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

def format_relative_time(last_scan_iso):
    """Formats the last scan timestamp into a human-readable, relative time."""
    try:
        last_scan_time = datetime.fromisoformat(last_scan_iso)
        now = datetime.now()
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