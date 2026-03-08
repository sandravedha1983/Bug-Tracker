from .models import db, Bug, User
from sqlalchemy import func
from datetime import datetime, timedelta

def get_priority_distribution():
    """Returns counts of bugs grouped by priority."""
    results = db.session.query(Bug.priority, func.count(Bug.id)).group_by(Bug.priority).all()
    return {priority: count for priority, count in results}

def get_status_overview():
    """Returns counts of bugs grouped by status."""
    results = db.session.query(Bug.status, func.count(Bug.id)).group_by(Bug.status).all()
    return {status: count for status, count in results}

def get_trends_data():
    """Returns number of bugs reported per day for the last 7 days."""
    today = datetime.utcnow().date()
    last_week = [today - timedelta(days=i) for i in range(6, -1, -1)]
    
    # Query for bugs created in the last 7 days
    results = db.session.query(
        func.date(Bug.created_at), 
        func.count(Bug.id)
    ).filter(Bug.created_at >= datetime.utcnow() - timedelta(days=7)).group_by(func.date(Bug.created_at)).all()
    
    counts_map = {str(date): count for date, count in results}
    
    labels = [date.strftime('%a') for date in last_week]
    data = [counts_map.get(str(date), 0) for date in last_week]
    
    return {"labels": labels, "data": data}

def get_developer_load():
    """Returns number of bugs assigned to each developer."""
    results = db.session.query(
        User.name, 
        func.count(Bug.id)
    ).join(Bug, User.id == Bug.assigned_to).filter(User.role == 'developer').group_by(User.name).all()
    
    labels = [r[0] for r in results]
    data = [r[1] for r in results]
    
    return {"labels": labels, "data": data}
