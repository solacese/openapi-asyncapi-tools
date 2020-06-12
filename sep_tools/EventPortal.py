import logging
import json
import re

import yaml
from .util import *

class EventPortal:
    spec = {}
    http_methods = [
        'get', 
        'put', 
        'post', 
        'delete', 
        'options', 
        'head', 
        'patch', 
        'trace']
    ApplicationDomains = {}
    Applications = {}
    Schemas = {}
    Events = {}
    
    _refSchemaRe = re.compile(r'\#\/components\/schemas/([^\/]+)$')
    _base_url = "https://solace.cloud"


    def __init__(self, token):
        super().__init__()
        self.token = token

    def importOpenAPISpec(self, spec_path, domain, application):
        self.spec_path = spec_path
        self.domainName = domain
        self.appName = application
        self.ApplicationDomains[domain]={
            "payload":{
                "name": domain,
                "enforceUniqueTopicNames": True,
                "topicDomain": "",
            }
        }
        self.Applications[application]={
            "payload":{
                "name": application,
            }
        }
        
        with open(spec_path) as f:
            text_context = f.read()
            self.spec = yaml.safe_load(text_context)

        version = self.spec.get("openapi")
        if not version:
            logging.error("There is no 'openapi' filed in {}".format(spec_path))
            raise SystemExit

        if int(version.split(".")[0]) < 3:
            logging.error("The open api version of '{}' is {}, must be 3.x.".format(spec_path, version))
            raise SystemExit

        self.generate_ep_objects()
        self.check_existed_objects()
        self.create_all_objects()
        

    def generate_ep_objects(self):
        for path, path_item in self.spec["paths"].items():
            for method in self.http_methods:
                if method not in path_item: continue
                operation = path_item.get(method)
                operationId = operation.get("operationId")
                event = {
                    "schemaName": None,
                    "payload": {
                        "name": operationId,
                        "description": operation.get("description", ""),
                        "topicName": method.upper()+path,
                    }
                }

                schemaName = self.extract_schema_from_operation(operation)
                if schemaName : event["schemaName"]=schemaName
                self.Events[operationId]=event
        
    def extract_schema_from_operation(self, operation):
        schemaName = None
        content = operation.get("requestBody", {'content':{}}).get("content")
        jsonkeys = [k for k in content.keys() if k.startswith("application/json")]
        if len(jsonkeys) > 0:
            # only extract the first matched json schema
            schema = content.get(jsonkeys[0]).get("schema")
            if schema.get("$ref"):
                # Reference Object like #/components/schemas/CouponRequest
                schemaName = self._refSchemaRe.search(schema.get("$ref")).group(1)
                if not self.Schemas.get(schemaName): 
                    self.Schemas[schemaName]={
                        "id": None,
                        "payload": {
                            "contentType": "JSON",
                            "content": json.dumps(self.get_component_schema(schemaName)),
                            "name": schemaName,
                        }
                    }
            else:
                # Inline Schema Object
                schemaName = operation.get("operationId")+"_schema"
                self.Schemas[schemaName]={
                    "id": None,
                    "payload": {
                        "contentType": "JSON",
                        "content": json.dumps(schema),
                        "name": schemaName,
                    }
                }
        return schemaName

    def get_component_schema(self, schemaName):
        payload = self.spec["components"]["schemas"][schemaName]
        self.dfs_ref_dict(payload)

        return payload

    def dfs_ref_dict(self, payload):
        for key, value in payload.items():
            if type(value) is dict:
                if value.get("$ref"):
                    # Reference Object
                    schemaName = self._refSchemaRe.search(value.get("$ref")).group(1)
                    payload[key] = self.get_component_schema(schemaName)
                else:
                    self.dfs_ref_dict(value)


    def check_existed_objects(self):
        to_check = {
            "applicationDomains": self.ApplicationDomains,
            "applications": self.Applications,
            "schemas": self.Schemas,
            "events": self.Events,
        }

        logging.info("Checking existed objects ...")
        isError = False
        applicationDomainId = None
        for coll_name, coll_objs in to_check.items():
            coll_url = self._base_url+"/api/v1/eventPortal/"+coll_name
            for obj_name, obj in coll_objs.items():
                print(".", end="", flush=True)
                thisAppDomainId = None
                url = coll_url+"?name="+obj_name
                rJson = rest("get", url, token=self.token)
                if len(rJson["data"]) > 0:
                    obj["id"] = rJson["data"][0]["id"]
                    obj["applicationDomainId"] = rJson["data"][0].get("applicationDomainId")
                    if coll_name == "applicationDomains":
                        applicationDomainId = obj["id"]
                    elif obj["applicationDomainId"] != applicationDomainId:
                        logging.error("{} '{}' already exists with another Application Domain[id:{}]".\
                            format(coll_name[:-1].capitalize(), obj_name, thisAppDomainId))
                        isError = True
                    else:
                        logging.warn("{} '{}' already exists".format(coll_name[:-1].capitalize(), obj_name))

        print()
        if isError: 
            raise SystemExit


    def create_all_objects(self):
        # 1. create application domain
        self.create_colls("applicationDomains", self.ApplicationDomains)
        applicationDomainId = self.ApplicationDomains[self.domainName]["id"]

        # 2. create application
        self.Applications[self.appName]["payload"]["applicationDomainId"] = applicationDomainId            
        self.create_colls("applications", self.Applications)
        applicationId = self.Applications[self.appName]["id"]

        # 3. create all schemas
        for s, v in self.Schemas.items():
            if not v.get("id"):
                v["payload"]["applicationDomainId"] = applicationDomainId
        self.create_colls("schemas", self.Schemas)

        # 4. create all events
        for e, v in self.Events.items():
            if not v.get("id"):
                event = v["payload"]
                event["applicationDomainId"] = applicationDomainId
#                event["consumedApplicationIds"] = [applicationId]
                if v["schemaName"] in self.Schemas:
                    event["schemaId"] = self.Schemas[v["schemaName"]]["id"]

        self.create_colls("events", self.Events)

        # 5. update the application to consume all events
        consumedEventIds = [ v["id"] for e, v in self.Events.items() ]
        data_json = {"consumedEventIds": consumedEventIds}
        url = self._base_url+"/api/v1/eventPortal/applications/"+applicationId
        rJson = rest("patch", url, data_json=data_json, token=self.token)
        logging.info("Application '{}' subscribes on all events successfully.".\
            format(self.appName))


    def create_colls(self, coll_name, coll_objs):
        coll_url = self._base_url+"/api/v1/eventPortal/"+coll_name
        for obj_name, obj_value in coll_objs.items():
            if obj_value.get("id"):
                continue
            # expected_code=201 Created.
            # The newly saved object is returned in the response body.
            rJson = rest("post", coll_url, data_json=obj_value["payload"],\
                expected_code=201, token=self.token)
            obj_value["id"] = rJson["data"]["id"]
            logging.info("{} '{}'[{}] created successfully".\
                format(coll_name[:-1].capitalize(), obj_name, obj_value["id"]))
