#! /bin/bash

pip install -r requirements.txt

mkdir ~/.acme_tea
mkdir ~/.acme_tea/bin
mkdir ~/.acme_tea/log
mkdir ~/.acme_tea/result
mkdir ~/.acme_tea/conf

cp *.py ~/.acme_tea/bin/
cp config.yaml.example ~/.acme_tea/conf/config.yaml.example

source ~/.acme_tea/acme_tea.env
echo "source ~/.acme_tea/acme_tea.env" >> .bashrc