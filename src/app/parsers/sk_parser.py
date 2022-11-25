import re
import math
import os
from datetime import datetime, timedelta

from bs4 import BeautifulSoup

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium import webdriver


import pandas as pd

from sqlalchemy import create_engine

from parsers.sql_scripts import yesterday, show_sql, DB_LAG, DB_PATH

from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

# CHROME_DRIVER_PATH = "...\chromedriver\chromedriver.exe"
TIMEOUT = 5
KEY_NAMES = ["пож", "спас", "огне"]


def samruk_main():

    browser = webdriver.Remote(f"http://{os.environ['SELENIUM_HOST']}:4444/wd/hub", DesiredCapabilities.CHROME)
    browser.implicitly_wait(TIMEOUT)

    dct = {"id": [], "type": [], "name": [], "exp_date": [], "price": []}
    try:
        for key_name in KEY_NAMES:
            adst_list = ["DISCUSSION_PUBLISHED", "PUBLISHED"]
            for adst in adst_list:
                URL = rf"https://zakup.sk.kz/#/ext?tabs=advert&q={key_name}&adst={adst}&lst=PUBLISHED&page=1"
                browser.get(URL)

                WebDriverWait(browser, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, ".info.jhi-item-count.ng-star-inserted")
                    )
                )
                text = browser.find_element(
                    By.CSS_SELECTOR, ".info.jhi-item-count.ng-star-inserted"
                ).text
                row_count = int(
                    max([i for i in re.findall("[0-9]*", text) if i.isdigit()])
                )
                pages_count = math.ceil(row_count / 10)

                if pages_count > 1:
                    for page in range(1, pages_count + 1):
                        if show_sql(DB_LAG)[0][0]:
                            URL = rf"https://zakup.sk.kz/#/ext?tabs=advert&q={key_name}&adst={adst}&lst=PUBLISHED&bab={yesterday('sk',int(show_sql(DB_LAG)[0][0]))}&page={page}"
                        else:
                            URL = rf"https://zakup.sk.kz/#/ext?tabs=advert&q={key_name}&adst={adst}&lst=PUBLISHED&bab={yesterday('sk')}&page={page}"
                        browser.get(URL)
                        WebDriverWait(browser, 10).until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR, ".m-sidebar.m-sidebar--found-list")
                            )
                        )
                        element = browser.find_element(
                            By.CSS_SELECTOR, ".m-sidebar.m-sidebar--found-list"
                        )
                        soup = BeautifulSoup(
                            element.get_attribute("innerHTML"), "html.parser"
                        )
                        list_of_elements = soup.find_all(
                            class_="m-found-item m-found-item--success"
                        )
                        for i in range(len(list_of_elements)):
                            dct["id"].append(
                                soup.find_all(
                                    class_="m-found-item m-found-item--success"
                                )[i]
                                .find_all("div")[0]
                                .text
                            )
                            dct["type"].append(
                                soup.find_all(
                                    class_="m-found-item m-found-item--success"
                                )[i]
                                .find_all("div")[1]
                                .text
                            )
                            dct["name"].append(
                                soup.find_all(
                                    class_="m-found-item m-found-item--success"
                                )[i]
                                .find_all("h3")[0]
                                .text
                            )
                            dct["exp_date"].append(
                                soup.find_all(
                                    class_="m-found-item m-found-item--success"
                                )[i]
                                .find_all("div")[3]
                                .text
                            )
                            dct["price"].append(
                                soup.find_all(
                                    class_="m-found-item m-found-item--success"
                                )[i]
                                .find_all("div")[4]
                                .text
                            )
                else:
                    element = browser.find_element(
                        By.CSS_SELECTOR, ".m-sidebar.m-sidebar--found-list"
                    )
                    soup = BeautifulSoup(
                        element.get_attribute("innerHTML"), "html.parser"
                    )
                    list_of_elements = soup.find_all(
                        class_="m-found-item m-found-item--success"
                    )
                    for i in range(len(list_of_elements)):
                        dct["id"].append(
                            soup.find_all(class_="m-found-item m-found-item--success")[
                                i
                            ]
                            .find_all("div")[0]
                            .text
                        )
                        dct["type"].append(
                            soup.find_all(class_="m-found-item m-found-item--success")[
                                i
                            ]
                            .find_all("div")[1]
                            .text
                        )
                        dct["name"].append(
                            soup.find_all(class_="m-found-item m-found-item--success")[
                                i
                            ]
                            .find_all("h3")[0]
                            .text
                        )
                        dct["exp_date"].append(
                            soup.find_all(class_="m-found-item m-found-item--success")[
                                i
                            ]
                            .find_all("div")[3]
                            .text
                        )
                        dct["price"].append(
                            soup.find_all(class_="m-found-item m-found-item--success")[
                                i
                            ]
                            .find_all("div")[4]
                            .text
                        )
        browser.close()
        df = pd.DataFrame(dct)
        df = df.drop_duplicates("id")
        df["id"] = df["id"].str.replace("№ ", "").astype(int)
        df["exp_date"] = df["exp_date"].str.findall("\d+").str[0].astype(int)
        df["price"] = (
            df["price"]
            .str.findall("\d+|,")
            .str.join("")
            .str.replace(",", ".")
            .astype(float)
        )
        df = df.rename(columns={"name": "name_full"})
        gos_zakup_sql_loading(df)
    except:
        browser.close()


def gos_zakup_sql_loading(df):
    """загрузка данных гос закупа в sql"""
    engine = create_engine("sqlite:///" + DB_PATH, echo=False)
    df.to_sql("samruk_lots", con=engine, if_exists="append", index=False)


if __name__ == "__main__":
    samruk_main()
