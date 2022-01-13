#! /bin/bash

TEMP_DIR=/tmp/acme_tea

pip install -r $TEMP_DIR/requirements.txt

mkdir ~/.acme_tea
mkdir ~/.acme_tea/bin
mkdir ~/.acme_tea/log
mkdir ~/.acme_tea/result
mkdir ~/.acme_tea/conf

cp $TEMP_DIR/*.py ~/.acme_tea/bin/
cp -R $TEMP_DIR/dns01 ~/.acme_tea/bin/
cp -R $TEMP_DIR/notify ~/.acme_tea/bin/
cp $TEMP_DIR/config.yaml.example ~/.acme_tea/conf/config.yaml.example
cp $TEMP_DIR/.env ~/.acme_tea/.env

chmod +x ~/.acme_tea/bin/acme_tea.py
source ~/.acme_tea/.env
echo "source ~/.acme_tea/.env" >> ~/.bashrc

( crontab -l ; echo "30 2 * * * ~/.acme_tea/bin/acme_tea.py --cron" ) | crontab - 
