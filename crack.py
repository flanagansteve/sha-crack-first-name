import hashlib
import argparse
import sys
import requests
from pathlib import Path
import names  # For additional random names after common ones

def get_common_names():
    """
    Gets a list of common names from the SSA dataset.
    Returns names sorted by popularity.
    """
    try:
        # URL for SSA top 1000 names from 2022
        url = "https://www.ssa.gov/oact/babynames/names.zip"
        names_file = "yob1998.txt"
        cache_dir = Path("name_cache")

        # Create cache directory if it doesn't exist
        cache_dir.mkdir(exist_ok=True)

        if not (cache_dir / names_file).exists():
            print("Downloading name dataset...")
            response = requests.get(url)
            with open(cache_dir / "names.zip", "wb") as f:
                f.write(response.content)

            # Unzip the file
            import zipfile
            with zipfile.ZipFile(cache_dir / "names.zip") as zip_ref:
                zip_ref.extractall(cache_dir)

        # Read and parse the names file
        names_list = []
        with open(cache_dir / names_file, 'r') as f:
            for line in f:
                name, gender, count = line.strip().split(',')
                names_list.append((name, int(count)))

        # Sort by frequency (descending) and return just the names
        return [name for name, count in sorted(names_list, key=lambda x: x[1], reverse=True)]
    except Exception as e:
        print(f"Error loading name dataset: {e}")
        return []

def check_name_hash(name, target_hash):
    """Check if a name matches the target hash."""
    name_hash = hashlib.sha1(name.lower().encode('utf-8')).hexdigest()
    return name_hash == target_hash, name_hash

def generate_and_check_names(target_hash, max_attempts):
    """
    First checks common names, then generates random names until max_attempts.
    """
    target_hash = target_hash.lower()
    attempts = 0

    # Try common names first
    common_names = get_common_names()
    print(f"Loaded {len(common_names)} common names to try first...")

    for i, name in enumerate(common_names):
        attempts += 1
        if attempts % 1000 == 0:
            print(f"Checked {attempts} names...", end='\r')

        matches, name_hash = check_name_hash(name, target_hash)
        if matches:
            print()  # Clear progress line
            return name, name_hash

        if attempts >= max_attempts:
            print()  # Clear progress line
            return None, None

    # If we haven't found a match in common names and haven't hit max_attempts,
    # continue with random names
    while attempts < max_attempts:
        name = names.get_first_name()
        attempts += 1

        if attempts % 1000 == 0:
            print(f"Checked {attempts} names...", end='\r')

        matches, name_hash = check_name_hash(name, target_hash)
        if matches:
            print()  # Clear progress line
            return name, name_hash

    print()  # Clear progress line
    return None, None

def main():
    parser = argparse.ArgumentParser(description='Find a name matching a specific SHA1 hash')
    parser.add_argument('hash', help='SHA1 hash to search for')
    parser.add_argument('--max-attempts', type=int, default=1000000,
                      help='Maximum number of names to try (default: 1000000)')

    args = parser.parse_args()

    # Validate hash format
    if len(args.hash) != 40 or not all(c in '0123456789abcdefABCDEF' for c in args.hash):
        print("Error: Invalid SHA1 hash format. Must be 40 hexadecimal characters.")
        sys.exit(1)

    print(f"Searching for name matching hash: {args.hash}")
    print("Starting with most common names first...")

    matching_name, matching_hash = generate_and_check_names(args.hash, args.max_attempts)

    if matching_name:
        print(f"\nFound match!")
        print(f"Name: {matching_name}")
        print(f"Hash: {matching_hash}")
    else:
        print(f"\nNo matching name found after trying {args.max_attempts} names.")

if __name__ == "__main__":
    main()
