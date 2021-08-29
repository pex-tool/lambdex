import hashlib

import flask
import requests


def handler(request):
    request_json = request.get_json()
    url = request_json.get("url")
    if not url:
        print("No URL provided!")
        return {}

    print("%s sha256:%s" % (url, hashlib.sha256(requests.get(url).content).hexdigest()))
    return {
        "url": flask.escape(url),
        "sha256": hashlib.sha256(requests.get(url).content).hexdigest(),
    }
