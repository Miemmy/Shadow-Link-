from celery_app import celery_app

# importing all scanners to register tasks
import scanners 

if __name__ == "__main__":
    celery_app.start()

