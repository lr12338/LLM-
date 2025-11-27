# db_utils.py
import time

import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool
from config import DATABASE_CONFIG
db_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="vessel_pool",
    pool_size=30,
    **DATABASE_CONFIG
)

def get_db_connection(retries=3, delay=2):
    for attempt in range(retries):
        try:
            return db_pool.get_connection()
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise e
