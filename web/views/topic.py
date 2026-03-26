from web.extensions import db
from flask import Blueprint, render_template, request, jsonify, session, redirect
#from confluent_kafka.admin import AdminClient, ConfigResource
#from web.utils import get_kafka_admin_client
from web.database import topic_info, clusters, topic_size

mod = Blueprint('topic', __name__, url_prefix='/api/topics')

@mod.route('/detail', methods=['GET'])
def get_topic_details():
    cluster_id = request.args.get('cluster_id', None)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 30, type=int)

    topic_info_table = topic_info.query.filter_by(cluster_id=cluster_id).paginate(
        page=page, per_page=per_page, error_out=False)

    pagination = {
        "total": topic_info_table.total,
        "pages": topic_info_table.pages,
        "has_next": topic_info_table.has_next,
        "data": []
    } 
    
    for i in topic_info_table.items:
        pagination['data'].append({
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
    return jsonify(pagination), 200