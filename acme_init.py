# coding=utf-8

from acme_util import acct_dir, acct_key_path, load_acct_Data, gen_acct_Data, save_acct_Data, add_kid_acct_Data
from acme_req import ACME_directory, ACME_Account
import os
import sys

def openssl_check():
    # OpenSSL 1.0.2k-fips  26 Jan 2017
    # OpenSSL 1.1.1f  31 Mar 2020
    version_out = os.popen("openssl version").read()
    if "command not found" in version_out:
        print "Need to install OpenSSL"
        return False
    
    version_num = version_out.split()[1]
    if version_num > '1.0.1g':
        return True
    else:
        print "OpenSSL need to upgrade, Heartbleed"
        return False

def init():
    if not openssl_check():
        sys.exit(1)

    if not ACME_directory():
        print "ACME Service Unavailable"
        sys.exit(1)

    if os.path.exists(acct_dir):
        print "Not need init, Read last config"
        load_acct_Data()

    else:
        print "Need Init, Start Now"

        os.mkdir(acct_dir)
        print "1. Generate Account Private Key"
        os.popen("openssl ecparam -name prime256v1 -genkey -out {}".format(acct_key_path))
        gen_acct_Data()

        print "2. Send newAccount Request"
        acct_obj = ACME_Account(1)
        result = acct_obj.stable_return()

        if result["status"] != "valid":
            print "Current Account Statu Not Valid!"
            return False

        add_kid_acct_Data(result['url'])

        print "3. Save Account Config Data"
        save_acct_Data()
        print "Init Done."

    return True