#! /bin/bash

pip install -r requirements.txt

mkdir ~/.acme_tea
mkdir ~/.acme_tea/bin
mkdir ~/.acme_tea/log
mkdir ~/.acme_tea/result
mkdir ~/.acme_tea/conf

cp *.py ~/.acme_tea/bin/
cp -R dns01 ~/.acme_tea/bin/
cp -R notify ~/.acme_tea/bin/
cp config.yaml.example ~/.acme_tea/conf/config.yaml.example
cp .env ~/.acme_tea/.env

chmod +x ~/.acme_tea/bin/acme_tea.py
source ~/.acme_tea/.env
echo "source ~/.acme_tea/.env" >> ~/.bashrc

( crontab -l ; echo "30 2 * * * acme_tea --cron" ) | crontab - 