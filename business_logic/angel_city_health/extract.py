from business_logic.angel_city_health.connect_snowflake import \
    get_snowflake_connection


def copy_patients_data():
    sql = """
            COPY INTO ACHS_ANALYTICS.STAGING.PATIENTS_RAW (raw_json,
            source_file_name)
            FROM (
                SELECT
                    $1,
                    METADATA$FILENAME
                FROM @ACHS_ANALYTICS.STAGING.ACHS_RAW_DATA_STAGE
            )
            FILE_FORMAT = (TYPE = 'JSON')
            PATTERN = '.*patients/.*\\.json'
            ON_ERROR = 'CONTINUE';
        """
    conn = get_snowflake_connection()
    cur = conn.cursor()
    cur.execute(sql)
    cur.close()
    conn.close()


def copy_providers_data():
    sql = """
            COPY INTO ACHS_ANALYTICS.STAGING.PROVIDERS_RAW (raw_json,
            source_file_name)
            FROM (
                SELECT
                    $1,
                    METADATA$FILENAME
                FROM @ACHS_ANALYTICS.STAGING.ACHS_RAW_DATA_STAGE
            )
            FILE_FORMAT = (TYPE = 'JSON')
            PATTERN = '.*providers/.*\\.json'
            ON_ERROR = 'CONTINUE';
        """
    conn = get_snowflake_connection()
    cur = conn.cursor()
    cur.execute(sql)
    cur.close()
    conn.close()


def copy_claims_data():
    sql = """
            COPY INTO ACHS_ANALYTICS.STAGING.CLAIMS_RAW
                (raw_json, source_file_name)
            FROM (
                SELECT
                    $1,
                    METADATA$FILENAME
                FROM @ACHS_ANALYTICS.STAGING.ACHS_RAW_DATA_STAGE
            )
            FILE_FORMAT = (TYPE = 'JSON')
            PATTERN = '.*claims.*\\.json'
            ON_ERROR = 'CONTINUE';
        """
    conn = get_snowflake_connection()
    cur = conn.cursor()
    cur.execute(sql)
    cur.close()
    conn.close()


def copy_diagnoses_data():
    sql = """
            COPY INTO ACHS_ANALYTICS.STAGING.DIAGNOSES_RAW
                (raw_json, source_file_name)
            FROM (
                SELECT
                    $1,
                    METADATA$FILENAME
                FROM @ACHS_ANALYTICS.STAGING.ACHS_RAW_DATA_STAGE
            )
            FILE_FORMAT = (TYPE = 'JSON')
            PATTERN = '.*diagnoses.*\\.json'
            ON_ERROR = 'CONTINUE';
        """
    conn = get_snowflake_connection()
    cur = conn.cursor()
    cur.execute(sql)
    cur.close()
    conn.close()


def copy_encounters_data():
    sql = """
            COPY INTO ACHS_ANALYTICS.STAGING.ENCOUNTERS_RAW
                (raw_json, source_file_name)
            FROM (
                SELECT
                    $1,
                    METADATA$FILENAME
                FROM @ACHS_ANALYTICS.STAGING.ACHS_RAW_DATA_STAGE
            )
            FILE_FORMAT = (TYPE = 'JSON')
            PATTERN = '.*encounters.*\\.json'
            ON_ERROR = 'CONTINUE';
        """
    conn = get_snowflake_connection()
    cur = conn.cursor()
    cur.execute(sql)
    cur.close()
    conn.close()
