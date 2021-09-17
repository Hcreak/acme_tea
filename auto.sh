#! /bin/bash

LATEST_RELEASE=$(curl -L -s -H 'Accept: application/json' https://github.com/Hcreak/acme_tea/releases/latest)
LATEST_VERSION=$(echo $LATEST_RELEASE | sed -e 's/.*"tag_name":"\([^"]*\)".*/\1/')
ARTIFACT_URL="https://github.com/Hcreak/acme_tea/releases/download/$LATEST_VERSION/acme_tea_install.tar.gz"

curl -L -o /tmp/acme_tea_install.tar.gz $ARTIFACT_URL

tar -zxvf /tmp/acme_tea_install.tar.gz -C /tmp

bash /tmp/acme_tea/setup.sh

rm -rf /tmp/acme*

