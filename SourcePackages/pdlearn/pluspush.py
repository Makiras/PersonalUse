import json
import requests  # 导入依赖库


class PlusPushHandler:
    def __init__(self, token, topic=''):
        self.token = token
        self.topic = topic

    def ftmsgsend(self, msgurl):

        url = "http://www.pushplus.plus/send"
        headers = {"Content-Type": "application/json"}  # 定义数据类型
        data = {
            "token": self.token,
            "title": "学习需要重新登陆",
            "content": "<img src='"+msgurl+"'/>"
        }

        res = requests.post(url, data=json.dumps(data),
                            headers=headers)  # 发送post请求
        print(res.text)

    def fttext(self, text):
        url = "http://www.pushplus.plus/send"
        headers = {"Content-Type": "application/json"}  # 定义数据类型
        data = {
            "token": self.token,
            "title": "学习需要你注意",
            "content": text,
            "topic": self.topic,
            "template": "markdown"
        }

        res = requests.post(url, data=json.dumps(data),
                            headers=headers)  # 发送post请求
        print(res.text)
