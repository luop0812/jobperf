import os
import yaml

path = os.path.realpath(os.path.dirname(__file__))

with open(path+'/config.yml', 'r') as cf:
    config = yaml.safe_load(cf)

with open(path+'/uuid.yml', 'r') as uf:
    uuids = yaml.safe_load(uf)

with open(path+'/id.yml', 'r') as idf:
    ids = yaml.safe_load(idf)
