import hashlib

import requests


def handler(event, context):
    url = event["url"]
    print("%s sha256:%s" % (url, hashlib.sha256(requests.get(url).content).hexdigest()))


def other_handler(event, context):
    print("Other handler invoked")
