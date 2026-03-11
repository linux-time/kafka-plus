import time

from flask_apscheduler import APScheduler
from web.extensions import db
from web.database import topic_info, clusters, topic_size
from sqlalchemy import and_
from kafka import KafkaAdminClient
from confluent_kafka.admin import AdminClient, ConfigResource

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

@scheduler.task('interval', id='job_get_partitions_size', seconds=5)
def get_partitions_size():
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

@scheduler.task('interval', id='job_write_topic_partitions_size', seconds=6)
def write_topic_partitions_size():
    from web import app
    with app.app_context():
        topic_info_table = topic_info.query.all()
        for topic in topic_info_table:
            topic_size_table = topic_size.query.filter(and_(
                topic_size.cluster_id == topic.cluster_id,
                topic_size.topic_name == topic.topic_name
                #topic_size.updated_at <= time.time() - 3600
            )).all()
            if topic_size_table:
                size_sum = 0
                for topic_size_item in topic_size_table:
                    size_sum += topic_size_item.partition_size
                topic.disk_usage_bytes = size_sum
                topic.updated_at = int(time.time())
                db.session.commit()

@scheduler.task('interval', id='job_get_topic_info', seconds=7)
def get_topic_info():
    from web import app
    with app.app_context():
        clusters_table = clusters.query.all()
        for cluster in clusters_table:
            admin_client = AdminClient({'bootstrap.servers': cluster.bootstrap_servers})
            metadata = admin_client.list_topics(timeout=10)

            for name, topic in metadata.topics.items():
                # 获取副本数（取第一个分区的副本列表长度）
                replication_factor = len(topic.partitions[0].replicas) if topic.partitions else 0
                topic_info_table = topic_info.query.filter(and_(
                    topic_info.cluster_id == cluster.id,
                    topic_info.topic_name == name
                )).first()
                if topic_info_table:
                    topic_info_table.partitions = len(topic.partitions)
                    topic_info_table.replication_factor = replication_factor
                    topic_info_table.updated_at = int(time.time())
                else:
                    new_topic_info = topic_info(
                        cluster_id=cluster.id,
                        topic_name=name,
                        partitions=len(topic.partitions),
                        replication_factor=replication_factor,
                        created_at=int(time.time()),
                        updated_at=int(time.time()),
                        status=1
                    )
                    db.session.add(new_topic_info)
                db.session.commit()