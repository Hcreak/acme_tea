# coding=utf-8

import requests
import json
from acme_util import _b64, acct_auth_option, signature, log_dir
import time
import os

REQ_RETRY_NUM = 5

directory_Data = {}

def ACME_directory(staging=False):
    if staging:
        directory_url = "https://acme-staging-v02.api.letsencrypt.org/directory"
    else:
        # This is Production
        directory_url = "https://acme-v02.api.letsencrypt.org/directory"

    r = requests.get(directory_url)
    if r.status_code != 200:
        return False
    else:
        info = r.json()
        directory_Data["newAccount"] = info["newAccount"]
        directory_Data["newNonce"] = info["newNonce"]
        directory_Data["newOrder"] = info["newOrder"]
        return True


class ACME_REQ:
    Forward_r_list = []

    @staticmethod
    def get_nonce():
        if len(ACME_REQ.Forward_r_list):
            r = ACME_REQ.Forward_r_list[-1]
        else:
            r = requests.head(directory_Data["newNonce"])
        return r.headers.get('Replay-Nonce')

    def __init__(self,url,payload=None):
        self.url = url
        # Fuck!!! {} Empty Dict also as False
        if payload == None:
            self.payload64 = ""
        else:
            self.payload64 = _b64(json.dumps(payload))

        self.try_req()

    def build_protected(self):
        protected = {
            "nonce": self.get_nonce(),
            "url": self.url,
            "alg": "ES256"
        }
        protected.update(acct_auth_option())

        self.protected64 = _b64(json.dumps(protected))

    def req_signature(self):
        return signature(self.protected64,self.payload64)

    def req(self):
        # Fix Bug: should get_nonce Every req
        self.build_protected()

        content = {
            "protected": self.protected64,
            "payload": self.payload64,
            "signature": self.req_signature()
        }
        # 不用 json= 参数, 防止 Content-Type 覆盖
        r = requests.post(self.url, headers={"Content-Type":"application/jose+json"}, data=json.dumps(content))
        # 无论是否成功都加入列表中 因为响应中都包含Replay-Nonce 同时也方便调试
        ACME_REQ.Forward_r_list.append(r)
        # 还有 201 Created
        if r.status_code != 200 and r.status_code != 201:
            return False
        else:
            self.r = r
            return True

    def try_req(self):
        for i in range(REQ_RETRY_NUM):
            if self.req():
                return
            else:
                print "Request Error, 10s Later Retry..."
                time.sleep(10)
                 
        print "Limit Retry Number upper, Exception Exit."
        self.Exception_Exit()

    def stable_return(self):
        # Fix Bug: some response Not json (e.g. ACME_Cert)
        if self.r.headers["Content-Type"] == "application/json":
            # some response Not have Location (headers.get return None)
            data = {'url': self.r.headers.get('Location')}
            data.update(self.r.json())
            return data
        else:
            return self.r.content

    @staticmethod
    def print_raw_res():
        output = ""
        for r in ACME_REQ.Forward_r_list:
            output += '''
###
{req.method} {req.url}
{req_headers}

{req_body}

-------------------------------------------------

{res.status_code} {res.reason}
{res_headers}

{res.text}
            '''.format(
                req=r.request,
                req_body=json.dumps(json.loads(r.request.body), indent=2, encoding='utf-8'),
                res=r,
                req_headers='\r\n'.join('{}: {}'.format(k, v) for k, v in r.request.headers.items()),
                res_headers='\r\n'.join('{}: {}'.format(k, v) for k, v in r.headers.items())
            )

        return output

    @staticmethod
    def save_http_log():
        filetime = time.strftime("%Y-%m-%d_%H-%M", time.localtime())
        http_log_path = os.path.join(log_dir, filetime+'.http')
        write_content = ACME_REQ.print_raw_res()
        if write_content:
            with open(http_log_path,'w') as f:
                f.write(write_content)

    @staticmethod
    def Exception_Exit():
        ACME_REQ.save_http_log()
        import sys
        sys.exit(1)


class ACME_Account(ACME_REQ):
    def __init__(self,mode):
        if mode:
            url = directory_Data["newAccount"]
            payload = {
                "termsOfServiceAgreed": True
            }

            ACME_REQ.__init__(self,url,payload)
           
        # Not Used
        # else:
        #     url = acct_Data["kid"]
        #     ACME_REQ.__init__(self,url)


class ACME_Order(ACME_REQ):
    def __init__(self,mode,domains=[],url=None):
        if mode:
            url = directory_Data["newOrder"]

            payload = {
                "identifiers": []
            }

            for d in domains:
                payload["identifiers"].append(
                    {
                        "type": "dns",
                        "value": d
                    }
                )

            ACME_REQ.__init__(self,url,payload)

        # verify statu
        else:
            ACME_REQ.__init__(self,url)


class ACME_AuthZ(ACME_REQ):
    def __init__(self,mode,url):  # mode only 0
        ACME_REQ.__init__(self,url)


class ACME_Chall(ACME_REQ):
    def __init__(self,mode,url):
        # Go Challenge
        if mode:
            payload = {}
            ACME_REQ.__init__(self,url,payload)

        # verify statu
        else:
            ACME_REQ.__init__(self,url)


class ACME_Finalize(ACME_REQ):
    def __init__(self,mode,url,csrfile):  # mode only 1
        csr_der = _b64(os.popen("openssl req -in {} -outform DER".format(csrfile)).read())
        payload = {
            "csr": csr_der
        }
        ACME_REQ.__init__(self,url,payload)


class ACME_Cert(ACME_REQ):
    def __init__(self,mode,url):  # mode only 0
        ACME_REQ.__init__(self,url)
