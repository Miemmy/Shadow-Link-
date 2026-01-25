from celery_app import celery_app

# Import scanners so Celery knows what tasks exist
import scanners 

if __name__ == "__main__":
    celery_app.start()

