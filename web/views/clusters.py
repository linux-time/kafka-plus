from web.extensions import db
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for

mod = Blueprint('clusters', __name__, url_prefix='/api/clusters')

@mod.route('/')
def create_cluster():
    pass
