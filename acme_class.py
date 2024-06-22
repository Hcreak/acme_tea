# coding=utf-8

from acme_util import dns01_plugin_dir, dns01_txt, notify_plugin_dir, init_domain_key, result_dir, path_check, get_ARI_CertID
from acme_req import ACME_Order, ACME_AuthZ, ACME_Chall, ACME_Finalize, ACME_Cert, ARI_Req
import os
from importlib import import_module
import time
from datetime import datetime

class DNS01():
    def __init__(self,info):
        self.name = info['name']
        self.type = info['type']
        self.spec = info['spec']
    
    def precheck(self):
        if os.path.exists(os.path.join(dns01_plugin_dir, self.type+'.py')):
            self.plugin = import_module('dns01.'+self.type)
            return True
        else:
            print "DNS-01 Plugin Program Not Exist!"
            return False

    def add_txt_record(self,domain,token):
        record = ("_acme-challenge."+domain, dns01_txt(token))
        try:
            if self.plugin.add(self.spec, record):
                return True
            else:
                raise
        except:
            print "DNS-01 Plugin Add record Fail!"
            return False

    def rm_txt_record(self,domain):
        record = ("_acme-challenge."+domain, "")
        try:
            if not self.plugin.rm(self.spec, record):
                raise
        except:
            print "Warn: DNS-01 Plugin Remove record Fail"
            # 删除解析记录即使失败提示即可不必退出


class Notify():
    def __init__(self,info):
        self.name = info['name']
        self.type = info['type']
        self.spec = info['spec']

    def precheck(self):
        if os.path.exists(os.path.join(notify_plugin_dir, self.type+'.py')):
            self.plugin = import_module('notify.'+self.type)
            return True
        else:
            print "Notify Plugin Program Not Exist!"
            return False

    def send_notify(self,statu,order_info):
        try:
            if statu:
                if not self.plugin.normal(self.spec,order_info):
                    raise
            else:
                if not self.plugin.error(self.spec,order_info):
                    raise
        except:
            print "Warn: Notify Plugin Send Fail"


# VERIFY_RETRY_NUM = 5
CHALLENGE_DELAY = 60
# NEAR_EXPIRE_MIN = 6
DEPLOY_DEFAULT_TIMEOUT = 10

class Order():
    def __init__(self,info):
        self.name = info['name']
        self.domains = info['domains']
        self.use_dns01 = info['use_dns01']

        if info.has_key('use_notify'):
            self.use_notify = info['use_notify']
        else:
            self.use_notify = None

        if info.has_key('no_cron'):
            self.no_cron = info['no_cron']
        else:
            self.no_cron = False

        if info.has_key('deploy'):
            self.deploy = info['deploy']
        else:
            self.deploy = None

        self.order_dir = os.path.join(result_dir, self.name)
        self.key_path = os.path.join(self.order_dir, 'domain')
        self.cert_path = os.path.join(self.order_dir, 'fullchain.crt')
        self.csr_path = os.path.join(self.order_dir, 'domain.csr')

    def precheck(self, dns01_list, notify_list):
        if not dns01_list.has_key(self.use_dns01):
            print "Selected DNS-01 Config Not Exist!"
            return False
        self.dns01_obj = dns01_list[self.use_dns01]

        if self.use_notify:
            if not notify_list.has_key(self.use_notify):
                print "Selected Notify Config Not Exist!"
                return False
            self.notify_obj = notify_list[self.use_notify]
        return True

    # def _cert_date(self):
    #     raw = os.popen("openssl x509 -in {} -noout -enddate".format(self.cert_path)).read()
    #     raw_split = raw.split('=')[1].split()
    #     maked = "{}-{}-{}".format(raw_split[-2], raw_split[0], raw_split[1])
    #     expire = datetime.datetime.strptime(maked, "%Y-%b-%d")
    #     return expire

    # def cert_date_check(self):
    #     expire = self._cert_date()
    #     today = datetime.datetime.today()
    #     if expire > today:
    #         delta = expire - today
    #         return delta.days > NEAR_EXPIRE_MIN
    #     else:  # expire long ago ....
    #         return False

    # https://letsencrypt.org/2024/04/25/guide-to-integrating-ari-into-existing-acme-clients#
    def ARI_Check(self):
        self.ARI_CertID = get_ARI_CertID(self.cert_path)
        start, _end = ARI_Req(self.ARI_CertID)
        start_datetime = datetime.strptime(start.split('.')[0], "%Y-%m-%dT%H:%M:%S")
        return datetime.utcnow() < start_datetime

    def renew(self,cron=False):
        if cron and self.no_cron:
            return True

        # PreCheck
        if os.path.exists(self.cert_path):
            if self.ARI_Check():
                print "Certificate Not In ARI suggested Window for Order [{}], Skip.".format(self.name)
                print "( If want to Force Update, Delete the specified directory in result )"
                return True # 跳过流程 继续执行下一订单
            print "Start Order (Renew) -- {}".format(self.name)
            order_obj = ACME_Order(1, domains=self.domains, replaces=self.ARI_CertID)
        else:
            print "Start Order -- {}".format(self.name)
            order_obj = ACME_Order(1, domains=self.domains)
        result = order_obj.stable_return()

        if result["status"] == "pending":
            if not self.normal_order(result):
                return False
        elif result["status"] == "ready":  # 处理上次中断的订单
            print "Order Ready Before :) Continue."
        else:
            self.ERROR_EXIT()
            return False
        finalize_url = result["finalize"]

        if os.path.exists(self.csr_path):
            print "Order is used, Use last CSR."
        else:
            init_domain_key(self.domains, self.order_dir)

        print "Complete Finalize, Submit CSR"
        finalize_obj = ACME_Finalize(1, finalize_url, self.csr_path)
        result = finalize_obj.stable_return()
        if result["status"] != "valid":
            self.ERROR_EXIT()
            return False
        cert_url = result["certificate"]

        print "Receive Certificate And Save."
        cert_obj = ACME_Cert(0,cert_url)
        result = cert_obj.stable_return()
        fullchain_path = self.cert_path
        with open(fullchain_path, 'w') as f:
            f.write(result)

        print "ACME Done."
        self.normal_notify()

        if self.deploy:
            self.deploy_process()

    def normal_order(self,order_result):
        order_url = order_result['url']
        authz_url_list = order_result["authorizations"] # 注意这里是个挑战列表

        print "Authorization Count {}".format(len(authz_url_list))
        for authz_url in authz_url_list:
            print "Start Authorization {}".format(authz_url.split('/')[-1])
            authz_obj = ACME_AuthZ(0,authz_url)
            result = authz_obj.stable_return()
            for chall in result["challenges"]:
                if chall["type"] == "dns-01":
                    chall_url = chall["url"]
                    chall_token = chall["token"]
                    break
            chall_domain = result["identifier"]["value"]

            if not self.dns01_obj.add_txt_record(chall_domain,chall_token):
                self.ERROR_EXIT("DNS-01 Plugin Add record Fail!")
                return False

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

            time.sleep(2)
            print "Verify Challenge."
            chall_obj = ACME_Chall(0,chall_url)
            result = chall_obj.stable_return()
            if result["status"] != "valid":
                self.ERROR_EXIT()
                return False

            print "Verify Authorization {}".format(authz_url.split('/')[-1])
            authz_obj = ACME_AuthZ(0,authz_url)
            result = authz_obj.stable_return()
            if result["status"] != "valid":
                if "error" in result:
                    self.ERROR_EXIT("Challenge Error: " + result["error"]["detail"])
                else:
                    self.ERROR_EXIT()
                return False

            # 删除解析记录即使失败提示即可不必退出
            self.dns01_obj.rm_txt_record(chall_domain)

        print "Verify Order whether Ready"
        order_obj = ACME_Order(0, url=order_url)
        result = order_obj.stable_return()
        if result["status"] != "ready":
            self.ERROR_EXIT()
            return False
        return True

    def deploy_process(self):
        for deploy in self.deploy:
            if deploy.has_key('copy-file'):
                target = deploy['copy-file']
                if target.has_key('key-path'):
                    path_check(target['key-path'])
                    os.popen("/bin/cp -f {} {}".format(self.key_path,target['key-path']))    # /bin/cp 防止 alias cp='cp -i' 干扰
                if target.has_key('cert-path'):
                    path_check(target['cert-path'])
                    os.popen("/bin/cp -f {} {}".format(self.cert_path,target['cert-path']))  # /bin/cp 防止 alias cp='cp -i' 干扰
            if deploy.has_key('link-file'):
                target = deploy['link-file']
                if target.has_key('key-path'):
                    path_check(target['key-path'])
                    os.popen("ln -sf {} {}".format(self.key_path,target['key-path']))
                if target.has_key('cert-path'):
                    path_check(target['cert-path'])
                    os.popen("ln -sf {} {}".format(self.cert_path,target['cert-path']))
            if deploy.has_key('command'):
                for command in deploy['command']:
                    command = command.replace("{KEY-PATH}", self.key_path)
                    command = command.replace("{CERT-PATH}", self.cert_path)
                    os.popen("timeout {} {}".format(DEPLOY_DEFAULT_TIMEOUT, command))  # 不接受执行结果 And 超时控制
            print "deploy task [{}] End.".format(deploy['name'])

    def ERROR_EXIT(self,msg=None):
        if msg:
            self.error = msg
        else:
            self.error = "Unknow Error, Exception Exit."
        print self.error
        self.error_notify()

    def error_notify(self):
        if self.use_notify:
            self.notify_obj.send_notify(0,self.__dict__)

    def normal_notify(self):
        if self.use_notify:
            self.notify_obj.send_notify(1,self.__dict__)
