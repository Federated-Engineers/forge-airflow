from datetime import date


def get_today_date() -> date:
    '''
    Get today's date for partitioning s3 objects
    Returns:
        Today's date in the format YYYY-MM-DD
    '''
    today_date = date.today().strftime("%Y-%m-%d")
    return today_date
