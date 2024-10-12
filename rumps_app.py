import os
import sys
import requests
import yaml
from rumps import *
from autofill import *
import subprocess

with open("key.yaml") as f: config = yaml.safe_load(f)

def show_alert(title, message):
    script = f'display dialog "{message}" with title "{title}"'
    subprocess.run(['osascript', '-e', script])

class NotionCitationApp(App):

    def __init__(self):
        super(NotionCitationApp, self).__init__("NotionCitationApp")
        self.menu = [
            [
                MenuItem("Settings"), [
                    MenuItem("API key", self.add_api_key), 
                    MenuItem("Add database", )
                ]
            ], 
            None,
            [
                MenuItem("Database"), [
                    MenuItem(k, callback=self.userclick) for k,v in config["database"].items()
                ]
            ],
            None
        ]
        self.table_key = list(config["database"].keys())[0]
        self.table_id = config["database"][self.table_key]
        self.icon = "static/logo.png"
    
    def add_api_key(self, menuitem):
        response = rumps.Window('Add your API key', dimensions=(200, 20)).run()

    def userclick(self, menuitem):
        db = config["database"][menuitem.title]["id"]
        key = config["api_key"]
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
 
if __name__ == "__main__":
    app = NotionCitationApp()
    app.run()