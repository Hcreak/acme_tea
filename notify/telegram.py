# coding=utf-8

import requests

def _escape(text):
    text = text.replace('_','\_')
    text = text.replace('*','\*')
    text = text.replace('`','\`')
    text = text.replace('[','\[')
    return text

def normal(api_param, order_info):
    content = '''
*ACME_TEA notify - Normal*

*{}*

```
{}
```
    '''.format(
        _escape(order_info['name']),
        _escape('\n'.join(order_info['domains']))
    )

    payload = {'chat_id':api_param['TG_BOT_ChatID'], 'text':content, 'parse_mode':'Markdown'}
    r = requests.post("https://api.telegram.org/bot{}/sendMessage".format(api_param['TG_BOT_Token']), data=payload)
    return r.json()['ok']

def error(api_param, order_info):
    content = '''
*ACME_TEA notify - Error*

*{}*

{}
    '''.format(
        _escape(order_info['name']),
        _escape(order_info['error'])
    )

    payload = {'chat_id':api_param['TG_BOT_ChatID'], 'text':content, 'parse_mode':'Markdown'}
    r = requests.post("https://api.telegram.org/bot{}/sendMessage".format(api_param['TG_BOT_Token']), data=payload)
    return r.json()['ok']