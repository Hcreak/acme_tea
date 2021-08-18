# coding=utf-8

from acme_util import config_Data, load_config_Data, dns01_txt
from acme_req import ACME_REQ

def renew(solo=None,cron=True):
    if not load_config_Data():
        ACME_REQ.Exception_Exit()
    
    for order in config_Data['order']:
        pass        
