import requests
import json

class BaseApi:
    def __init__(self):
        self.base_url = "https://jsonplaceholder.typicode.com"
        self.headers = {"Content-Type": "application/json"}

    def send_request(self, method, url, **kwargs):
        """通用请求发送方法"""
        full_url = self.base_url + url
        try:
            response = requests.request(
                method=method,
                url=full_url,
                headers=self.headers,
                timeout=60,
                **kwargs
            )
            return response
        except Exception as e:
            print(f"请求异常: {e}")
            raise

    def get(self, url, params=None, **kwargs):
        return self.send_request("GET", url, params=params, **kwargs)

    def post(self, url, data=None, json=None, **kwargs):
        return self.send_request("POST", url, data=data, json=json, **kwargs)

    def put(self, url, data=None, json=None, **kwargs):
        return self.send_request("PUT", url, data=data, json=json, **kwargs)

    def delete(self, url, **kwargs):
        return self.send_request("DELETE", url, **kwargs)