import requests

class visualAPIConnection():
    def __init__(self):
        self.url = "https://"
    
    def postData(self, data):
        response = requests.post(url=self.url, data=data)
        response.status_code
        response.reason

    def postJson(self, json):
        response = requests.post(url=self.url, json=json, stream=True)
        response.status_code
        response.reason
        response.c