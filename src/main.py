import time
import os
import logging  # Add logging import

from vector_utils import fetch_bikes;

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_file(path):
    # TODO: actually do something
    logger.info(f"Processing file: {path}")
    # print(path, flush=True)
    

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
        logger.error(f"Directory not found: {path}")
    except OSError as e:
        logger.error(f"Error accessing directory {path}: {e}")


def main():
    fetch_bikes()
    while True:
        logger.info("Listing files!")
        list_files("scrapped_data")
        time.sleep(5)

if __name__ == "__main__":
    main()