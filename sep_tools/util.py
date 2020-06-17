import json
import requests
import logging

def rest(verb, url, data_json=None, expected_code=200, token=None):
    headers={"content-type": "application/json"}
    if token : headers["Authorization"] = "Bearer "+token
    str_json = json.dumps(data_json) if data_json != None else None
    r = getattr(requests, verb)(url, headers=headers,
        data=(str_json))
    if (r.status_code != expected_code):
        logging.error("{} on {} returns {}".format(verb.upper(), url, r.status_code))
        if data_json: print(json.dumps(data_json, indent=2))
        print(r.text)
        raise SystemExit

    return r.json()
