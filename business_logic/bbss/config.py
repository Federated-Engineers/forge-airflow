LOCATIONS = [
    {
        "name": "puerto_portals",
        "query": "39.5347,2.5656",
    },
    {
        "name": "port_adriano",
        "query": "39.490472,2.480188",
    },
]

WEATHER_API_URL = "https://api.weatherapi.com/v1/forecast.json"

SSM_PARAMETER_NAME = "/production/forge/bbss/api-key"

BUCKET_NAME = "federated-production-forge-data-engineers-bbss-data-lake"

RAW_PREFIX = "raw/weatherapi"

TRANSFORMED_PREFIX = "transformed/weatherapi"

ANALYTICS_PREFIX = "analytics/weatherapi"

FORECAST_DAYS = 1
