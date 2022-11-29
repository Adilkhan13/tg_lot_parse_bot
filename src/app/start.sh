#!/bin/sh
service cron start&&
cd /src/app && python3  telegram_bot.py