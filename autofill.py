import os
import sys
import requests
import json
import yaml
import pandas as pd
import pprint


def get_notion_db(db, key):
    # get database information
    url = f"https://api.notion.com/v1/databases/{db}/query"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {key}",
        "Notion-Version": "2022-06-28"
    }
    response = requests.post(url, headers=headers)

    if response.status_code == 200:
        data = response.json()["results"]
        return [d["properties"]for d in data]
    else:
        print(f"Failed to retrieve data: {response.status_code} - {response.text}")

def get_paper_info(doi):
    url = f"https://api.crossref.org/works/{doi}"
    response = requests.get(url)
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()["message"]
        if len(data["short-container-title"]) > 0: journal = data["short-container-title"][0]
        else: journal = data["container-title"][0]
        return {
            "Author": [f"{a['given']} {a['family']}" for a in data["author"]],
            "Title": data["title"][0],
            "Year": data["published"]["date-parts"][0][0],
            "Journal": journal,
            "doi": doi
        }


def push_notion_db(paper_info, db, key):
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    # get row id
    url = f"https://api.notion.com/v1/databases/{db}/query"
    payload = {
        "filter": {
            "property": "doi",
            "url": {"equals": paper_info["doi"]}
        }
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        print(f"Failed to add entry: {url} - {response.status_code} - {response.text}")
        return None

    # push data into the row
    page_id = response.json()["results"][0]["id"]
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {
        "parent": {"database_id": db},
        "properties": {
            "Title": { "title": [{"text": {"content": paper_info["Title"]}}] },
            "Author": { "multi_select": [{"name": a} for a in paper_info["Author"]] },
            "Year": {"number": paper_info["Year"]},
            "Journal": {"select": {"name": paper_info["Journal"]}}
        }
    }
    response = requests.patch(url, json=payload, headers=headers)
    if response.status_code == 200:
        print(f"New entry {paper_info['doi']} added to the database")
    else:
        print(f"Failed to add entry: {url} - {response.status_code} - {response.text}")



if __name__ == "__main__":
    with open("key.yaml") as f: config = yaml.safe_load(f)
    db_name = "Projects"
    db = config["tables"][db_name]
    key = config["api_key"]
    props_db = get_notion_db(db, key)

    for entry in props_db:
        doi = entry["doi"]["url"]
        title = entry["Title"]["title"]
        if (doi is not None) and len(title) == 0:
            paper_info = get_paper_info(doi)
            push_notion_db(paper_info, db, key)