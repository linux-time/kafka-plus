from web.extensions import db
from flask import Blueprint, render_template, request, jsonify, session, redirect
from confluent_kafka.admin import AdminClient, ConfigResource

mod = Blueprint('topic', __name__, url_prefix='/api/topic')

admin_client = AdminClient({'bootstrap.servers': 'localhost:9092'})

@mod.route('/api/topics/detail', methods=['GET'])
def get_topic_details():
    try:
        # 1. 获取基础元数据 (名称, 分区, 副本)
        metadata = admin_client.list_topics(timeout=10)
        topic_data = {}

        for name, topic in metadata.topics.items():
            # 获取副本数（取第一个分区的副本列表长度）
            replication_factor = len(topic.partitions[0].replicas) if topic.partitions else 0
            topic_data[name] = {
                "topic_name": name,
                "partitions": len(topic.partitions),
                "replication_factor": replication_factor,
                "disk_usage_gb": 0,
                "retention_h": 0,
                "consumer_groups": []
            }

        # 2. 获取磁盘使用量
        broker_ids = [b.id for b in metadata.brokers.values()]
        log_dirs = admin_client.describe_log_dirs(broker_ids)
        for bid, future in log_dirs.items():
            for log_dir in future.result():
                for replica in log_dir.replicas:
                    if replica.topic in topic_data:
                        # 换算为 GB
                        topic_data[replica.topic]["disk_usage_gb"] += replica.size / (1024**3)

        # 3. 获取保留时长 (Retention Ms)
        resource_configs = [ConfigResource(ConfigResource.Type.TOPIC, name) for name in topic_data.keys()]
        config_futures = admin_client.describe_configs(resource_configs)
        for res, future in config_futures.items():
            configs = future.result()
            retention_ms = int(configs.get('retention.ms').value)
            # 换算为 小时
            topic_data[res.name]["retention_h"] = round(retention_ms / (1000 * 60 * 60), 1)

        # 4. 获取消费组 (简化逻辑：找出正在消费该 Topic 的组)
        # 注意：在大规模集群中，此步建议异步缓存，否则响应较慢
        groups_future = admin_client.list_consumer_groups()
        all_groups = groups_future.result().valid
        for group in all_groups:
            group_id = group.group_id
            # 这里可以进一步查询 group 订阅的 topic 并匹配，此处示意
            # topic_data[target_topic]["consumer_groups"].append(group_id)

        # 格式化输出
        result = list(topic_data.values())
        for item in result:
            item["disk_usage_gb"] = round(item["disk_usage_gb"], 2)

        return jsonify({"status": "success", "data": result})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500