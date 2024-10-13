import os
import sys
import requests
import yaml
from rumps import *
#from autofill import *
import subprocess


def show_alert(title, message):
    script = f'display dialog "{message}" with title "{title}"'
    subprocess.run(['osascript', '-e', script])


def check_api_key(key):
    url = 'https://api.notion.com/v1/users'
    headers = {
        "Authorization": f"Bearer {key}",
        "Notion-Version": "2022-06-28"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return True, ""
    else: 
        return False, f"{response.status_code} - {response.text}"


def check_notion_db_id(db, key):
    # get database information
    url = f"https://api.notion.com/v1/databases/{db}/query"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {key}",
        "Notion-Version": "2022-06-28"
    }
    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        return True, ""
    else: 
        return False, f"{response.status_code} - {response.text}"



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
        elif len(data["container-title"]) > 0: journal = data["container-title"][0]
        else: journal = "-"
        authors = [ f"{a.get('given')} {a.get('family')}" if 'given' in a else a.get("name") for a in data["author"] ]
        authors = [ a for a in authors if len(a) < 100 ]
        if len(authors) > 100: authors = authors[:5]
        return {
            "Author": authors,
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


class NotionCitationApp(App):

    def __init__(self):
        super(NotionCitationApp, self).__init__("NotionCitationApp")
        self.icon = "logo.png"
        self.quit_button = None
        self.update_menu()

    def update_menu(self):
        with open("key.yaml") as f: 
            self.config = yaml.safe_load(f)
            if self.config is None: self.config = {}
        
        self.dbs = self.config.get("database", {})
        self.menu.clear()
        self.menu.update([
            [
                MenuItem("Settings"), [
                    MenuItem("Add API key", self.add_api_key), 
                    MenuItem("Add database", self.add_database)
                ]
            ], 
            None,
            [
                MenuItem("Database"), [
                    MenuItem(k, callback=self.userclick) for k,v in self.dbs.items()
                ]
            ],
            None,
            MenuItem("Quit Noitation", callback=self.quit_app)
        ])
    
    def update_config(self):
        with open("key.yaml", "w") as f:
            yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)

    def add_api_key(self, menuitem):
        w = rumps.Window("Add your API key",
                         dimensions=(200, 20),
                         cancel=True)
        w.icon = self.icon
        response = w.run()
        if response.clicked:
            val, message = check_api_key(response.text)
            if val: 
                self.config["api_key"] = str(response.text)
                self.update_config()
                self.update_menu()
                show_alert("Succeeded!", "The API key is was verified")
            else:
                show_alert("Failure", "The API key is not working")

    def add_database(self, menuitem):
        w = rumps.Window("Add database", 
                         default_text="Database name:\nDatabase ID:", 
                         dimensions=(200, 40), 
                         cancel=True)
        w.icon = self.icon
        response = w.run()
        if response.clicked:
            db_name = response.text.split("\n")[0].split(":")[1].strip()
            db_id = response.text.split("\n")[1].split(":")[1].strip()
            if db_name == "": show_alert("Failure", "Database name is empty")
            elif db_id == "": show_alert("Failure", "Database ID is empty")
            if not "api_key" in self.config: show_alert("Failure", "Please set API key first")
            val, message = check_notion_db_id(db_id, self.config.get("api_key", ""))
            if val:
                if not "database" in self.config: 
                    self.config["database"] = {db_name: db_id}
                else:
                    self.config["database"][db_name] = db_id
                self.update_config()
                self.update_menu()
                show_alert("Succeeded!", "The Database ID was verified")
            else:
                show_alert("Failure", f"The database ID {db_id} was not found")

    def userclick(self, menuitem):
        db = self.dbs[menuitem.title]
        key = self.config.get("api_key", "")
        props_db = get_notion_db(db, key)
        n = 0
        for entry in props_db:
            doi = entry["doi"]["url"]
            title = entry["Title"]["title"]
            if (doi is not None) and len(title) == 0:
                paper_info = get_paper_info(doi)
                push_notion_db(paper_info, db, key)
                n += 1
        if n > 0:
            show_alert("Done!", f"Filled information about {n} entries") 
        else:
            show_alert("Done!", "No update")

    def quit_app(self, menuitem):
        rumps.quit_application()
 
if __name__ == "__main__":
    app = NotionCitationApp()
    app.run()