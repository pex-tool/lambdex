import hashlib

import flask
import requests


def handler(request: flask.Request):
    request_json = request.get_json()
    url = request_json["url"]
    print("%s sha256:%s" % (url, hashlib.sha256(requests.get(url).content).hexdigest()))

    return {
        "url": flask.escape(url),
        "sha256": hashlib.sha256(requests.get(url).content).hexdigest(),
    }
