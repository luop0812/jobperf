import yaml

with open('config.yml', 'r') as cf:
    config = yaml.safe_load(cf)

with open('uuid.yml', 'r') as uf:
    uuids = yaml.safe_load(uf)

with open('id.yml', 'r') as idf:
    ids = yaml.safe_load(idf)
