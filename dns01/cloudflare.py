# coding=utf-8

import requests

# 实测CF同一名称不同值的TXT记录视为多条TXT记录
# 请求创建不同值的TXT记录不会报错 同样值才会报已存在

def _getid(api_param,name):
    url = "https://api.cloudflare.com/client/v4/zones/{}/dns_records?name={}&type=TXT".format(api_param['CF_Zone_ID'], name)
    auth = {"Authorization": "Bearer {}".format(api_param['CF_Token'])}
    r = requests.get(url, headers=auth)
    if r.status_code != 200:
        return False
    data = r.json()
    if data["success"] == True:
        id_list = []
        for i in data["result"]:
            id_list.append(i["id"])
        return id_list
    else:
        return False

def add(api_param, record):
    url = "https://api.cloudflare.com/client/v4/zones/{}/dns_records".format(api_param['CF_Zone_ID'])
    auth = {"Authorization": "Bearer {}".format(api_param['CF_Token'])}
    body = {
        "type": "TXT",
        "name": record[0],
        "content": record[1],
        "ttl": 120
    }
    r = requests.post(url, headers=auth, json=body)
    if r.status_code == 200 and r.json()["success"]:
        return True
    elif r.status_code == 400 and r.json()["errors"][0]["code"] == 81057:
    # 名称和值都相同报已存在 可能是上次流程中断
        return True
    else:
        return False

def rm(api_param, record):
    record_id = _getid(api_param, record[0])
    if not record_id:
        return False
    for i in record_id:
        url = "https://api.cloudflare.com/client/v4/zones/{}/dns_records/{}".format(api_param['CF_Zone_ID'], i)
        auth = {"Authorization": "Bearer {}".format(api_param['CF_Token'])}
        r = requests.delete(url, headers=auth)
        if r.status_code != 200:
            return False
        if r.json()["success"] != True:
            return False
    return True