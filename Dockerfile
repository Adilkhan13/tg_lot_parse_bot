FROM python:3.8
COPY requirments.txt requirments.txt
RUN python -m pip install --upgrade pip && pip install -r requirments.txt
COPY src/app src/app
WORKDIR src/app
ENTRYPOINT ["python3","telegram_bot.py"]