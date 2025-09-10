def validate_date(date_string):
    from datetime import datetime
    
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def format_date(date):
    return date.strftime('%Y-%m-%d') if date else None

def get_today_date():
    from datetime import datetime
    return datetime.today().date()