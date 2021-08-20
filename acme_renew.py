# coding=utf-8

from acme_util import load_config_Data, get_config_Data, dns01_txt, dns01_plugin_dir, result_dir
from acme_req import ACME_REQ, ACME_Order, ACME_AuthZ, ACME_Chall, ACME_Finalize, ACME_Cert
import os
from importlib import import_module
import time
import datetime

# VERIFY_RETRY_NUM = 5
CHALLENGE_DELAY = 60
NEAR_EXPIRE_MIN = 6
DEPLOY_DEFAULT_TIMEOUT = 10

def find_dns01(name):
    for dns01 in get_config_Data('dns01'):
        if dns01['name'] == name:
            return dns01
    return None

def add_txt_record(dns01_conf,domain,token):
    if not os.path.exists(os.path.join(dns01_plugin_dir, dns01_conf['type']+'.py')):
        print "Selected DNS-01 Plugin Program Not Exist!"
        return False

    dns01_plugin = import_module('dns01.'+dns01_conf['type'])

    record = ("_acme-challenge."+domain, dns01_txt(token))
    if dns01_plugin.add(dns01_conf['spec'], record):
        return True
    else:
        print "DNS-01 Plugin Add record Fail!"
        return False

def rm_txt_record(dns01_conf,domain):
    dns01_plugin = import_module('dns01.'+dns01_conf['type'])

    record = ("_acme-challenge."+domain, "")
    if dns01_plugin.rm(dns01_conf['spec'], record):
        pass
    else:
        print "Warn: DNS-01 Plugin Remove record Fail"
        # 删除解析记录即使失败提示即可不必退出

def Unknow_Error():
    print "Unknow Error, Exception Exit."
    ACME_REQ.Exception_Exit()

def init_domain_key(domains,order_dir):
    print "Generate New Domain Private Key & CSR"
    os.mkdir(order_dir)
    key_path = os.path.join(order_dir, 'domain')
    csr_path = os.path.join(order_dir, 'domain.csr')
    os.popen("openssl ecparam -name prime256v1 -genkey -out {}".format(key_path))

    if len(domains) > 1:
        # multi domains
        # FUCK works with openssl < 1.1.1
        openssl_config = "[ req_distinguished_name ]\n[ req ]\ndistinguished_name = req_distinguished_name\nreq_extensions = v3_req\n[ v3_req ]\n\n"
        alt = "\nsubjectAltName=DNS:"
        alt += ",DNS:".join(domains)
        openssl_config += alt

        # FUCK!!!FUCK!!!FUCK!!!
        tmpfile_path = "/tmp/openssl.cnf"
        with open(tmpfile_path, 'w') as f:
            f.write(openssl_config)

        os.popen("openssl req -new -sha256 -key {} -subj \"/\" -config {} > {}".format(key_path, tmpfile_path, csr_path))
    else:
        # single domain
        os.popen("openssl req -new -sha256 -key {} -subj \"/CN={}\" > {}".format(key_path, domains[0], csr_path))

def cert_date_check(cert_path):
    raw = os.popen("openssl x509 -in {} -noout -enddate".format(cert_path)).read()
    raw_split = raw.split('=')[1].split()
    maked = "{}-{}-{}".format(raw_split[-2], raw_split[0], raw_split[1])
    expire = datetime.datetime.strptime(maked, "%Y-%b-%d")

    today = datetime.datetime.today()
    if expire > today:
        delta = expire - today
        return delta.days > NEAR_EXPIRE_MIN
    else:  # expire long ago ....
        return False


def renew(solo=None,cron=True):
    # solo & cron 还没有做
    if not load_config_Data():
        ACME_REQ.Exception_Exit()
    
    for order in get_config_Data('order'):
        if not ( order.has_key('name') and order.has_key('domains') and order.has_key('use_dns01') ):
            print "Order Param Not Complete!"
            ACME_REQ.Exception_Exit()

        dns01_conf = find_dns01(order['use_dns01'])
        if not dns01_conf:
            print "Selected DNS-01 Config Not Exist!"
            ACME_REQ.Exception_Exit()

        order_dir = os.path.join(result_dir, order['name'])
        cert_path = os.path.join(order_dir, 'fullchain.crt')
        # PreCheck
        if os.path.exists(cert_path):
            if cert_date_check(cert_path):
                print "Certificate Not near expire for Order [{}], Skip.".format(order['name'])
                print "( If want to Force Update, Delete the specified directory in result )"
                continue  # 跳过流程 继续执行下一订单

        print "Start Order -- {}".format(order['name'])
        order_obj = ACME_Order(1, domains=order['domains'])
        result = order_obj.stable_return()

        if result["status"] == "pending":
            normal_order(result, dns01_conf)
        elif result["status"] == "ready":  # 处理上次中断的订单
            print "Order Ready Before :) Continue."
        else:
            Unknow_Error()
        finalize_url = result["finalize"]

        csr_path = os.path.join(order_dir, 'domain.csr')
        if os.path.exists(csr_path):
            print "Order is used, Use last CSR."
        else:
            init_domain_key(order['domains'], order_dir)

        print "Complete Finalize, Submit CSR"
        finalize_obj = ACME_Finalize(1, finalize_url, csr_path)
        result = finalize_obj.stable_return()
        if result["status"] != "valid":
            Unknow_Error()
        cert_url = result["certificate"]

        print "Receive Certificate And Save."
        cert_obj = ACME_Cert(0,cert_url)
        result = cert_obj.stable_return()
        fullchain_path = cert_path
        with open(fullchain_path, 'w') as f:
            f.write(result)

        print "ACME Done."

        if order.has_key('deploy'):
            key_path = os.path.join(order_dir, 'domain')
            deploy_process(order['deploy'], key_path, cert_path)


def normal_order(result,dns01_conf):
    order_url = result['url']
    authz_url_list = result["authorizations"] # 注意这里是个挑战列表

    print "Authorization Count {}".format(len(authz_url_list))
    for authz_url in authz_url_list:
        print "Start Authorization {}".format(authz_url.split('/')[-1])
        authz_obj = ACME_AuthZ(0,authz_url)
        result = authz_obj.stable_return()
        for chall in result["challenges"]:
            if chall["type"] == "dns-01":
                chall_url = chall["url"]
                chall_token = chall["token"]
        chall_domain = result["identifier"]["value"]

        if not add_txt_record(dns01_conf,chall_domain,chall_token):
            ACME_REQ.Exception_Exit()

        print "Wait {} second, Then Request Challenge".format(CHALLENGE_DELAY)
        time.sleep(CHALLENGE_DELAY)
        ACME_Chall(1,chall_url)

        # Fuck Let's Encrypt!!!!
        # 实测 Let's Encrypt 挑战失败直接invalid 导致整个订单invalid 没有意义
        # for i in range(VERIFY_RETRY_NUM):
        #     wait_second = 5*(1+i)
        #     print "Wait {} second, Then verify Challenge".format(wait_second)
        #     time.sleep(wait_second)

        #     chall_obj = ACME_Chall(0,chall_url)
        #     result = chall_obj.stable_return()
        #     if result["status"] == "valid":
        #         break
        #     elif result["status"] == "processing":
        #         continue
        #     else:
        #         Unknow_Error()

        print "Verify Challenge."
        chall_obj = ACME_Chall(0,chall_url)
        result = chall_obj.stable_return()
        if result["status"] != "valid":
            Unknow_Error()

        print "Verify Authorization {}".format(authz_url.split('/')[-1])
        authz_obj = ACME_AuthZ(0,authz_url)
        result = authz_obj.stable_return()
        if result["status"] != "valid":
            Unknow_Error()

        # 删除解析记录即使失败提示即可不必退出
        rm_txt_record(dns01_conf,chall_domain)

    print "Verify Order whether Ready"
    order_obj = ACME_Order(0, url=order_url)
    result = order_obj.stable_return()
    if result["status"] != "ready":
        Unknow_Error()

def deploy_process(deploy_list,key_path,cert_path):
    for deploy in deploy_list:
        if deploy.has_key('copy-file'):
            target = deploy['copy-file']
            os.popen("/bin/cp -f {} {}".format(key_path,target['key-path']))    # /bin/cp 防止 alias cp='cp -i' 干扰
            os.popen("/bin/cp -f {} {}".format(cert_path,target['cert-path']))  # /bin/cp 防止 alias cp='cp -i' 干扰
        if deploy.has_key('link-file'):
            target = deploy['link-file']
            os.popen("ln -sf {} {}".format(key_path,target['key-path']))
            os.popen("ln -sf {} {}".format(cert_path,target['cert-path']))
        if deploy.has_key('command'):
            for command in deploy['command']:
                command = command.replace("{KEY-PATH}", key_path)
                command = command.replace("{CERT-PATH}", cert_path)
                os.popen("timeout {} {}".format(DEPLOY_DEFAULT_TIMEOUT, command))  # 不接受执行结果 And 超时控制
        print "deploy task [{}] End.".format(deploy['name'])