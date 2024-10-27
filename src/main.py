import time
import os

def process_file(path):
    # TODO: actually do something
    print(path)

def list_files(path):
    """Lists all files in the specified directory."""

    try:
        files = os.listdir(path)
        for file in files:
            if "report" not in file:
                if "final" not in file:
                    continue

            process_file(file)
    except FileNotFoundError:
        print(f"Directory not found: {path}")


def main():
    while True:
        print("\nListing files!")
        list_files("scrapped_data")
        time.sleep(5)

if __name__ == "__main__":
    main()