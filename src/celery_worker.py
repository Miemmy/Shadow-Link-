from celery_app import celery_app
from log import init_logging, get_worker_logger

# Initialize logging for worker
init_logging()
logger = get_worker_logger()

# importing all scanners to register tasks
import scanners 

if __name__ == "__main__":
    logger.info("Starting Celery worker")
    try:
        celery_app.start()
    except Exception as e:
        logger.error("Failed to start Celery worker: %s", str(e))
        raise

