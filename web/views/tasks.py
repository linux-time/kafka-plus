import subprocess
import json

from web.extensions import db
from flask import Blueprint, render_template, request, jsonify, session, redirect
from web.database import topic_info, clusters, topic_size
from web.config import config

mod = Blueprint('tasks', __name__, url_prefix='/api/tasks')

@mod.route('/topic-size', methods=['GET'])
def get_topic_size():
    log_dir_bin = config.log_dir_bin
    clusters_table = clusters.query.all()
    for cluster in clusters_table:
        bootstrap_servers = cluster.bootstrap_servers
        cmd = [log_dir_bin, "--bootstrap-server", bootstrap_servers]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        if result.returncode != 0:
            print(f"执行错误: {result.stderr}")
        
        # 这里的 data 将包含所有 Broker 的磁盘路径、副本大小、以及是否离线
        data = json.loads(result.stdout)
        print(data)
        return jsonify({"status": "success", "data": data}), 200