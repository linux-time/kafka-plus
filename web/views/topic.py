from web.extensions import db
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for

mod = Blueprint('topic', __name__, url_prefix='/api/topic')

@mod.route('/')
def get_topic_info():
    pass