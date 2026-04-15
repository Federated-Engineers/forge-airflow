import gspread
import pandas as pd
import json
import awswrangler as wr
import boto3

# initialize boto session and ssm parameter
session = boto3.Session()
ssm = session.client('ssm')

s3_path = 's3://federated-engineers-staging-forge-datalake/glaciair_logistic'

# get service credentials from ssm parameter
parameter_name = '/production/google-service-account/credentials'
google_sc = ssm.get_parameter(Name=parameter_name)

# set up google service credentials
cred_dict = json.loads(google_sc['Parameter']['Value'])

spreadsheet_names = ['Finance Overview', 'Marketing Performance', 'Supply Chain Master', 'User Growth Metrics']

def load_gsheets_s3_csv(report_date):
    '''
    A function to load google sheets source data into S3 bucket
    '''
    # authenticate google service credentials
    gc = gspread.service_account_from_dict(cred_dict)

    # open google sheets by name
    for gsheet_name in spreadsheet_names:
        spreadsheet = gc.open(gsheet_name)
        
        # selecting worksheet by its title. All the spreadsheets has just one sheet named sheet1
        worksheet = spreadsheet.worksheet("Sheet1")

        # convert google sheet data to pandas dataframe
        sheet_df = pd.DataFrame(worksheet.get_all_records())

        s3_prefix = gsheet_name.lower().replace(' ', '_')
        wr.s3.to_csv(
            df=sheet_df,
            path=f'{s3_path}/{s3_prefix}/{report_date}/{s3_prefix}.csv',
            index=False
        )