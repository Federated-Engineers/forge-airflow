
from business_logic.bbss.analytics import build_weather_analytics
from business_logic.bbss.extract import extract_weather_data
from business_logic.bbss.transform import transform_weather_data


def extract_task():
    """
    Run the extraction task.
    """
    extract_weather_data()


def transform_task():
    """
    Run the transformation task.
    """
    transform_weather_data()


def analytics_task():
    """
    Run the analytics task.
    """
    build_weather_analytics()