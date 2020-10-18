import requests
import pandas as pd
import smtplib
from glob import glob
from bs4 import BeautifulSoup
from datetime import datetime
from time import sleep

headers = ({'User-Agent':
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Safari/605.1.15',
            'Accept-Language': 'en-US, en;q=0.5'})

def send_email(url):
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    
    server.login('frankchou0424@gmail.com', 'tzddphcsuhnncxef')

    subject = 'Price below threshold'
    body = url

    msg = f"Subject: {subject}\n\n{body}"

    server.sendmail(
        'frankchou0424@gmail.com',
        'zhou26276719@gmail.com',
        msg
    )

    print('email sent')

    server.quit()

    


def search_product_list(interval_count, interval_hours):
    """
    This function loads a csv file named products.csv, with headers: [url, code, buy_below]
    
    It also requires a file called search_history.xslx under the folder ./search_history to start saving the results.
    An empty file can be used on the first time using the script.

    Both the old and new resulkts are then saved in a new file named search_history_{datetime}.xlsx
    This is the file the script will use to gewt the history next time it runs.

    Args:
        interval_count (optional type): The number of iterations for the script to run a search on the product list.
        interval_hours (optional type): 

    Returns:
    New .xlsx file with previous search history and results form current search
    """
    # import csv file containing url of our desired products
    prod_tracker = pd.read_csv('trackers/products.csv', sep=';')
    prod_tracker_URLS = prod_tracker.url
    tracker_log = pd.DataFrame()
    now = datetime.now().strftime('%Y-%m-%d %Hh%Mm')
    interval = 0

    while interval < interval_count:

        for x, url in enumerate(prod_tracker_URLS):

            # fetch the url
            page = requests.get(url, headers=headers)

            # create beautiful soup object that contain info to the url
            soup = BeautifulSoup(page.content, features="lxml")

            # product title
            title = soup.find(id='productTitle').get_text().strip()

            # price of product
            try:
                price = float(soup.find(id='priceblock_saleprice').get_text().replace('$', '').replace(',', '').strip())
            except:
                price = ''

            # check if product is out of stock
            try:
                soup.select('#availability .a-color-state')[0].get_text().strip()
                stock = 'Out of Stock'
            except:
                # checking if there is "Out of stock" on a second possible position
                try:
                    soup.select('#availability .a-color-price')[0].get_text().strip()
                    stock = 'Out of Stock'
                except:
                    # if there is any error in the previous try statements, it means the product is available
                    stock = 'Available'
            
            log = pd.DataFrame({'date': now.replace('h',':').replace('m',''),
                                'code': prod_tracker.code[x], # this code comes from the TRACKER_PRODUCTS file
                                'url': url,
                                'title': title,
                                'buy_below': prod_tracker.buy_below[x], # this price comes from the TRACKER_PRODUCTS file
                                'price': price,
                                'stock': stock}, index = [x])

            try:
                if price < prod_tracker.buy_below[x]:
                    send_email(url)
            except:
                pass

            tracker_log = tracker_log.append(log)
            print('added '+ prod_tracker.code[x] +'\n' + title + '\n\n')
            sleep(1)

        interval += 1

        sleep(interval_hours*1*1)
        print('end of interval '+ str(interval))

    last_search_path = 'C:/Users/frankchou/Desktop/amazon-price-tracker/search_history/*.xlsx'
    last_search = glob(last_search_path, recursive=True)[-1] # path to file in the folder
    
    search_hist = pd.read_excel(last_search)
    final_df = search_hist.append(tracker_log, sort=False)
    
    final_df.to_excel('search_history/search_history_{}.xlsx'.format(now), index=False)
    print('end of search')


search_product_list(1, 6)