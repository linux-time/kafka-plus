from web.extensions import db
from flask import Blueprint, render_template, request, jsonify, session, redirect
#from confluent_kafka.admin import AdminClient, ConfigResource
#from web.utils import get_kafka_admin_client
from web.database import topic_info, clusters, topic_size

mod = Blueprint('topic', __name__, url_prefix='/api/topics')

@mod.route('/detail1', methods=['GET'])
def get_topic_details():
    topic_info_table = topic_info.query.filter_by(cluster_id=1).all()
    res_list = []
    for i in topic_info_table:
        res_list.append({
            "id": i.id,
            "cluster_id": i.cluster_id,
            "topic_name": i.topic_name,
            "consumer_groups": i.consumer_groups,
            "partitions": i.partitions,
            "replication_factor": i.replication_factor,
            "disk_usage_bytes": i.disk_usage_bytes,
            "retention_ms": i.retention_ms,
            "created_at": i.created_at,
            "updated_at": i.updated_at,
            "status": i.status,
            "remarks": i.remarks
        })
    return jsonify({"status": "success", "topics": res_list}), 200