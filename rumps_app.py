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

def userclick(app, menuitem):
    db = config["tables"][menuitem.title]
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


class NotionCitationApp(App):

    def __init__(self):
        super(NotionCitationApp, self).__init__("NotionCitationApp")
        self.menu=[
            MenuItem(k, callback=self.set_table(key=k, id=v)) for k,v in config["tables"].items()
        ]
        self.table_key = list(config["tables"].keys())[0]
        self.table_id = config["tables"][self.table_key]
        self.icon = "static/logo.png"
    
    for k,v in config["tables"].items():
        userclick = clicked(k)(userclick)

    def set_table(self, key, id):
        self.table_key = key
        self.table_id = id
 
if __name__ == "__main__":
    app = NotionCitationApp()
    app.run()