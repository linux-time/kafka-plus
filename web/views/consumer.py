from web.extensions import db
from flask import Blueprint, render_template, request, jsonify, session, redirect
#from confluent_kafka.admin import AdminClient, ConfigResource
#from web.utils import get_kafka_admin_client
from web.database import topic_info, clusters, topic_size, consumers_groups_info

mod = Blueprint('consumer', __name__, url_prefix='/api/consumer')

@mod.route('/topic', methods=['GET'])
def get_topic_consumer_details():
    cluster_id = request.args.get('cluster_id', None)
    topic_name = request.args.get('topic_name', None)

    consumers_groups_info_table = consumers_groups_info.query.filter(
        consumers_groups_info.cluster_id == cluster_id,
        consumers_groups_info.topic_name == topic_name
    ).all()

    res_list = []
    for i in consumers_groups_info_table: 
        res_list.append({
            "id": i.id,
            "cluster_id": i.cluster_id,
            "topic_name": i.topic_name,
            "consumer_groups": i.consumer_groups,
            "member_id": i.member_id,
            "updated_at": i.updated_at,
            "client_id": i.client_id,
            "host": i.host,
            "partition": i.partition
        })
    return jsonify(res_list), 200