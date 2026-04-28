import logging

import requests
from airflow.models import Variable


def slack_failure_alert(context):
    ti = context["task_instance"]
    dag_id = ti.dag_id
    task_id = ti.task_id
    run_id = getattr(ti, "run_id", "unknown")
    try_number = getattr(ti, "try_number", "unknown")
    execution_time = getattr(ti, "start_date", "unknown")
    error = str(context.get("exception", "No exception captured"))
    log_url = getattr(ti, "log_url", "N/A")

    message = {
        "text": ":rotating_light: *Pipeline Task Failed!*",
        "blocks": [
            {"type": "section", 
            "text": {
                "type": "mrkdwn", 
                "text": ":rotating_light: *Airflow Task Failed!*"}},
            {"type": "section", "fields": [
                {"type": "mrkdwn", "text": f"*DAG:*\n{dag_id}"},
                {"type": "mrkdwn", "text": f"*Task:*\n{task_id}"},
                {"type": "mrkdwn", "text": f"*Run ID:*\n{run_id}"},
                {"type": "mrkdwn", "text": f"*Try:*\n{try_number}"},
                {"type": "mrkdwn", 
                "text": f"*Execution Time:*\n{execution_time}"},
                {"type": "mrkdwn", "text": f"*Error:*\n{error}"}
            ]},
            {"type": "section", 
            "text": {
                "type": "mrkdwn", 
                "text": f"<{log_url}|View Logs>"}}
        ]
    }

    webhook = Variable.get("SLACK_WEBHOOK_URL")

    response = requests.post(webhook, json=message)

    if response.status_code not in (200, 201):
        logging.error(
            "Failed to send Slack notification: "
            f"{response.status_code} {response.text}")
    else:
        logging.info("Slack notification sent successfully")


def slack_success_alert(context):
    ti = context["task_instance"]
    dag_id = ti.dag_id
    task_id = ti.task_id
    run_id = ti.run_id
    execution_time = getattr(ti, "start_date", "unknown")
    log_url = ti.log_url

    message = {
        "text": ":white_check_mark: *Pipeline Task Succeeded!*",
        "blocks": [
            {"type": "section", 
            "text": {
                "type": "mrkdwn", 
                "text": ":white_check_mark: *Airflow Task Succeeded!*"}},
            {"type": "section", "fields": [
                {"type": "mrkdwn", "text": f"*DAG:*\n{dag_id}"},
                {"type": "mrkdwn", "text": f"*Task:*\n{task_id}"},
                {"type": "mrkdwn", "text": f"*Run ID:*\n{run_id}"},
		{"type": "mrkdwn", "text": f"*Execution Time:*\n{execution_time}"}
            ]},
                {"type": "section", 
                "text": {
                    "type": "mrkdwn", 
                    "text": f"<{log_url}|View Logs>"}}
        ]
    }

    webhook = Variable.get("SLACK_WEBHOOK_URL")

    resp = requests.post(webhook, json=message)

    if resp.status_code not in (200, 201):
        logging.error(
            "Slack SUCCESS alert failed: "
            f"{resp.status_code} {resp.text}")
    else:
        logging.info("Slack SUCCESS notification sent successfully")
