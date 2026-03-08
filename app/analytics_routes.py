from flask import Blueprint, jsonify, render_template
from flask_login import login_required
from .decorators import admin_required
from .analytics_utils import (
    get_priority_distribution, 
    get_status_overview, 
    get_trends_data, 
    get_developer_load
)

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/analytics')
@login_required
@admin_required
def dashboard():
    return render_template('analytics.html')

@analytics_bp.route('/api/analytics/priority')
@login_required
@admin_required
def priority_data():
    """
    Get Bug Priority Distribution
    ---
    tags:
      - Analytics
    responses:
      200:
        description: Priority counts
        schema:
          properties:
            High: {type: integer}
            Medium: {type: integer}
            Low: {type: integer}
    """
    return jsonify(get_priority_distribution())

@analytics_bp.route('/api/analytics/status')
@login_required
@admin_required
def status_data():
    """
    Get Bug Status Overview
    ---
    tags:
      - Analytics
    responses:
      200:
        description: Status counts
        schema:
          properties:
            Open: {type: integer}
            In Progress: {type: integer}
            Resolved: {type: integer}
            Closed: {type: integer}
    """
    return jsonify(get_status_overview())

@analytics_bp.route('/api/analytics/trends')
@login_required
@admin_required
def trends_data():
    """
    Get Bug Trends Over Time
    ---
    tags:
      - Analytics
    responses:
      200:
        description: A list of daily bug counts
    """
    return jsonify(get_trends_data())

@analytics_bp.route('/api/analytics/developer-load')
@login_required
@admin_required
def developer_load_data():
    """
    Get Developer Workload Distribution
    ---
    tags:
      - Analytics
    responses:
      200:
        description: Workload stats per developer
    """
    return jsonify(get_developer_load())
