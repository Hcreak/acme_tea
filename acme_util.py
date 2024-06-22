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
dns01_plugin_dir = os.path.join(bin_dir, 'dns01')
notify_plugin_dir = os.path.join(bin_dir, 'notify')

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
        json.dump(acct_Data, f, indent=4, encoding='utf-8', sort_keys=True)

# FUCK!!!FUCK!!!FUCK!!!
def acct_auth_option():
    if acct_Data.has_key("kid"):
        return {"kid": acct_Data["kid"]}
    else:
        return {"jwk": acct_Data["jwk"]}

config_Data = {}

def load_config_Data():
    if not os.path.exists(config_yaml_path):
        print "config.yaml Not Found"
        return False
    with open(config_yaml_path,'r') as f:
        try:
            global config_Data
            config_Data = yaml.load(f.read())
        except:
            print "config.yaml Parse Failed, Format Error!"
            return False
    return True

# FUCK!!!FUCK!!!FUCK!!!
def get_config_Data(item):
    if config_Data.has_key(item):
        return config_Data[item]
    else:
        return None


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

def path_check(file_path):
    dir_path = os.path.split(file_path)[0]
    if not os.path.exists(dir_path):
        os.popen("mkdir -p {}".format(dir_path))

def get_ARI_CertID(cert_path):
    AKI_raw = os.popen("openssl x509 -in {} -noout -ext authorityKeyIdentifier".format(cert_path)).read()
    AKI_b64 = _b64(a2b_hex(AKI_raw.split('\n')[1].replace(' ','').replace(':','')))
    Serial_raw = os.popen("openssl x509 -in {} -noout -serial".format(cert_path)).read()
    Serial_b64 = _b64(a2b_hex(Serial_raw.split('\n')[0].replace('serial=','')))
    return "{}.{}".format(AKI_b64, Serial_b64)