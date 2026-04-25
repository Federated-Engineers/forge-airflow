import pandas as pd


# Transformation
def transformation(df1, df2):
    influencer_data, orders_data = df1, df2
    influencer_data['signup_date'] = pd.to_datetime(
        influencer_data['signup_date'], errors='coerce'
    )

    # Broken into steps to stay under 79 characters
    signup_dt = influencer_data['signup_date'].dt
    influencer_data['year'] = signup_dt.year.astype(str)
    influencer_data['month'] = signup_dt.strftime('%m')

    influencer_data = influencer_data.dropna(subset=['year', 'month'])

    # Cleaning the code column - broken into two lines
    influencer_data['influencer_code'] = (
        influencer_data['influencer_code'].astype(str).str.strip('@')
    )

    return influencer_data, orders_data
