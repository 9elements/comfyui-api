import json

def load_workflow(workflow_path):
  file = open(workflow_path)
  workflow = json.load(file)
  workflow = json.dumps(workflow)

  return workflow
