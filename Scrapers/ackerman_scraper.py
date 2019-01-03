from bs4 import BeautifulSoup
import json
import pandas as pd
import requests
from pandas.io.json import json_normalize

ackerman_auction_url = 'https://www.ackerwines.com/AuctionArchives'
ackerman_current_auction_url = 'https://www.ackerwines.com/api/napalots/browse'
current_auction_post_header_template = {'Content-Type': 'application/json'}
current_auction_post_body_template = {
    "pageRequested": 1,
    "previousInitialLotId": "",
    "recordsRequested": 100,
    "sortBy": "lotNo",
    "isArchiveSearch": False,
    "auctionId": 1216,
    "auctionDateStart": "Sun Dec 31 2017 11:10:23 GMT-0700 (Mountain Standard Time)",
    "auctionDateEnd": "Mon Dec 31 2018 11:10:23 GMT-0700 (Mountain Standard Time)",
    "search": "",
    "upcomingBidsLock": False,
    "myBidsLock": False,
    "unformattedSearch": "",
    "myBids": False,
    "watchedLots": False,
    "lotsWithNoBidsOnly": False,
    "mixedLotsOnly": False,
    "newLotsOnly": False,
    "mixedLots": False,
    "favoriteProducers": False,
    "singleBottleLotsOnly": False,
    "owcOnly": False,
    "onlyNewlots": False,
    "vintages": [],
    "myBidsList": [],
    "regions": [],
    "prices": [],
    "bottleSizes": [],
    "locations": [],
    "jumpToLot": ""
}


def send_post_request(auction_id):
    """
    # Hits the ackerman auction url site with the post request corresponding to a particular auction. Returns raw html text
    """
    r = requests.post(ackerman_auction_url, data=dict(
        auction=auction_id
    ))
    return r.text


def send_active_auction_post_request(auction_id=1216, previousInitialLotId=''):
    """
    # Hits the ackerman active auction url site with the post request corresponding to 100 live auction lots. Returns raw html text
    """
    post_body = current_auction_post_body_template
    post_body['auctionId'] = auction_id
    post_body['previousInitialLotId'] = previousInitialLotId
    r = requests.post(ackerman_current_auction_url, headers=current_auction_post_header_template, json=post_body)
    return r.json()


def query_current_auction_results(auction_id):
    """
    For a given auction, the active auction rest endpoint paginates results, only returning 100 at a time.
    We need to iterate over all the paginated results and stitch them together
    """
    # Fire off the first set of paginated results
    lots_list = []
    current_payload = send_active_auction_post_request(auction_id)
    current_page = current_payload['currentPage']
    total_pages = current_payload['totalPage']
    has_next_lots = current_payload['hasNextLots']
    total_lots = current_payload['totalLots']
    lots_list += current_payload['auctionLots'][0]['lots']

    # The Rest endpoint takes a lot number n and returns the results for lots n+1 -> n+100
    while (has_next_lots):
        previousInitialLotId = lots_list[-1]['lotId']
        print('Querying current page', current_page,
              'Out of total pages', total_pages,
              'previousInitialLotId', previousInitialLotId,
              )
        current_payload = send_active_auction_post_request(auction_id, previousInitialLotId)
        current_page = current_payload['currentPage']
        has_next_lots = current_payload['hasNextLots']
        lots_list += current_payload['auctionLots'][0]['lots']

    # Confirm that the size of lots_list checks w/ the total_lots from the payload
    if (total_lots != len(lots_list)):
        raise ValueError('Missing Lots', total_lots, len(lots_list))

    return lots_list


def extract_auction_ids():
    """
    # Hits the auckerman auction url site to extract the list of all auctions
    """
    auction_html = send_post_request(1)
    auction_id_to_name_map = parse_auction_ids_from_soup(auction_html)

    # Auction ID = 0 doesn't correspond to an actual auction
    del auction_id_to_name_map[0]
    return auction_id_to_name_map


def parse_auction_ids_from_soup(raw_html):
    """
    # Look for the auction archives tag in the soup. The option values correspond to auction ids and names
    # Return a map of auction id to auction name
    """
    soup = BeautifulSoup(raw_html, 'html.parser')
    auction_archive_tag = soup.find_all('div', id='auctionarchives-container')
    auction_select = auction_archive_tag[0].find('select', {'name': 'auction'})
    all_auctions = auction_select.find_all('option')

    auction_id_to_name_map = {}
    for auction in all_auctions:
        id = int(auction.attrs['value'])
        auction_name = auction.text
        auction_id_to_name_map[id] = auction_name

    return auction_id_to_name_map


def extract_df_from_html(raw_html):
    """
    # The entire datapayload exists in a javascript variable called siteLayoutModel
    # Extract the variable element and convert it into a json payload
    # Conevrt the json payload into a dataframe
    """
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
        # print(df.shape)
        # print(df.head())
        # print(df.tail())
    df = pd.concat(df_per_auction_id_list)
    return df

def dataframe_current_auction(auction_id):
    """
    For a given auction, scrapes the current bid information flattens to df
    """
    current_auction_scrape = query_current_auction_results(auction_id)
    current_auction_df_full = pd.DataFrame(current_auction_scrape)
    return current_auction_df_full

# df = dataframe_ackerman_auction()
#current_auction_scrape = query_current_auction_results(1216)
#print(current_auction_scrape)
