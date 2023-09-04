import os
import time
import datetime
import requests
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# CHROME_DRIVER_PATH = '/usr/lib/chromium-browser/chromedriver'
COINMARKETCAP_URL = 'https://coinmarketcap.com/'
COIN_HISTORICAL_URL = COINMARKETCAP_URL + 'historical/'
DATE = datetime.date(2023, 8, 25)
# DATE.strftime('%Y%m%d')

class Coin:
    def __init__(self, name, symbol, main_link, historical_link=None):
        self.name = name
        self.symbol = symbol
        self.main_link = main_link
        self.historical_link = historical_link

class CoinHistory:
    pass

class CoinScraper:
    def __init__(self, data_path=None):
        self.coins = None

        project_path = os.path.abspath(os.path.dirname(__file__))
        data_relative_path = 'data'

        if not data_path:
            self.data_path = os.path.join(project_path, data_relative_path)
        else:
            self.data_path = data_path
        
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)

        chrome_options = webdriver.ChromeOptions()
        prefs = {
            "download.default_directory": self.data_path,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": False,
        }
        chrome_options.add_experimental_option("prefs", prefs)

        # self.driver = webdriver.Chrome(CHROME_DRIVER_PATH, options=chrome_options)
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
    def __del__(self):
        self.driver.quit()
            
    def get_coins(self):
        self.driver.get(COIN_HISTORICAL_URL + DATE.strftime('%Y%m%d'))
        
        # Scroll down to trigger lazy loading
        x, y = 0, 1500
        for _ in range(6):  # Scroll down 6 times
            self.driver.execute_script("window.scrollTo({}, {});".format(x,y))
            x += 1500
            y += 1500
            time.sleep(1)  # Wait for the new content to load

        coins_table_head = self.driver.find_element_by_tag_name('thead')
        ths = coins_table_head.find_elements_by_tag_name('th')
        columns = list(map(lambda th: th.text, ths))
        coins_table = self.driver.find_element_by_tag_name('tbody')
        rows = coins_table.find_elements_by_tag_name("tr")

        self.coins = []
        print(len(rows))
        for i, row in enumerate(rows):
            if i % 10 == 0:
                y_position = row.location['y'] 
                # Scroll to the specific Y-coordinate position
                self.driver.execute_script("window.scrollTo(0, {});".format(y_position - 100))  
            tds = row.find_elements_by_tag_name('td')
            name = tds[columns.index('Name')].text
            symbol = tds[columns.index('Symbol')].text    
            main_link = tds[columns.index('Name')].find_element_by_tag_name('a').get_attribute('href')
            popover_cell = row.find_element(By.CSS_SELECTOR, ".sc-63cc44da-0.kHpXFp")
            popover_cell.click()
            dropdown_cell = popover_cell.find_element_by_class_name('cmc-popover__dropdown')
            historical_link = dropdown_cell.find_element_by_link_text('View Historical Data').get_attribute('href')
            popover_cell.click()
            # historical_link = main_link + 'historical-data/'
            self.coins.append(Coin(name, symbol, main_link, historical_link))
            
        return self.coins
    
    
    def download_historical_data(self, coin):
        self.driver.get(coin.historical_link)
        date_button = self.driver.find_elements_by_tag_name('button')[3]
        date_button.click()
        self.wait.until(EC.visibility_of_element_located((By.ID, 'tippy-1')))
        tippy = self.driver.find_element_by_id('tippy-1')
        tippy.find_elements_by_tag_name('li')[-1].click()
        tippy.find_elements_by_tag_name('button')[1].click()
        download_button = self.driver.find_elements_by_tag_name('button')[4]
        time.sleep(0.5)
        download_button.click()

    
    def get_coins_table(self):
        if not self.coins:
            self.get_coins()
        coins_table = pd.DataFrame(columns=['Rank', 'Name', 'Symbol', 'MainLink', 'HistoricalLink'])
        for i, coin in enumerate(self.coins):
            coins_table.loc[i] = [i+1, coin.name, coin.symbol, coin.main_link, coin.historical_link]
        return coins_table
    
    def cions_to_csv(self, file_name):
        if not self.coins:
            self.get_coins()
        coins_table = self.get_coins_table()
        path = os.path.join(self.data_path, file_name)
        coins_table.to_csv(path, index=False)
    

def main():
    cs = CoinScraper()
    cs.get_coins()
    cs.cions_to_csv('Coins.csv')
    for coin in cs.coins:
        cs.download_historical_data(coin)
        
if __name__ == '__main__':
    main()