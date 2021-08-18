#!/usr/bin/env python
#coding=utf-8

# acme_tea --only-init 只执行 newAccount
# acme_tea --solo-order xxx 指定订单执行
# acme_tea --no-cron 全部订单执行一次不做定时任务
# acme_tea --solo-order xxx --no-cron 指定订单执行一次不做定时任务

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
    cron = True

    if len(sys.argv) != 0:
        if sys.argv[1] == '--only-init':
            Normal_Exit()

        if sys.argv[1] == '--solo-order':
            solo = sys.argv[2]
        if '--no-cron' in sys.argv:
            cron = False
    
    acme_renew.renew(solo,cron)