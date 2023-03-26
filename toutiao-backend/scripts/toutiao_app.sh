#! /bin/bash
source ~/.bash_profile
cd /home/python/toutiao-backend/
workon toutiao
exec gunicorn -w 4 -b 127.0.0.1:5000 --access-logfile /home/python/logs/access_toutiao_app.log --error-logfile /home/python/logs/error_toutiao_app.log toutiao.main:app