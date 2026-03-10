import time

from flask_apscheduler import APScheduler
from web.extensions import db
from web.database import topic_info, clusters, topic_size
from sqlalchemy import and_

from kafka import KafkaAdminClient

scheduler = APScheduler()

def get_kafka_admin_client(cluster_address):
    return KafkaAdminClient(bootstrap_servers=cluster_address)

def get_topic_size(cluster_address):
    admin = get_kafka_admin_client(cluster_address)
    log_dirs_data = admin.describe_log_dirs()
    log_dirs = log_dirs_data.to_object()
    return log_dirs

@scheduler.task('interval', id='job_test', seconds=5)
def job1():
    print("定时任务1执行中...")

@scheduler.task('interval', id='job_get_topic_info', seconds=3600)
def get_topic_info():
    with db.app.app_context():
        # 这里可以执行数据库操作，例如查询 topic_info 表
        topic_info_table = topic_info.query.all()
        clusters_table = clusters.query.all()
        for cluster in clusters_table:
            cluster_address = cluster.bootstrap_servers
            log_dir = get_topic_size(cluster_address)
            for i in log_dir:
                for k in i['partitions']:
                    topic_size_table = topic_size.query.filter(and_(
                        topic_size.cluster_id == cluster.id,
                        topic_size.topic_name == i['name'],
                        topic_size.partition_id == k['partition_index']
                    )).first()
                    if topic_size_table:
                        topic_size_table.updated_at = int(time.time())
                        topic_size_table.partition_size = k['partition_size']
                    else:
                        new_topic_size = topic_size(
                            cluster_id=cluster.id,
                            topic_name=i['name'],
                            partition_id=k['partition_index'],
                            partition_size=k['partition_size'],
                            updated_at=int(time.time())
                        )
                        db.session.add(new_topic_size)
        db.session.commit()