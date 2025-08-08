import mysql.connector
from mysql.connector import pooling, Error
from config import Config
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename='app.log')
logger = logging.getLogger(__name__)

db_pool = None
try:
    db_pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="main_app_pool",
        pool_size=5,
        host=Config.DATABASE_HOST,
        user=Config.DATABASE_USER,
        password=Config.DATABASE_PASSWORD,
        database=Config.DATABASE_NAME,
        charset='utf8mb4'
    )
    logger.info("Successfully created shared database connection pool.")
except Error as e:
    logger.critical(f"FATAL: Could not create the shared database pool. The application will not work. Error: {e}")