# coding=utf-8

import base64
import json
import os
from binascii import a2b_hex
import hashlib
import yaml

user_home = os.path.expanduser('~')
project_dir = os.path.join(user_home, '.acme_tea')
bin_dir = os.path.join(project_dir, 'bin')
log_dir = os.path.join(project_dir, 'log')
result_dir = os.path.join(project_dir, 'result')
config_dir = os.path.join(project_dir, 'conf')
acct_dir = os.path.join(config_dir, 'acct')
acct_key_path = os.path.join(acct_dir, 'account')
acct_conf_path = os.path.join(acct_dir, 'acct.json')
config_yaml_path = os.path.join(config_dir, 'config.yaml')

acct_Data = {}

def load_acct_Data():
    with open(acct_conf_path,'r') as f:
        global acct_Data
        acct_Data = json.load(f)

def gen_acct_Data():
    acct_Data["jwk"] = pem2jwk()
    acct_Data["thumbprint"] = calc_thumbprint()

def add_kid_acct_Data(kid):
    acct_Data["kid"] = kid

def save_acct_Data():
    with open(acct_conf_path,'w') as f:
        json.dump(acct_Data, f)

config_Data = {}

def load_config_Data():
    if not os.path.exists(config_yaml_path):
        print "config.yaml Not Found"
        return False
    with open(config_yaml_path,'r') as f:
        try:
            config_Data = yaml.load(f.read())
        except:
            print "config.yaml Parse Failed, Format Error!"
            return False
    return True


def _b64(content):
    return base64.urlsafe_b64encode(content).decode('utf8').replace("=", "")

def pem2jwk(keyfile=acct_key_path):
    pubi = int(os.popen("openssl ec -in {} -noout -text 2>/dev/null | grep -n pub: | cut -d : -f 1".format(keyfile)).read())
    pubi += 1
    pubj = int(os.popen("openssl ec -in {} -noout -text 2>/dev/null | grep -n \"ASN1 OID:\" | cut -d : -f 1".format(keyfile)).read())
    pubj -= 1
    pubtext = os.popen("openssl ec -in {} -noout -text 2>/dev/null | sed -n \"{},{}p\" | tr -d \" \\n\\r\"".format(keyfile,pubi,pubj)).read()

    xlen = int(os.popen("printf \"%s\" \"{}\" | tr -d ':' | wc -c".format(pubtext)).read())
    xlen = xlen / 4
    xend = xlen + 1
    x = os.popen("printf \"%s\" \"{}\" | cut -d : -f 2-{}".format(pubtext,xend)).read()
    ystart = xend + 1
    y = os.popen("printf \"%s\" \"{}\" | cut -d : -f {}-10000".format(pubtext,ystart)).read()

    x64 = _b64(a2b_hex(x.replace(':','').strip('\n').upper()))
    y64 = _b64(a2b_hex(y.replace(':','').strip('\n').upper()))

    jwk = {"crv": "P-256", "kty": "EC", "x": x64, "y": y64}
    return jwk

def calc_thumbprint(jwk=None):
    if not jwk:
        jwk = acct_Data["jwk"]
    accountkey_json = json.dumps(jwk, sort_keys=True, separators=(',', ':'))
    thumbprint = _b64(hashlib.sha256(accountkey_json.encode('utf8')).digest())
    return thumbprint

def signature(protected64,payload64,keyfile=acct_key_path):
    signedECText = os.popen("printf \"%s\" \"{}.{}\"| openssl dgst -sha256 -sign {}| openssl asn1parse -inform DER".format(protected64,payload64,keyfile)).read()
    ec_r = os.popen("echo \"{}\" | head -n 2 | tail -n 1 | cut -d : -f 4 | tr -d \"\\r\\n\"".format(signedECText)).read()
    ec_s = os.popen("echo \"{}\" | head -n 3 | tail -n 1 | cut -d : -f 4 | tr -d \"\\r\\n\"".format(signedECText)).read()
    return _b64(a2b_hex(ec_r+ec_s))

def dns01_txt(token):
    keyauthorization = "{0}.{1}".format(token, acct_Data["thumbprint"])
    txt = _b64(hashlib.sha256(keyauthorization).digest())
    return txt

# def debug_log():
#     pass