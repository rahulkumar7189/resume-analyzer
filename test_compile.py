import requests
import time
import sys

API_URL = "http://localhost:3000/api"

# 1. Test compile-pdf
print("Testing compile-pdf...")
compile_payload = {
    "resume_url": "/uploads/1781789379_Rahul_Kumar_MLSS2026_Final.pdf",
    "accepted_edits": [
        {"original": "software", "suggested": "Software Engineering"}
    ],
    "template": "premium"
}

res = requests.post(f"{API_URL}/compile-pdf", json=compile_payload)
print(f"Compile Response: {res.status_code} {res.text}")
if res.status_code != 200:
    sys.exit(1)

data = res.json()
if data.get("status") != "queued":
    print("Not queued!")
    sys.exit(1)

task_id = data["task_id"]
print(f"Task ID: {task_id}")

while True:
    time.sleep(2)
    res = requests.get(f"{API_URL}/task/{task_id}")
    print(f"Poll Response: {res.status_code} {res.text}")
    task_data = res.json()
    
    if task_data.get("status") == "success":
        print("Success!")
        print("New Resume URL:", task_data.get("new_resume_url"))
        break
    elif task_data.get("status") == "error":
        print("Error!")
        break
    else:
        print("Still processing...")
