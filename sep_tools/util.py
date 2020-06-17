import json
import requests
import logging

HTTP_METHODS = [
    'get', 
    'put', 
    'post', 
    'delete', 
    'options', 
    'head', 
    'patch', 
    'trace']

def rest(verb, url, data_json=None, expected_code=200, params=None, token=None):
    headers={"content-type": "application/json"}
    if token : headers["Authorization"] = "Bearer "+token
    str_json = json.dumps(data_json) if data_json != None else None
    r = getattr(requests, verb)(url, headers=headers,
        data=(str_json), params=params)
    if (r.status_code != expected_code):
        logging.error("{} on {} returns {}".format(verb.upper(), url, r.status_code))
        if data_json: print(json.dumps(data_json, indent=2))
        print(r.text)
        raise SystemExit

    return r.json()

def safeget(dct, *keys):
    for key in keys:
        try:
            dct = dct[key]
        except KeyError:
            return None
    return dct


def generateOpenAPISpec(app_name, description, event_list, schema_list):
    # 1. init the spec
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": app_name,
            "description": description,
            "version": "1.0.0"
        },
        "components": {
            "schemas": {}
        },
        "paths": {}
    }
    
    # 2. generate all schemas
    schemas = spec["components"]["schemas"]
    for es in schema_list:
        if es["contentType"]=="JSON" and es["content"]:
            # only support JSON schema
            schemas[es["name"]] = json.loads(es["content"])

    # 3. generate all path
    for e in event_list:
        path = e["topicName"]
        http_method = path.split("/")[0].lower()
        if http_method in HTTP_METHODS:
            # This is a event topic generated from REST url
            path = path[len(http_method):]
        else:
            # path of OpenAPI MUSH start with "/"
            http_method = "post"
            path = "/"+path
        
        if path not in spec["paths"]: spec["paths"][path] = {}
        pathItem = spec["paths"][path]

        operation = {
            "operationId": e["name"],
            "description": e["description"],
            # TODO: responses is required for operation object of Open API
            # but event of Event Portal do not have such information
            "responses":{},
        }

        if e["schemaId"] != None:
            ep_schema = [s for s in schema_list if s["id"]==e["schemaId"]][0]
            if safeget(spec, "components", "schemas", ep_schema["name"]):
                operation["requestBody"] = {
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/"+ep_schema["name"]
                            }
                        }
                    }
                }
                pathItem[http_method] = operation

    # 4. output the spec
    print(json.dumps(spec, indent=2))
