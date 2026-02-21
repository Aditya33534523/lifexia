from datetime import datetime
import uuid

def get_timestamp():
    return datetime.utcnow()

def format_date(date, format_str='%Y-%m-%d %H:%M:%S'):
    if isinstance(date, datetime):
        return date.strftime(format_str)
    return date

def generate_session_id():
    return f"session_{uuid.uuid4().hex}"
