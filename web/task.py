import time
import json
import subprocess

import requests
from flask_apscheduler import APScheduler
from web.config import config
from web.extensions import db
from web.database import topic_info, clusters, topic_size
from sqlalchemy import and_
#from kafka import KafkaAdminClient
from confluent_kafka.admin import AdminClient, ConfigResource

scheduler = APScheduler()

@scheduler.task('interval', id='job_test', seconds=5)
def job1():
    print("定时任务1执行中...")

@scheduler.task('interval', id='job_test2', seconds=5)
def job2():
    print("定时任务2执行中...")

@scheduler.task('interval', id='get_topic_list', seconds=10)
def get_topic_list():
    from web import app
    with app.app_context(): 
        clusters_table = clusters.query.all()
        for cluster in clusters_table:
            try:
                client = AdminClient({'bootstrap.servers': cluster.bootstrap_servers})
                # 获取元数据，捕获可能的连接超时
                metadata = client.list_topics(timeout=10)
                kafka_topic_names = set(metadata.topics.keys())

                # 2. 批量获取数据库现有的 Topic
                existing_topics_query = topic_info.query.filter_by(cluster_id=cluster.id).all()
                # 创建一个映射字典方便快速查找对象
                db_topic_map = {t.topic_name: t for t in existing_topics_query}
                db_topic_names = set(db_topic_map.keys())

                # 3. 处理新增 (New)
                new_topics = kafka_topic_names - db_topic_names
                for topic_name in new_topics:
                    topic_metadata = metadata.topics[topic_name]
                    partitions = len(topic_metadata.partitions)
                    replication_factor = len(topic_metadata.partitions[0].replicas) if partitions > 0 else 0
                    
                    new_item = topic_info(
                        cluster_id=cluster.id,
                        topic_name=topic_name,
                        partitions=partitions,
                        replication_factor=replication_factor,
                        status=1, # 活跃
                        created_at=int(time.time()),
                        updated_at=int(time.time())
                    )
                    db.session.add(new_item)

                # 4. 处理删除 (Deleted) - 批量更新状态
                deleted_topics = db_topic_names - kafka_topic_names
                if deleted_topics:
                    topic_info.query.filter(
                        topic_info.cluster_id == cluster.id,
                        topic_info.topic_name.in_(deleted_topics)
                    ).update({
                        "status": 2, 
                        "updated_at": int(time.time())
                    }, synchronize_session=False)

                # 5. 处理恢复 (Recover) - 原本是 status=2，现在 Kafka 里又有了
                recovered_topics = kafka_topic_names & db_topic_names
                for name in recovered_topics:
                    if db_topic_map[name].status == 2:
                        db_topic_map[name].status = 1
                        db_topic_map[name].updated_at = int(time.time())

                # 统一提交，保证事务原子性且性能最高
                db.session.commit()
                print(f"集群 {cluster.cluster_name} 同步完成")

            except Exception as e:
                db.session.rollback()
                print(f"同步集群 {cluster.cluster_name} 失败: {str(e)}")


@scheduler.task('interval', id='get_topic_size', seconds=12)
def get_topic_size():
    from web import app
    with app.app_context():
        log_dir_bin = config.log_dir_bin
        all_clusters = clusters.query.all()
        
        for cluster in all_clusters:
            try:
                # 1. 获取 Kafka 磁盘数据
                cmd = [log_dir_bin, "--bootstrap-server", cluster.bootstrap_servers]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode != 0:
                    print(f"集群 {cluster.id} 执行错误: {result.stderr}")
                    continue
                
                data = json.loads(result.stdout)
                
                # 2. 一次性查出该集群下所有 Topic 存入内存字典 (优化查询)
                existing_topics = topic_info.query.filter_by(cluster_id=cluster.id).all()
                topic_map = {t.topic_name: t for t in existing_topics}
                
                # 3. 解析数据并累加大小
                # 注意：同一个 Topic 可能分布在多个 Broker 和多个路径下
                topic_size_accumulator = {}
                
                for broker_id, broker_data in data.items():
                    for log_dir in broker_data:
                        if log_dir.get('Topics'):
                            for t_entry in log_dir['Topics']:
                                t_name = t_entry['Topic']
                                # 累加该路径下所有分区的 Size
                                current_path_size = sum(p['Size'] for p in t_entry['Partitions'])
                                topic_size_accumulator[t_name] = topic_size_accumulator.get(t_name, 0) + current_path_size

                # 4. 更新内存对象
                now = int(time.time())
                updated_count = 0
                for t_name, total_size in topic_size_accumulator.items():
                    if t_name in topic_map:
                        topic_obj = topic_map[t_name]
                        # 只有数值变化较大或时间较久时才更新，减少脏数据写入
                        topic_obj.disk_usage_bytes = total_size
                        topic_obj.updated_at = now
                        updated_count += 1

                # 5. 在集群层面统一提交 (解决锁表关键)
                db.session.commit()
                print(f"集群 {cluster.cluster_name} 更新了 {updated_count} 条 Topic 容量数据")

            except Exception as e:
                db.session.rollback()
                print(f"集群 {cluster.cluster_name} 容量同步异常: {str(e)}")