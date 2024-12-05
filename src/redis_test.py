import redis
import time

from logger import app_logger
from colorama import Fore
from datetime import datetime

# Set up logging
logger = app_logger.getChild('redis')

class RedisConnection:
    """
    A singleton class that manages the Redis connection.
    
    This class implements a lazy loading pattern for Redis connection,
    creating the connection only when first needed and reusing it afterwards.
    """
    def __init__(self):
        """Initialize RedisConnection with no active connection."""
        self._redis_client = None
    
    def get_connection(self) -> redis.Redis:
        """
        Get or create a Redis connection.

        Returns:
            redis.Redis: An active Redis connection instance.

        Raises:
            redis.ConnectionError: If unable to establish connection to Redis.

        Note:
            - Uses 'redis' as host when running in Docker, 'localhost' otherwise
            - Connection is created only once and reused for subsequent calls
            - Performs a ping test to verify connection is working
        """
        if self._redis_client is None:
            try:
                self._redis_client = redis.Redis(host='redis', port=6379, db=0)
                # Test the connection. If connection fails, error will happen here.
                self._redis_client.ping()  

            except redis.ConnectionError as e:
                logger.error(Fore.RED + f"Failed to connect to Redis: {e}")
                raise
        return self._redis_client
    
# Create a singleton instance
redis_connection = RedisConnection()

def check_redis_connection():
    r = redis_connection.get_connection()
    if r is None:
        logger.error(Fore.RED + "Redis connection not available")
        raise redis.ConnectionError("Redis connection not available")
    else:
        logger.info(Fore.GREEN + "Redis connection successful")

def save_jobstate_to_redis(state_type: str, job_type: str, location: str, value: int) -> None:
    """
    Set a key-value pair in Redis.

    Args:
        state_type (str): The type of state being set.
        job_type (str): The type of job.
        location (str): The location for the job.
        value (int): The value to store.

    Raises:
        redis.ConnectionError: If unable to connect to Redis.
        redis.RedisError: For other Redis-related errors.

    Note:
        Redis-py automatically handles the encoding of Python objects to bytes:
        1. Strings are encoded to UTF-8 bytes.
        2. Integers are converted to strings and then encoded.
        3. Other types may require explicit conversion before setting.

        This automatic encoding simplifies the process of storing data in Redis,
        but it's important to be aware of it when retrieving and decoding data.
    """
    r = redis_connection.get_connection()
    if r is None:
        logger.error(Fore.RED + "Redis connection not available")
        raise redis.ConnectionError("Redis connection not available")

    key = f"{state_type}_{job_type}_{location}"
    try:
        r.set(key, value)
        logger.info(Fore.YELLOW + f"Successfully set state for {key}")
    except redis.RedisError as e:
        logger.error(Fore.RED + f"Failed to set state for {key}: {e}")
        raise

def get_jobstate_from_redis(state_type: str, job_type: str, location: str) -> str:
    """
    Retrieve a value from Redis and decode it to a UTF-8 string.

    Args:
        state_type (str): The type of state being retrieved.
        job_type (str): The type of job.
        location (str): The location for the job.

    Returns:
        str or None: The decoded string value if the key exists, None otherwise.

    Raises:
        redis.ConnectionError: If unable to connect to Redis.

    Note:
        Redis stores data as bytes. We decode the returned value to a UTF-8 string
        because:
        1. Redis stores data in a binary format.
        2. Python 3 distinguishes between strings (sequences of Unicode characters) 
           and bytes.
        3. The Redis-py client returns raw bytes from Redis.
        4. Decoding converts these bytes back into a Python string.

        This approach ensures we always return either a string or None, making it 
        easier to work with in Python code. It also handles cases where the key 
        doesn't exist in Redis (which returns None).
    """
    r = redis_connection.get_connection()
    if r is None:
        logger.error(Fore.RED + "Redis connection not available")
        raise redis.ConnectionError("Redis connection not available")

    key = f"{state_type}_{job_type}_{location}"
    try:
        value = r.get(key)
        logger.info(Fore.YELLOW + f"Successfully retrieved state for {key}")
        return value.decode('utf-8') if value else None
    except redis.RedisError as e:
        logger.error(Fore.RED + f"Failed to get state for {key}: {e}")
        raise

def get_search_config_from_redis(site: str) -> dict:
    try:
        r = redis_connection.get_connection()
        if r is None:
            logger.error(Fore.RED + "Redis connection not available")
            raise redis.ConnectionError("Redis connection not available")

        key = f"{site}_search_config"
        config = r.json().get(key)
        return config if config else None
    except redis.RedisError as e:
        logger.error(Fore.RED + f"Error in get_search_config_from_redis for {site}: {e}")
        raise

def set_search_config_in_redis(site: str, search_params: dict) -> None:
    try:
        r = redis_connection.get_connection()
        if r is None:
            logger.error(Fore.RED + "Redis connection not available")
            raise redis.ConnectionError("Redis connection not available")

        key = f"{site}_search_config"
        response = r.json().set(key, "$", search_params)
        if response:
            logger.info(Fore.YELLOW + f"Successfully set search config for {site}")
        else:
            logger.error(Fore.RED + f"Failed to set search config for {site}, response: {response}")
    except redis.RedisError as e:
        logger.error(Fore.RED + f"Error in set_search_config_in_redis for {site}: {e}")
        raise

def set_last_scrape(job_type: str, location: str) -> None:
    """
    Set the last scrape time for a specific job and location.

    Args:
        job_type (str): The type of job.
        location (str): The location for the job.
    """
    value = int(time.time())
    state_type = "last_scrape"
    save_jobstate_to_redis(state_type, job_type, location, value)

def set_jobs_as_viewed(job_type: str, location: str) -> None:
    """
    Mark jobs as viewed for a specific job type and location.

    Args:
        job_type (str): The type of job.
        location (str): The location for the job.
    """
    state_type = "jobs_viewed"
    save_jobstate_to_redis(state_type, job_type, location, 1)

def set_jobs_as_not_viewed(job_type: str, location: str) -> None:
    """
    Mark jobs as not viewed for a specific job type and location.

    Args:
        job_type (str): The type of job.
        location (str): The location for the job.
    """
    state_type = "jobs_viewed"
    save_jobstate_to_redis(state_type, job_type, location, 0)

def should_scrape_by_jobs_state(job_type: str, location: str) -> bool:
    """
    Determine if scraping should occur based on the jobs viewed state.

    Args:
        job_type (str): The type of job.
        location (str): The location for the job.

    Returns:
        bool: True if there is no scrap history or jobs have been viewed, False otherwise.
    """
    state = get_jobstate_from_redis("jobs_viewed", job_type, location)
    # None = no scrap history
    # 1 = jobs viewed
    # 0 = jobs not viewed
    # Return True if state is None or 1, False otherwise
    return state is None or state == '1'

def should_scrape_by_time(job_type: str, location: str, interval_seconds: int) -> bool:
    """
    Determine if scraping should occur based on the time since the last scrape.

    Args:
        job_type (str): The type of job.
        location (str): The location for the job.
        interval_seconds (int): The minimum interval in seconds between scrapes.

    Returns:
        bool: True if enough time has passed since the last scrape or if no last scrape is recorded.
    """
    last_scrape = get_jobstate_from_redis("last_scrape", job_type, location)
    if last_scrape is None:
        return True
    # the number of seconds that have elapsed since the last scrape >= to the given interval
    # the program should wait to scrape again
    return (int(time.time()) - int(last_scrape)) >= interval_seconds

def save_report_to_redis(site: str, report: dict, timestamp: str, query: str, location: str) -> None:
    """
    Save a job description to Redis as a JSON string.

    Args:
        site (str): The job site the data was scraped from.
        report (dict): The full report to be saved.
        timestamp (str): The timestamp of the scrape.
        query (str): The query used to scrape the data.
        location (str): The location used to scrape the data.

    Raises:
        redis.RedisError: If there is an error saving to Redis.
    """

    query = query.replace(" ", "_")
    location = location.replace(" ", "_")
    key = f"{query}_{location}_{site}_{timestamp}"

    try:
        r = redis_connection.get_connection()
        response = r.json().set(key, "$", report)
        logger.info(Fore.YELLOW + f"Successfully saved report '{key}' to Redis with response: {response}")
    except redis.RedisError as e:
        logger.error(Fore.RED + f"Failed to save report '{key}' in function 'save_report_to_redis'. Error: {e}. Report: {report}")
        raise