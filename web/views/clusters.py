from web.extensions import db
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from web.database import clusters

mod = Blueprint('clusters', __name__, url_prefix='/api/clusters')

@mod.route('/', methods=['POST'])
def create_cluster():
    data = request.json
    cluster_name = data.get('cluster_name', None)
    bootstrap_servers = data.get('bootstrap_servers', None)
    remarks = data.get('remarks', '') 

    if not cluster_name or not bootstrap_servers:
        return jsonify({"status": "error", "message": "Cluster name and bootstrap servers are required."}), 400

    new_cluster = clusters(cluster_name=cluster_name, bootstrap_servers=bootstrap_servers, remarks=remarks)
    db.session.add(new_cluster)
    db.session.commit()
    return jsonify({"status": "success", "message": "Cluster created successfully.", "cluster_id": new_cluster.id}), 201

@mod.route('/', methods=['GET'])
def get_cluster():
    clusters_table = clusters.query.all()
    cluster_list = []
    for cluster in clusters_table:
        cluster_list.append({
            "id": cluster.id,
            "cluster_name": cluster.cluster_name,
            "bootstrap_servers": cluster.bootstrap_servers,
            "remarks": cluster.remarks
        })
    return jsonify({"status": "success", "clusters": cluster_list}), 200