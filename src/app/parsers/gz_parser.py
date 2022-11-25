import re
import math
import time

import ssl

ssl._create_default_https_context = ssl._create_unverified_context

import logging

import pandas as pd

import urllib.request
from bs4 import BeautifulSoup

from sqlalchemy import create_engine

from parsers.sql_scripts import yesterday, show_sql, DB_LAG, DB_PATH


logging.basicConfig(
    level=logging.INFO,
    filename="../database/mylog.log",
    format="%(asctime)s - %(module)s - %(levelname)s - %(funcName)s: %(lineno)d - %(message)s",
    datefmt="%H:%M:%S",
    force=True,
)
URL = r"https://www.goszakup.gov.kz/ru/search/lots?filter%5Bstatus%5D%5B0%5D=220&filter%5Bstatus%5D%5B1%5D=210&filter%5Bstatus%5D%5B2%5D=240"
if show_sql(DB_LAG)[0][0]:
    URL += yesterday("gz", int(show_sql(DB_LAG)[0][0]))
else:
    URL += yesterday("gz")


def page_counts() -> int:
    """Считает количество страниц для парсинга в цикле"""
    html = urllib.request.urlopen(URL).read().decode("utf8")
    soup = BeautifulSoup(html, "html.parser")
    text = soup.find_all(class_="dataTables_info")[0].get_text().replace("\n", "")
    row_count = int(max([i for i in re.findall("[0-9]*", text) if i.isdigit()]))
    pages_count = math.ceil(row_count / 2000)
    return pages_count


def gos_zakup_cleaning(df) -> pd.DataFrame:
    """Очистка датафрейма"""
    df["Сумма, тг."] = df["Сумма, тг."].str.replace(" ", "").astype(float)
    df["Кол-во"] = df["Кол-во"].astype(float)
    df["Наименование и описание лота"] = (
        df["Наименование и описание лота"]
        .apply(lambda x: x[:-7] if x[-7:] == "История" else x)
        .str.strip()
    )
    return df


def gos_zakup_parsing(url):
    """Поскольку сайт часто вылетает парсинг происходит в цикле"""
    error = True
    sleep_time = 10
    while error:
        if sleep_time > 100:
            logging.error(
                f"parsing error sleep time get over 100({sleep_time}) breaking "
            )
            break
        try:
            df = pd.read_html(url)[1]
            error = False
        except:
            logging.error(f"parsing error increasing sleep time to {sleep_time}")
            time.sleep(sleep_time)
            sleep_time += 10
    return df


def gos_zakup_main():
    """главная функция парсинга гос закупа"""
    logging.info(f"подсчет количества страниц на сайте goszakup")
    pages_count = page_counts()
    logging.info(f"Кол-во страниц на сайте goszakup составило {pages_count}")
    # data = []
    sleep_time = 1
    for i in range(pages_count + 1):
        logging.info(f"page {i} parsing... ")

        df = gos_zakup_parsing(URL + rf"&count_record=2000&page={i}")
        df = df.reset_index(drop=True)
        df = gos_zakup_cleaning(df)
        df.columns = [
            "id",
            "name_short",
            "name_full",
            "qty",
            "price",
            "lot_type",
            "status",
        ]
        gos_zakup_sql_loading(df)
        time.sleep(sleep_time)
        logging.info(f"page {i} was parsed")


def gos_zakup_sql_loading(df):
    """загрузка данных гос закупа в sql"""
    engine = create_engine("sqlite:///" + DB_PATH, echo=False)
    df.to_sql("goszakup_lots", con=engine, if_exists="append", index=False)


if __name__ == "__main__":
    URL = r"https://www.goszakup.gov.kz/ru/search/lots?filter%5Bstatus%5D%5B0%5D=220&filter%5Bstatus%5D%5B1%5D=210&filter%5Bstatus%5D%5B2%5D=240"
    URL += yesterday("gz", int(show_sql(DB_LAG)[0][0]))
    print(URL)
    gos_zakup_main()
