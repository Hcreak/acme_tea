# coding=utf-8

# Fuck Let's Encrypt!!!! ECDSA curve P-521 not allowed!!!!
# Fuck echo Default Add \n , Use echo -n OR printf !!!!
# Fuck RFC!!! Fuck POST-as-GET!!!!

import base64
import json
import os
from binascii import a2b_hex
import requests
import hashlib

def _b64(content):
    return base64.urlsafe_b64encode(content).decode('utf8').replace("=", "")

Forward_r_list = []
acct_Data = {}

def get_nonce():
    if len(Forward_r_list):
        r = Forward_r_list[-1]
    else:
        r = requests.head("https://acme-staging-v02.api.letsencrypt.org/acme/new-nonce")
    return r.headers.get('Replay-Nonce')

def pem2jwk(keyfile):
    pubi = int(os.popen("openssl ec -in {} -noout -text 2>/dev/null | grep -n pub: | cut -d : -f 1".format(keyfile)).read())
    pubi += 1
    pubj = int(os.popen("openssl ec -in {} -noout -text 2>/dev/null | grep -n \"ASN1 OID:\" | cut -d : -f 1".format(keyfile)).read())
    pubj -= 1
    pubtext = os.popen("openssl ec -in {} -noout -text 2>/dev/null | sed -n \"{},{}p\" | tr -d \" \\n\\r\"".format(keyfile,pubi,pubj)).read()

    xlen = int(os.popen("printf \"%s\" \"{}\" | tr -d ':' | wc -c".format(pubtext)).read())
    xlen = xlen / 4
    xend = xlen + 1
    x = os.popen("printf \"%s\" \"{}\" | cut -d : -f 2-{}".format(pubtext,xend)).read()
    xend += 1
    y = os.popen("printf \"%s\" \"{}\" | cut -d : -f {}-10000".format(pubtext,xend)).read()

    x64 = _b64(a2b_hex(x.replace(':','').strip('\n').upper()))  # Fcuk \n !!!
    y64 = _b64(a2b_hex(y.replace(':','').strip('\n').upper()))  # Fcuk \n !!!
    # print x,y,x64,y64

    # jwk = {"crv": "P-521", "kty": "EC", "x": x64, "y": y64}
    jwk = {"crv": "P-256", "kty": "EC", "x": x64, "y": y64}
    return jwk

def calc_thumbprint(jwk):
    accountkey_json = json.dumps(jwk, sort_keys=True, separators=(',', ':'))
    thumbprint = _b64(hashlib.sha256(accountkey_json.encode('utf8')).digest())
    return thumbprint

def signature(protected64,payload64,keyfile):
    # Fuck Fuck Fuck echo Default Add \n , Use echo -n OR printf !!!!
    signedECText = os.popen("printf \"%s\" \"{}.{}\"| openssl dgst -sha256 -sign {}| openssl asn1parse -inform DER".format(protected64,payload64,keyfile)).read()
    ec_r = os.popen("echo \"{}\" | head -n 2 | tail -n 1 | cut -d : -f 4 | tr -d \"\\r\\n\"".format(signedECText)).read()
    ec_s = os.popen("echo \"{}\" | head -n 3 | tail -n 1 | cut -d : -f 4 | tr -d \"\\r\\n\"".format(signedECText)).read()
    return _b64(a2b_hex(ec_r+ec_s))


nonce = get_nonce()
acct_jwk = pem2jwk(keyfile='account')
acct_thumbprint = calc_thumbprint(acct_jwk)

def acct_protected():
    protected = {
        "nonce": nonce,
        "url": "https://acme-staging-v02.api.letsencrypt.org/acme/new-acct",
        # "alg": "ES512",
        "alg": "ES256",
        "jwk": acct_jwk
    }
    return _b64(json.dumps(protected))

def acct_payload():
    payload = {
        "termsOfServiceAgreed": True
    }
    return _b64(json.dumps(payload))

def acct_signature():
    return signature(protected64=acct_protected(), payload64=acct_payload(), keyfile='account')

def order_protected():
    protected = {
        "nonce": nonce,
        "url": "https://acme-staging-v02.api.letsencrypt.org/acme/new-order",
        "alg": "ES256",
        "kid": "https://acme-staging-v02.api.letsencrypt.org/acme/acct/22965118"
    }
    return _b64(json.dumps(protected))

def order_payload():
    payload = {
        "identifiers": [
            {
                "type": "dns",
                "value": "test-e1.xeonphi.xyz"
            }
        ]
    }
    return _b64(json.dumps(payload))

def order_signature():
    return signature(protected64=order_protected(), payload64=order_payload(), keyfile='account')

def authz_protected():
    protected = {
        "nonce": nonce,
        "url": "https://acme-staging-v02.api.letsencrypt.org/acme/authz-v3/242969138",
        "alg": "ES256",
        "kid": "https://acme-staging-v02.api.letsencrypt.org/acme/acct/22965118"
    }
    return _b64(json.dumps(protected))

def authz_signature():
    return signature(protected64=authz_protected(), payload64="", keyfile='account') 

def chall_protected():
    protected = {
        "nonce": nonce,
        "url": "https://acme-staging-v02.api.letsencrypt.org/acme/chall-v3/242969138/Rg-Q6A",
        "alg": "ES256",
        "kid": "https://acme-staging-v02.api.letsencrypt.org/acme/acct/22965118"
    }
    return _b64(json.dumps(protected))

# FUCK!!! FUCK!!! FUCK!!!
def chall_payload_POST():
    payload = {}
    return _b64(json.dumps(payload))

def chall_signature_POST():
    return signature(protected64=chall_protected(), payload64=chall_payload_POST(), keyfile='account')

def chall_signature():
    return signature(protected64=chall_protected(), payload64="", keyfile='account')

def dns01_txt(token):
    keyauthorization = "{0}.{1}".format(token, acct_thumbprint)
    txt = _b64(hashlib.sha256(keyauthorization).digest())
    return txt

def finalize_protected():
    protected = {
        "nonce": nonce,
        "url": "https://acme-staging-v02.api.letsencrypt.org/acme/finalize/22965118/269336538",
        "alg": "ES256",
        "kid": "https://acme-staging-v02.api.letsencrypt.org/acme/acct/22965118"
    }
    return _b64(json.dumps(protected))

def finalize_payload(csrfile):
    csr_der = _b64(os.popen("openssl req -in {} -outform DER".format(csrfile)).read())
    payload = {
        "csr": csr_der
    }
    return _b64(json.dumps(payload))

def finalize_signature():
    return signature(protected64=finalize_protected(), payload64=finalize_payload('domain.csr'), keyfile='account')

def cert_protected():
    protected = {
        "nonce": nonce,
        "url": "https://acme-staging-v02.api.letsencrypt.org/acme/cert/fa31027f9abd2bd9c8a1ccdcaf428cea5d86",
        "alg": "ES256",
        "kid": "https://acme-staging-v02.api.letsencrypt.org/acme/acct/22965118"
    }
    return _b64(json.dumps(protected))

def cert_signature():
    return signature(protected64=cert_protected(), payload64="", keyfile='account') 

if __name__ == '__main__':
    # print acct_protected(), acct_payload(), acct_signature()
    # print order_protected(), order_payload(), order_signature()
    # print authz_protected(), authz_signature()
    # print chall_protected(), chall_signature()
    # print dns01_txt("te-ZRlTjIT0Op1_7hSvBZPVZcgMsCCXOv2wPifkVd8c")
    # print chall_protected(), chall_payload_POST(), chall_signature_POST()
    # print finalize_protected(), finalize_payload('domain.csr'), finalize_signature()
    # print cert_protected(), cert_signature()

    protected = {
        "nonce": nonce,
        "url": "https://acme-staging-v02.api.letsencrypt.org/acme/acct/22965118",
        "alg": "ES256",
        "kid": "https://acme-staging-v02.api.letsencrypt.org/acme/acct/22965118"
    }
    protected64 = _b64(json.dumps(protected))
    print protected64
    print signature(protected64=protected64, payload64="", keyfile='account')