from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime
import sqlite3
import re
import os


def get_prices(items: list) -> dict:
    global url
    results = {}
    driver = webdriver.Chrome()
    driver.get(url)

    for i in range(len(items)):
        elem = driver.find_element_by_id('twotabsearchtextbox')  # Finds the search box
        elem.clear()
        elem.send_keys(items[i])
        elem.submit()

        try:
            product = driver.find_element_by_partial_link_text(items[i])
            product.click()  # Go to product's page
            product_name = driver.find_element_by_id('productTitle').text
            price = driver.find_element_by_css_selector('span.a-color-price').text
        except NoSuchElementException:
            # Sometimes the product name can have a slightly change on Amazon updates
            # For example: "Iphone" and "iphone" would make the code above to return an NoSuchElementException
            partial_name = items[i].split()[0]
            product = driver.find_element_by_partial_link_text(partial_name)
            product.click()  # Go to product's page
            product_name = driver.find_element_by_id('productTitle').text
            price = driver.find_element_by_css_selector('span.a-color-price').text
            pass
        except Exception:
            # If no product at all is found
            # Like searching for "asdfgfhjprhr"
            product_name = items[i]
            price = "NotFound"

        results[product_name] = format_value(price)

    driver.close()
    return results


def price_tracker(products: list, db_path: str):
    results = get_prices(products)
    save_prices(database_path=db_path, to_save=results)
    print('Done!')


def format_value(value):
    if value.isalpha():
        return value
    if '-' in value:
        value = value.split('-')[0]
    reg_exp = re.compile(r'[^\d.,]+')
    formatted_value = reg_exp.sub('', value)
    return formatted_value


def save_prices(database_path: str, to_save: dict):
    conn = sqlite3.connect(database_path)
    cur = conn.cursor()

    cur.execute("CREATE TABLE IF NOT EXISTS Amazon_Prices (ID INTEGER PRIMARY KEY AUTOINCREMENT ,\
    Product TEXT, Price REAL, Date TEXT);")

    date = datetime.now().strftime('%d-%b-%Y')
    for name, price in to_save.items():

        table = cur.execute("""SELECT Product, Date
                            FROM Amazon_Prices 
                            WHERE Product = ? AND Date = ?""",
                            (name, date))

        if table.fetchone() is None and price != 'NotFound':
            # Checks if the product already exists for the same date and if a price was found
            cur.execute("INSERT INTO Amazon_Prices (Product, Price, Date) VALUES (?, ?, ?);",
                        (name, price, date))
        conn.commit()
    conn.close()


if __name__ == '__main__':

    db_path = r'C:\Users\Thales\Desktop\AmazonPriceTracker.db'  # Change to your db path

    if not os.path.exists(db_path):
        raise Exception('Database path does not exist')

    url = r'https://www.amazon.com'  # It works any amazon extension (.br, .de, .fr, etc)

    to_search = ['Apple iPhone 11 Pro, 64GB, Space Gray - Fully Unlocked (Renewed)',
                 'The Godfather by Mario Puzo (2002-03-01)',
                 "Timberland Men's White Ledge Mid Waterproof Ankle Boot",
                 'Samsung Electronics UN32N5300AFXZA 32" 1080p Smart LED TV (2018), Black'
                 ]  # Works better if you give the full title of the product
    
    price_tracker(products=to_search, db_path=db_path)
