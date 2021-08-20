#!/usr/bin/env python
#coding=utf-8

# acme_tea --only-init 只执行 newAccount
# acme_tea --solo-order xxx 指定订单执行
# acme_tea --cron 定时任务调用

import sys
import acme_init
import acme_renew

def Normal_Exit():
    import acme_req
    acme_req.ACME_REQ.save_http_log()
    sys.exit(0)

if __name__ == '__main__':
    acme_init.init()

    solo = None
    cron = False

    if len(sys.argv) > 1:
        if sys.argv[1] == '--only-init':
            Normal_Exit()

        if sys.argv[1] == '--solo-order':
            solo = sys.argv[2]
 
        if sys.argv[1] == '--cron':
            cron = True
    
    acme_renew.renew(solo,cron)
    Normal_Exit()