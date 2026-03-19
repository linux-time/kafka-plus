import time
import json
import subprocess

import requests
from flask_apscheduler import APScheduler
from web.config import config
from web.extensions import db
from web.database import topic_info, clusters, topic_size, consumers_groups_info
from sqlalchemy import and_
#from kafka import KafkaAdminClient
from confluent_kafka.admin import AdminClient, ConfigResource

scheduler = APScheduler()

@scheduler.task('interval', id='job_test', seconds=20)
def job1():
    print("定时任务1执行中...")

@scheduler.task('interval', id='job_test2', seconds=20)
def job2():
    print("定时任务2执行中...")

@scheduler.task('interval', id='get_topic_list', seconds=60)
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


@scheduler.task('interval', id='get_topic_size', seconds=60)
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

@scheduler.task('interval', id='get_consumer_groups', seconds=15)
def get_consumer_groups():
    from web import app
    with app.app_context():
        all_clusters = clusters.query.all()
        now_ts = int(time.time())

        for cluster in all_clusters:
            try:
                # 1. 快速获取所有消费组 ID
                client = AdminClient({'bootstrap.servers': cluster.bootstrap_servers})
                # 设置略长的超时，确保大规模集群能返回
                cg_future = client.list_consumer_groups(request_timeout=5)
                group_names = [g.group_id for g in cg_future.result(timeout=5).valid]
                
                if not group_names:
                    continue

                # 2. 批量描述消费组
                describe_future = client.describe_consumer_groups(group_names, request_timeout=5)
                
                topic_to_groups = {}  # 用于更新 topic_info 表: {topic: set(groups)}
                current_assignments = [] # 用于更新 consumers_groups_info 表

                for group_name, future in describe_future.items():
                    try:
                        group_desc = future.result(timeout=5)
                        for member in group_desc.members:
                            if member.assignment and member.assignment.topic_partitions:
                                for tp in member.assignment.topic_partitions:
                                    # 汇总 Topic 对应的消费组
                                    topic_to_groups.setdefault(tp.topic, set()).add(group_name)
                                    # 汇总成员详情
                                    current_assignments.append({
                                        "topic_name": tp.topic,
                                        "partition": tp.partition,
                                        "cluster_id": cluster.id,
                                        "consumer_groups": group_name,
                                        "member_id": member.member_id,
                                        "client_id": member.client_id,
                                        "host": member.host,
                                    })
                    except Exception as e:
                        print(f"消费组 {group_name} 描述异常: {e}")

                # --- 数据库操作优化阶段 ---

                # 3. 优化 topic_info 表更新 (批量操作)
                db_topics = topic_info.query.filter_by(cluster_id=cluster.id).all()
                for t in db_topics:
                    new_groups_str = ",".join(topic_to_groups.get(t.topic_name, []))
                    if t.consumer_groups != new_groups_str: # 仅当内容变化时更新
                        t.consumer_groups = new_groups_str
                        t.updated_at = now_ts

                # 4. 优化 consumers_groups_info 表更新 (关键性能点)
                # 一次性读入现有记录，构建复合主键映射: {(topic, partition, group): object}
                existing_cgit = consumers_groups_info.query.filter_by(cluster_id=cluster.id).all()
                cgit_map = { (c.topic_name, c.partition, c.consumer_groups): c for c in existing_cgit }
                
                processed_keys = set()
                for item in current_assignments:
                    key = (item['topic_name'], item['partition'], item['consumer_groups'])
                    processed_keys.add(key)
                    
                    if key in cgit_map:
                        # 已存在，更新字段
                        target = cgit_map[key]
                        target.member_id = item['member_id']
                        target.client_id = item['client_id']
                        target.host = item['host']
                        target.updated_at = now_ts
                    else:
                        # 不存在，新增记录
                        new_c = consumers_groups_info(
                            **item,
                            updated_at=now_ts
                        )
                        db.session.add(new_c)

                # 5. 可选：清理数据库中已经不存在的分配关系 (Kafka侧已消失的)
                # for key, obj in cgit_map.items():
                #     if key not in processed_keys:
                #         db.session.delete(obj)

                # 6. 一个集群处理完，统一 Commit
                db.session.commit()
                print(f"集群 {cluster.cluster_name} 同步完成，处理记录: {len(current_assignments)}")

            except Exception as e:
                db.session.rollback()
                print(f"集群 {cluster.cluster_name} 全局异常: {str(e)}")