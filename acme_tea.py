#!/usr/bin/env python
#coding=utf-8

# acme_tea --only-init 只执行 newAccount

import sys
import acme_init
import acme_req

def Normal_Exit():
    acme_req.ACME_REQ.save_http_log()
    sys.exit(0)

if __name__ == '__main__':
    acme_init.init()
    if sys.argv[1] == '--only-init':
        Normal_Exit()

