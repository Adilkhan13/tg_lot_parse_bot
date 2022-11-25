import os
import telebot
import pickle
from telebot import types
import argparse

# init some files
if not os.path.exists("/src/database/main.db"):
    from create_db import create_data_files
    create_data_files()

TOKEN = os.environ['TOKEN']
##########
# import sys

# sys.path.insert(0, "../parsers")
##########
from parsers.sql_scripts import show_sql, delete_duplicates_from_sql
from parsers.gz_parser import gos_zakup_main
from parsers.sk_parser import samruk_main


# USER_DICT = {'496885396':{'views':set(),"keys":set(['пож','спас','огне']),'price':5000000}}
def sql_script_constructor(table, user):
    if table == "samruk_lots":
        select_part = f"SELECT DISTINCT id,name_full,price FROM (select * FROM {table} where  exp_date >=3)"

    elif table == "goszakup_lots":
        select_part = f"SELECT DISTINCT id,name_full ,price,name_short FROM {table}"

    sql_script_lst = []
    if len(user["views"]) > 0:
        sql_script_lst.append(f" id not in ({str(user['views'])[1:-1]}) ")
    if len(user["keys"]) > 0:
        text = "OR".join([f" name_full LIKE '%{i}%' " for i in user["keys"]])
        if table == "goszakup_lots":
            text += "OR" + "OR".join(
                [f" name_short LIKE '%{i}%' " for i in user["keys"]]
            )
        sql_script_lst.append(text)
    sql_script_lst.append(f"price > '{str(user['price'])}'")
    where_part = "WHERE " + " AND ".join([f"({i})" for i in sql_script_lst])
    return select_part + " \n" + where_part + ";"


def text_for_chat(user_id):
    res = show_sql(sql_script_constructor("goszakup_lots", USER_DICT[user_id]))
    res += show_sql(sql_script_constructor("samruk_lots", USER_DICT[user_id]))
    total_text = []
    for el in res:
        text = []
        text.append("*Наименование и описание лота*:\n" + str(el[1]))
        text.append("*Сумма, млн.тг.*:\n" + str(round(el[2] / 1000000, 2)))
        if len(el) > 3:
            text.append(
                "*Ссылка*:\n"
                + str(
                    r"https://www.goszakup.gov.kz/ru/announce/index/"
                    + el[3].partition("-")[0]
                ).strip()
            )
        else:
            text.append(
                "*Ссылка*:\n"
                + str(rf"https://zakup.sk.kz/#/ext(popup:item/{el[0]}/advert)").strip()
            )
        total_text.append("\n\n".join(text))
        USER_DICT[user_id]["views"].update([el[0]])
    return total_text


"""
Created 01/07/2022

@author: Zaidulla Adilkan
@email : adilhanzai@gmail.com
"""


bot = telebot.TeleBot(TOKEN)

USER_DICT_PATH = "../database/USER_DICT.pkl"
a_file = open(USER_DICT_PATH, "rb")
USER_DICT = pickle.load(a_file)

MENU_WORDS = set(
    [
        "📋Вернуться в меню",
        "Изменить фильтры",
        "изменить цену",
        "изменить ключевые слова",
        "удалить слово",
        "добавить слово",
        "👩‍💻Связаться с менеджером",
    ]
)


def menu(n):
    if n == 1:
        itembtn1 = types.KeyboardButton("Обновить")
        itembtn2 = types.KeyboardButton("Изменить фильтры")
        itembtn3 = types.KeyboardButton("👩‍💻Связаться с менеджером")

        # or add KeyboardButton one row at a time:
        markup = types.ReplyKeyboardMarkup()
        markup.row(itembtn1)
        markup.row(itembtn2)
        markup.row(itembtn3)
        return markup
    if n == 2:
        itembtn1 = types.KeyboardButton("изменить цену")
        itembtn2 = types.KeyboardButton("изменить ключевые слова")
        itembtn3 = types.KeyboardButton("📋Вернуться в меню")

        # or add KeyboardButton one row at a time:
        markup = types.ReplyKeyboardMarkup()
        markup.row(itembtn1)
        markup.row(itembtn2)
        markup.row(itembtn3)
        return markup

    if n == 3:
        itembtn1 = types.KeyboardButton("удалить слово")
        itembtn2 = types.KeyboardButton("добавить слово")
        itembtn3 = types.KeyboardButton("📋Вернуться в меню")

        # or add KeyboardButton one row at a time:
        markup = types.ReplyKeyboardMarkup()
        markup.row(itembtn1)
        markup.row(itembtn2)
        markup.row(itembtn3)
        return markup


#
@bot.message_handler(commands=["start"])
def start_message(message):
    bot.send_message(message.chat.id, "Бот в процессе разработки", reply_markup=menu(1))
    if str(message.chat.id) not in USER_DICT:
        USER_DICT[str(message.chat.id)] = {"views": set(), "keys": set(), "price": 0}
        bot.send_message(
            message.from_user.id, "Введите минимальную интересующую вас цену лота"
        )
        bot.register_next_step_handler(message, get_min_price)
        # следующий шаг – функция get_name


def get_min_price(message):
    if message.text in MENU_WORDS:
        bot.send_message(message.from_user.id, "Отмена действия", reply_markup=menu(1))
        return None
    if (message.text).isdigit():
        USER_DICT[str(message.chat.id)]["price"] = int((message.text).lower())
        bot.send_message(
            message.from_user.id, "минимальная цена изменена", reply_markup=menu(1)
        )
    else:
        USER_DICT[str(message.chat.id)]["price"] = 0
        bot.send_message(
            message.from_user.id,
            "минимальная цена введена не корректно, условное значение было выставленно как 0",
            reply_markup=menu(1),
        )

    if len(USER_DICT[str(message.chat.id)]["keys"]) == 0:
        bot.send_message(
            message.from_user.id, "Введите интересующее вас ключевое слово"
        )
        bot.register_next_step_handler(message, get_key_words)


def get_key_words(message):
    if message.text in MENU_WORDS:
        bot.send_message(message.from_user.id, "Отмена действия", reply_markup=menu(1))
        return None
    USER_DICT[str(message.chat.id)]["keys"].update([(message.text).lower()])
    bot.send_message(
        message.from_user.id, "Ключевое слово добавленно", reply_markup=menu(3)
    )
    bot.send_message(
        message.from_user.id,
        f"Ключевые слова:{', '.join(USER_DICT[str(message.chat.id)]['keys'])}",
        reply_markup=menu(3),
    )


def delete_key_words(message):
    if message.text in MENU_WORDS:
        bot.send_message(message.from_user.id, "Отмена действия", reply_markup=menu(1))
        return None
    if (message.text).lower() in USER_DICT[str(message.chat.id)]["keys"]:
        USER_DICT[str(message.chat.id)]["keys"].remove((message.text).lower())
        bot.send_message(
            message.from_user.id, "Ключевое слово удаленно", reply_markup=menu(3)
        )
        bot.send_message(
            message.from_user.id,
            f"Ключевые слова:{', '.join(USER_DICT[str(message.chat.id)]['keys'])}",
            reply_markup=menu(3),
        )
    else:
        bot.send_message(
            message.from_user.id,
            f"Данного слова нет в списке ключевых слов\nКлючевые слова:{', '.join(USER_DICT[str(message.chat.id)]['keys'])}",
            reply_markup=menu(3),
        )


@bot.message_handler(commands=["update"])
def update_message(message):
    gos_zakup_main()
    bot.send_message(message.chat.id, "updated gos_zakup_lots")
    try:
        

        samruk_main()
        print('Samruk Жив!')
    except Exception as e:
        print('"samruk data not parsed"\nОшибка:\n', str(e))
        bot.send_message(message.chat.id, "samruk data not parsed")

    bot.send_message(message.chat.id, "updated sk_lots")
    delete_duplicates_from_sql()
    bot.send_message(message.chat.id, "deleted duplicates")


@bot.message_handler(commands=["me"])
def about_me_message(message):
    bot.send_message(message.chat.id, "Ваши настройки:\n")
    bot.send_message(
        message.chat.id,
        "Минимальная цена\n" + str(USER_DICT[str(message.chat.id)]["price"]),
    )
    bot.send_message(
        message.chat.id,
        "Ключевые слова\n" + str(USER_DICT[str(message.chat.id)]["keys"]),
    )
    bot.send_message(
        message.chat.id,
        "Просмотренно лотов\n" + str(len(USER_DICT[str(message.chat.id)]["views"])),
    )


@bot.message_handler(content_types=["text"])
def send_text(message):

    if message.text == "Обновить":
        # bot.send_message(message.chat.id, 'Выберите категорию:', reply_markup=menu(5))
        if str(message.chat.id) in USER_DICT:
            total_text = text_for_chat(str(message.chat.id))
            if len(total_text) == 0:
                bot.send_message(
                    message.chat.id, "Пока ничего актуального нет", reply_markup=menu(1)
                )
            else:
                for text in total_text:
                    bot.send_message(
                        message.chat.id,
                        text,
                        parse_mode="Markdown",
                        reply_markup=menu(1),
                    )
    if message.text == "📋Вернуться в меню":
        bot.send_message(message.chat.id, "Выберите категорию:", reply_markup=menu(1))
    if message.text == "Изменить фильтры":
        bot.send_message(message.chat.id, "Выберите категорию:", reply_markup=menu(2))
    if message.text == "изменить цену":
        bot.send_message(
            message.from_user.id, "Введите минимальную интересующую вас цену лота"
        )
        bot.register_next_step_handler(message, get_min_price)
        # bot.send_message(message.chat.id, 'Выберите категорию:', reply_markup=menu(3))
    if message.text == "изменить ключевые слова":
        bot.send_message(message.chat.id, "Выберите категорию:", reply_markup=menu(3))
    if message.text == "удалить слово":
        bot.send_message(
            message.from_user.id, "Введите интересующее вас ключевое слово"
        )
        bot.register_next_step_handler(message, delete_key_words)
        # bot.send_message(message.chat.id, 'Выберите категорию:', reply_markup=menu(5))
    if message.text == "добавить слово":
        bot.send_message(
            message.from_user.id, "Введите интересующее вас ключевое слово"
        )
        bot.register_next_step_handler(message, get_key_words)
        # bot.send_message(message.chat.id, 'Выберите категорию:', reply_markup=menu(5))
    if message.text == "👩‍💻Связаться с менеджером":
        bot.send_message(
            message.from_user.id,
            "Данный функционал пока не добавлен прошу писать на @Acheronta",
            reply_markup=menu(1),
        )
        # bot.send_message(message.chat.id, 'Выберите категорию:', reply_markup=menu(5))

    if "fire" == str(message.text).lower():
        # bot.send_message(message.chat.id, 'fire')
        if str(message.chat.id) in USER_DICT:
            total_text = text_for_chat(str(message.chat.id))
            if len(total_text) == 0:
                bot.send_message(message.chat.id, "Пока ничего актуального нет")
            else:
                for text in total_text:
                    bot.send_message(message.chat.id, text, parse_mode="Markdown")

        elif str(message.chat.id) not in USER_DICT:
            if str(message.chat.id) == "581173518":
                USER_DICT[str(message.chat.id)] = {
                    "views": set(),
                    "keys": set(["пож", "спас", "огне"]),
                    "price": 5_000_000,
                }
            else:
                USER_DICT[str(message.chat.id)] = {
                    "views": {},
                    "keys": set(),
                    "price": 0,
                }
            print(USER_DICT)
            bot.send_message(message.chat.id, "Сюда меню надо прикрутить")

    if "fire_to_max" == str(message.text).lower():
        total_text = text_for_chat(str("496885396"))
        if len(total_text) == 0:
            bot.send_message(message.chat.id, "Пока ничего актуального нет")
        else:
            for text in total_text:
                bot.send_message("496885396", text, parse_mode="Markdown")
            bot.send_message(message.chat.id, f"отправленно {len(total_text)}")

    a_file = open(USER_DICT_PATH, "wb")
    pickle.dump(USER_DICT, a_file)
    a_file.close()
    #
    #    bot.send_message(message.chat.id, 'Выберите категорию:', reply_markup=menu(5))
    #


bot.infinity_polling(timeout=10, long_polling_timeout=5)
