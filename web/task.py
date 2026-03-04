from flask_apscheduler import APScheduler

scheduler = APScheduler()

@scheduler.task('interval', id='job_test', seconds=5)
def job1():
    print("定时任务1执行中...")

#@scheduler.task('interval', id='job_test2', seconds=5)
#def job2():
#    print("定时任务执2行中...")