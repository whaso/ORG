from celery_tasks.main import app

@app.task(bind=True,name="haha")
def debug_task(self):
    for i in range(0,10):
        print("helloworld {}".format(i))
