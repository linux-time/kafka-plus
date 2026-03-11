import time

from flask_apscheduler import APScheduler
from web.extensions import db
from web.database import topic_info, clusters, topic_size
from sqlalchemy import and_

from kafka import KafkaAdminClient

scheduler = APScheduler()

def get_kafka_admin_client(cluster_address):
    print(cluster_address)
    return KafkaAdminClient(bootstrap_servers=cluster_address)

def get_topic_size(cluster_address):
    admin = get_kafka_admin_client(cluster_address)
    print(admin)
    log_dirs_data = admin.describe_log_dirs()
    log_dirs = log_dirs_data.to_object()
    return log_dirs

@scheduler.task('interval', id='job_test', seconds=5)
def job1():
    print("定时任务1执行中...")

@scheduler.task('interval', id='job_get_topic_info', seconds=5)
def get_topic_info():
    print("定时任务2执行中，获取 topic 信息...")
    from web import app
    with app.app_context():
        # 这里可以执行数据库操作，例如查询 topic_info 表
        #topic_info_table = topic_info.query.all()
        clusters_table = clusters.query.all()
        for cluster in clusters_table:
            cluster_address = cluster.bootstrap_servers
            log_dir = get_topic_size(cluster_address)
            for i in log_dir['log_dirs']:
                for j in i['topics']:
                    for k in j['partitions']:
                        #print(cluster.id, j['name'], k['partition_index'], k['partition_size'])
                        topic_size_table = topic_size.query.filter(and_(
                            topic_size.cluster_id == cluster.id,
                            topic_size.topic_name == j['name'],
                            topic_size.partition_id == k['partition_index']
                        )).first()
                        print(topic_size_table)
                        if topic_size_table:
                            topic_size_table.updated_at = int(time.time())
                            topic_size_table.partition_size = k['partition_size']
                        else:
                            new_topic_size = topic_size(
                                cluster_id=cluster.id,
                                topic_name=j['name'],
                                partition_id=k['partition_index'],
                                partition_size=k['partition_size'],
                                updated_at=int(time.time())
                            )
                            db.session.add(new_topic_size)
                        db.session.commit()