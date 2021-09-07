# coding=utf-8

from acme_util import load_config_Data, get_config_Data
from acme_class import DNS01, Notify, Order

def renew(solo=None,cron=False):
    if not load_config_Data():
        return False
    
    DNS01_LIST = {}
    try:
        for item in get_config_Data('dns01'):
            obj = DNS01(item)
            if not obj.precheck():
                raise
            DNS01_LIST[item['name']] = obj
    except:
        print "DNS-01 Param Not Complete!"
        return False

    NOTIFY_LIST = {}
    try:
        for item in get_config_Data('notify'):
            obj = Notify(item)
            if not obj.precheck():
                raise
            NOTIFY_LIST[item['name']] = obj
    except:
        print "Notify Param Not Complete!"
        return False

    ORDER_LIST = {}
    try:
        for item in get_config_Data('order'):
            obj = Order(item)
            if not obj.precheck(DNS01_LIST,NOTIFY_LIST):
                raise
            ORDER_LIST[item['name']] = obj
    except:
        print "Order Param Not Complete!"
        return False

    # solo option
    if solo:
        try:
            if not ORDER_LIST[solo].renew():
                raise
        except:
            return False
    
    error_flag = False
    # cron option
    for o in ORDER_LIST.values():
        if not o.renew(cron):
            error_flag = True

    return not error_flag