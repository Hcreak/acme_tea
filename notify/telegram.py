# coding=utf-8

import requests

def _escape(text):
    text = text.replace('_','\_')
    text = text.replace('*','\*')
    text = text.replace('`','\`')
    text = text.replace('[','\[')
    return text

def normal(api_param, order_info, expire):
    domains_str = ''
    for domain in order_info['domains']:
        item = '`'+_escape(domain)+'`\n'
        domains_str += item

    content = '''
*ACME_TEA notify - Normal*

*{}*

{}

*Expire* {}
    '''.format(
        _escape(order_info['name']),
        domains_str,
        _escape(expire)
    )

    payload = {'chat_id':api_param['TG_BOT_ChatID'], 'text':content, 'parse_mode':'Markdown'}
    requests.post("https://api.telegram.org/bot{}/sendMessage".format(api_param['TG_BOT_Token']), data=payload)

def error(api_param, order_info, error):
    content = '''
*ACME_TEA notify - Error*

*{}*

{}
    '''.format(
        _escape(order_info['name']),
        _escape(error)
    )

    payload = {'chat_id':api_param['TG_BOT_ChatID'], 'text':content, 'parse_mode':'Markdown'}
    requests.post("https://api.telegram.org/bot{}/sendMessage".format(api_param['TG_BOT_Token']), data=payload)