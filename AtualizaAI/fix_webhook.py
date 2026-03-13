import os
import httpx
import subprocess
from dotenv import load_dotenv

load_dotenv()

def run_cmd(cmd):
    return subprocess.check_output(cmd, shell=True).decode().strip()

project_id = os.getenv("GCP_PROJECT_ID")
region = "us-central1"
service_name = "flose-ai-platform"

try:
    service_url = run_cmd(f"gcloud run services describe {service_name} --platform managed --region {region} --project={project_id} --format=\"value(status.url)\"")
    webhook_url = f"{service_url}/telegram_webhook"
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    set_url = f"https://api.telegram.org/bot{token}/setWebhook?url={webhook_url}"
    
    resp = httpx.get(set_url)
    print("Set Webhook Response:", resp.json())
    
    # Check again
    info_resp = httpx.get(f"https://api.telegram.org/bot{token}/getWebhookInfo")
    print("New Webhook Info:", info_resp.json())
except Exception as e:
    print(f"Error: {e}")
