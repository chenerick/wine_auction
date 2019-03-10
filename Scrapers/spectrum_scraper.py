from bs4 import BeautifulSoup
import json
import pandas as pd
import requests
from pandas.io.json import json_normalize

class SpectrumScraper:
    def __init__(self, auction_url_list = None):
        self.auction_url_list = auction_url_list if auction_url_list else self.generate_default_auction_url_list()
        self.spectrum_url_base = 'https://ssl.spectrumwine.com'
    def generate_default_auction_url_list(self):
        pass

    def get_auction_raw_html(self, url):
        '''
        Recursive function for hitting all the pages of an auction. Goes to a page, grabs the raw html, attempts to
        find the url for the next button. Recursively calls itself on the next page url
        '''
        print('Getting URL:', url)
        r = requests.get(url)
        next_page_url = self.find_next_page_url(r.text)
        if next_page_url is not None:
            next_page_raw_html = self.get_auction_raw_html(next_page_url)
            return [r.text] + next_page_raw_html
        else:
            return([r.text])

    def find_next_page_url(self, text):
        soup = BeautifulSoup(text, 'html.parser')
        next_page_tag = soup.find_all('a', title = 'Next Page')
        #While we can find a next page link
        if(next_page_tag[0].has_attr('href')):
            #next_page_tag only contains the relative link. Need to append to the domain name
            formatted_url = self.spectrum_url_base + next_page_tag[0]['href']
            return(formatted_url)
        else:
            return(None)

    def parse_raw_html(self, raw_html_auction_pages):
        '''
        Parse the raw html for a single auction, which contains a list of pages
        '''
        parsed_html_auct = list(map(self.parse_single_auction_page_raw_html, raw_html_auction_pages))
        # List of parsed pages, fold them together
        return parsed_html_auct

    def parse_single_auction_page_raw_html(self, raw_html_page):
        soup = BeautifulSoup(raw_html_page, 'html.parser')
        #Only grab the table rows we care about
        rows = soup.find_all('tr', id=lambda id: id and "ctl00_cphContent_ucAuctionLots1_dgLots_ctl00__" in id)
        parsed_rows = [[field.text for field in row.findAll(['a', 'span'])] for row in rows]

        return(parsed_rows)

#test_url = ['https://ssl.spectrumwine.com/auctions/AuctionLots.aspx?AuctionID=543&SessionID=797']
test_url = 'https://ssl.spectrumwine.com/auctions/AuctionLots.aspx?AuctionID=543&SessionID=797&ctl00_cphContent_ucAuctionLots1_dgLotsChangePage=90_50'

spectrum_scraper = SpectrumScraper([test_url])
print( 'p1', spectrum_scraper.auction_url_list )
raw_html_auction_list = spectrum_scraper.get_auction_raw_html(test_url)
print(len(raw_html_auction_list))
parsed_auction_list = spectrum_scraper.parse_raw_html(raw_html_auction_list)
print(parsed_auction_list)
#df_auction = spectrum_scraper.convert_to_dataframe(parsed_auction_list)

