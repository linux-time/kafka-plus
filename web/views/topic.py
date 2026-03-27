from web.extensions import db
from flask import Blueprint, render_template, request, jsonify, session, redirect, make_response
#from confluent_kafka.admin import AdminClient, ConfigResource
#from web.utils import get_kafka_admin_client
from web.database import topic_info, clusters, topic_size, consumers_groups_info

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

@mod.route('/output', methods=['GET'])
def output_topic_data():
    topic_info_table = topic_info.query.filter_by(status=1).all()
    clusters_table = clusters.query.all()
    consumer_groups_info_table = consumers_groups_info.query.all()

    data_list = []

    for i in topic_info_table:
        cluster_name = next((c.cluster_name for c in clusters_table if c.id == i.cluster_id), "Unknown Cluster")
        consumer_groups = next((cg.consumer_groups for cg in consumer_groups_info_table if cg.cluster_id == i.cluster_id and cg.topic_name == i.topic_name), "Unknown Consumer Groups")

        data_list.append({
            "id": i.id,
            "cluster_id": i.cluster_id,
            "cluster_name": cluster_name,
            "topic_name": i.topic_name,
            "consumer_groups": consumer_groups,
            "partitions": i.partitions,
            "replication_factor": i.replication_factor,
            "disk_usage_bytes": i.disk_usage_bytes,
            "retention_ms": i.retention_ms,
            "created_at": i.created_at,
            "updated_at": i.updated_at,
            "status": i.status,
            "remarks": i.remarks
        })
    import csv, io
    si = io.StringIO()
    si.write(u'\ufeff')  # 添加BOM头，解决Excel打开乱码问题
    cw = csv.writer(si)
    cw.writerow(["ID", "Cluster ID", "Cluster Name", "Topic Name", "Consumer Groups", "Partitions", "Replication Factor", "Disk Usage (Bytes)", "Retention (ms)", "Created At", "Updated At", "Status", "Remarks"])
    for data in data_list:
        cw.writerow([
            data["id"],
            data["cluster_id"],
            data["cluster_name"],
            data["topic_name"],
            data["consumer_groups"],
            data["partitions"],
            data["replication_factor"],
            data["disk_usage_bytes"],
            data["retention_ms"],
            data["created_at"],
            data["updated_at"],
            data["status"],
            data["remarks"]
        ])  
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=topic_data.csv"
    output.headers["Content-type"] = "text/csv; charset=utf-8"
    return output