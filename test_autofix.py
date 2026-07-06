import requests
import json
import time

print("Testing Autofix API...")

# Step 1: Upload and parse resume to get a resume_url and keywords
url = "http://localhost:8000/api/analyze"
data = {
    "job_description": "We need a Senior Software Engineer with deep expertise in PostgreSQL, Kubernetes, and Golang.",
    "candidate_email": "test@example.com"
}
files = {
    "resume": ("test_resume.txt", "John Doe\nSoftware Engineer\nI wrote code for 3 years.", "text/plain")
}

try:
    res = requests.post(url, data=data, files=files)
    res_data = res.json()
    print("Upload response:", res_data)
    
    task_id = res_data.get("task_id")
    if not task_id:
        print("No task ID returned. Exiting.")
        exit(1)
        
    print(f"Waiting for scan task {task_id}...")
    while True:
        poll_res = requests.get(f"http://localhost:8000/api/task/{task_id}").json()
        if poll_res.get("status") == "success":
            scan_result = poll_res.get("data_inserted")[0]
            print("Scan finished!")
            break
        elif poll_res.get("status") == "error":
            print("Scan failed:", poll_res)
            exit(1)
        time.sleep(2)

    # Step 2: Trigger Autofix
    print("Triggering Autofix...")
    autofix_payload = {
        "resume_url": scan_result["resume_url"],
        "job_description": data["job_description"],
        "missing_keywords": ["PostgreSQL", "Kubernetes", "Golang"],
        "improvement_tips": [{"actionable_fix": "Add metrics to bullet points"}],
        "output_format": "pdf"
    }
    
    autofix_res = requests.post("http://localhost:8000/api/autofix", json=autofix_payload).json()
    print("Autofix response:", autofix_res)
    
    autofix_task = autofix_res.get("task_id")
    print(f"Waiting for autofix task {autofix_task}...")
    
    while True:
        poll_res = requests.get(f"http://localhost:8000/api/task/{autofix_task}").json()
        if poll_res.get("status") == "success":
            print("Autofix SUCCESS!")
            print("New Resume URL:", poll_res.get("new_resume_url"))
            break
        elif poll_res.get("status") == "error":
            print("Autofix FAILED:", poll_res)
            break
        time.sleep(2)
        
except Exception as e:
    print("Test failed:", e)
