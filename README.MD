## Запуск ->


#### Через команды Docker
# Создаем сеть 
sudo docker network create tg_1
# Собираем Образ с докерфайла 
sudo docker build -t telegram_tender_5 
# Запуск хрома
# порт прокидывать не обязательно они в одной сети 
sudo docker run -d \
 --net=tg_1 \
 --name=s_chrome \
 -p 4444:4444 \
 selenium/standalone-chrome
# запускаем бота
sudo docker run -it \
 -v $(pwd)/src/database:/src/database \
 --rm --net=tg_1 \
 -e SELENIUM_HOST=s_chrome \
 -e TOKEN=<Ваш токен $(cat secret_token)> \
 telegram_tender_5 \



#### Через команды Docker-compose
sudo docker-compose -f docker-compose.yaml up


### В планах
- рефакторинг кода
    - убрать pandas
    - добавить healthcheck
    - рефакторинг в ООП(добавление платной подписки к samruk закупу)