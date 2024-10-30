import json
import time
import logging  # Add logging import

import numpy as np
import pandas as pd
import requests
import redis
from redis.commands.search.field import (
    NumericField,
    TagField,
    TextField,
    VectorField,
)
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from sentence_transformers import SentenceTransformer

client = redis.Redis(host="redis", port=6379, decode_responses=True)

URL = ("https://raw.githubusercontent.com/bsbodden/redis_vss_getting_started"
    "/main/data/bikes.json"
    )

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_bikes() -> None:
    logger.info("Fetching bikes!")
    try:
        response = requests.get(URL, timeout=10)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        bikes = response.json()
        logger.info("Bikes fetched successfully.")
    except requests.RequestException as e:
        logger.error(f"Error fetching bikes: {e}")
        return

    try:
        pipeline = client.pipeline()
        for i, bike in enumerate(bikes, start=1):
            redis_key = f"bikes:{i:03}"
            pipeline.json().set(redis_key, "$", bike)
        res = pipeline.execute()
        logger.info("Bikes saved to Redis successfully.")
    except redis.RedisError as e:
        logger.error(f"Error saving bikes to Redis: {e}")

if __name__ == "__main__":
    fetch_bikes()