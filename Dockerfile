FROM apache/airflow:3.1.5

ARG AIRFLOW_HOME_ARG=/opt/airflow
ENV AIRFLOW_HOME=${AIRFLOW_HOME_ARG}

USER airflow
ENV PYTHONPATH=${AIRFLOW_HOME}:$PYTHONPATH

COPY requirements.txt /
RUN pip install  -r /requirements.txt

COPY --chown=airflow:airflow dags /opt/airflow/dags
COPY --chown=airflow:airflow plugins /opt/airflow/plugins
COPY --chown=airflow:airflow business_logic /opt/airflow/business_logic

WORKDIR /opt/airflow
