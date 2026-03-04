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
