import json

def fetch_candidate_profile(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        candidate_profile = json.load(file)

    return candidate_profile

def fetch_resume(file_path):
    with open(file_path, "r") as file:
        resume_data = json.load(file)

    return resume_data