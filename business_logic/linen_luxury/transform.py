import pandas as pd


##Transformation
def transformation(df1, df2):
    influencer_data, orders_data = df1, df2
    influencer_data['signup_date']=pd.to_datetime(influencer_data['signup_date'],errors='coerce')
    influencer_data['year']=influencer_data['signup_date'].dt.year.astype(str)
    influencer_data['month']=influencer_data['signup_date'].dt.strftime('%m')
    influencer_data=influencer_data.dropna(subset=['year','month'])

    influencer_data['influencer_code']=influencer_data['influencer_code'].astype(str).str.strip('@')

    return influencer_data, orders_data