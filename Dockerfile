FROM python:3.8
COPY requirments.txt requirments.txt
RUN python -m pip install --upgrade pip && pip install -r requirments.txt
RUN apt-get update && apt-get -y install cron

COPY crontab /etc/cron.d/crontab
RUN chmod 0644 /etc/cron.d/crontab && /usr/bin/crontab /etc/cron.d/crontab

COPY src/app src/app
WORKDIR src/app

RUN chmod +x start.sh
ENTRYPOINT ["./start.sh"]
