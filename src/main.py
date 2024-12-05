import time
import os

from logger import app_logger
from vector_utils import fetch_bikes;
from redis_test import check_redis_connection

logger = app_logger.getChild('main')

def process_file(path):
    # TODO: actually do something
    logger.info(f"Processing file: {path}")
    print(path, flush=True)
    

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
    # fetch_bikes() 
    # TODO: fetch the unprocessed reports from redis
    logger.info("Listing files!")
    list_files("scrapped_data")
    time.sleep(5)

if __name__ == "__main__":
    # check_redis_connection()
    main()
