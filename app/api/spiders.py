import requests
from config.const import make_url

def get_deamon():
    call = requests.get(make_url('daemonstatus.json'))
    return call.status_code, call.json()

def get_projects():
    call = requests.get(make_url('listprojects.json'))
    return call.status_code, call.json()

def get_spiders():
    call = requests.get(make_url('listspiders.json?project='))
    return call.status_code, call.json()