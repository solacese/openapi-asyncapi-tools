import logging
import json
import re

from ruamel.yaml import YAML

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
    ApplicationDomain = {}
    applicationDomainId = None
    Application = {}
    applicationId = None
    Schemas = {}
    Events = []
    
    _refSchemaRe = re.compile(r'\#\/components\/schemas/([^\/]+)$')

    def importOpenAPISpec(self, spec_path, domain, application):
        self.spec_path = spec_path
        self.domainName = domain
        self.appName = application
        
        with open(spec_path) as f:
            text_context = f.read()
            self.spec = YAML().load(text_context)

        version = self.spec.get("openapi")
        if not version:
            logging.error("There is no 'openapi' filed in {}".format(spec_path))
            raise SystemExit

        if int(version.split(".")[0]) < 3:
            logging.error("The open api version of '{}' is {}, must be 3.x.".format(spec_path, version))
            raise SystemExit

        self.ApplicationDomain = {
            "name": domain
        }

        self.Application = {
            "name": application
        }

        self.generate_ep_objects()


    def generate_ep_objects(self):
        for path, path_item in self.spec["paths"].items():
            for method in self.http_methods:
                if method not in path_item: continue
                operation = path_item.get(method)
                operationId = operation.get("operationId")
                event = {
                    "schemaName": None,
                    "payload": {
                        "applicationDomainId": "TestApp",
                        "name": operationId,
                        "description": operation.get("description", ""),
                        "topicName": method.upper()+path,
                    }
                }

                schemaName = self.extract_schema_from_operation(operation)
                if schemaName : event["schemaName"]=schemaName
                self.Events.append(event)

        print(json.dumps(self.Schemas, indent=2))
        print(json.dumps(self.Events, indent=2))

    def extract_schema_from_operation(self, operation):
        schemaName = None
        content = operation.get("requestBody", {'content':{}}).get("content")
        jsonkeys = [k for k in content.keys() if k.startswith("application/json")]
        if len(jsonkeys) > 0:
            # only extract the first matched json schema
            schema = content.get(jsonkeys[0]).get("schema")
            if schema.get("$ref"):
                # Reference Object
                schemaName = self._refSchemaRe.search(schema.get("$ref")).group(1)
                if not self.Schemas.get(schemaName): 
                    self.Schemas[schemaName]={
                        "id": None,
                        "payload": {
                            "contentType": "JSON",
                            "content": json.dumps(schema),
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