from bs4 import BeautifulSoup
import json
import pandas as pd
import requests
from pandas.io.json import json_normalize

ackerman_auction_url = 'https://www.ackerwines.com/AuctionArchives'

# Hits the ackerman auction url site with the post request corresponding to a particular auction. Returns raw html text
def send_post_request(auction_id):
    r = requests.post(ackerman_auction_url, data=dict(
        auction=auction_id
    ))
    return r.text

# Hits the auckerman auction url site to extract the list of all auctions
def extract_auction_ids():
    auction_html = send_post_request(1)
    auction_id_to_name_map = parse_auction_ids_from_soup(auction_html)

    # Auction ID = 0 doesn't correspond to an actual auction
    del auction_id_to_name_map[0]
    return auction_id_to_name_map

# Look for the auction archives tag in the soup. The option values correspond to auction ids and names
# Return a map of auction id to auction name
def parse_auction_ids_from_soup(raw_html):
    soup = BeautifulSoup(raw_html, 'html.parser')
    auction_archive_tag = soup.find_all('div', id='auctionarchives-container')
    auction_select = auction_archive_tag[0].find('select', {'name':'auction'})
    all_auctions = auction_select.find_all('option')

    auction_id_to_name_map = {}
    for auction in all_auctions:
        id = int(auction.attrs['value'])
        auction_name = auction.text
        auction_id_to_name_map[id] = auction_name

    return auction_id_to_name_map

# The entire datapayload exists in a javascript variable called siteLayoutModel
# Extract the variable element and convert it into a json payload
# Conevrt the json payload into a dataframe
def extract_df_from_html(raw_html):
    soup = BeautifulSoup(raw_html, 'html.parser')

    text_to_find = 'ArchivedLots'
    scripts = soup.find_all('script')

    for script in scripts:
        if text_to_find in script.text:
            siteLayoutModel_payload = script.text
    siteLayoutModel_payload = siteLayoutModel_payload.replace('var siteLayoutModel = ', '')
    siteLayoutModel_payload = siteLayoutModel_payload.replace(';', '')

    siteLayoutModel_json = json.loads(siteLayoutModel_payload)

    archivedLots_json = siteLayoutModel_json['ArchivedLots']
    df = pd.DataFrame.from_dict(json_normalize(archivedLots_json), orient='columns')

    return df

def dataframe_ackerman_auction():
    auction_id_to_name_map = extract_auction_ids()
    print(auction_id_to_name_map)

    df_per_auction_id_list = []
    for auction_id, auction_name in auction_id_to_name_map.items():
        print(auction_id, auction_name)
        auction_html = send_post_request(auction_id)
        df = extract_df_from_html(auction_html)
        df_per_auction_id_list.append(df)
        #print(df.shape)
        #print(df.head())
        #print(df.tail())
    df = pd.concat(df_per_auction_id_list)
    return df

#df = dataframe_ackerman_auction()
