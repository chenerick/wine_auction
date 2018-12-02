import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")
from scipy import stats
import datetime as dt
import pandas as pd

date_col = 'Date'
vintage_col = 'Vintage'
wine_col = 'Wine'
producerdesignation_col = 'ProducerAndDesignation'
unit_price_col = 'UnitPriceUSD'
annual_percent_change_col = 'Annual Percent Change'
unique_bottle_keys = ['Vintage', "Wine", "ProducerAndDesignation"]


'''
Given a bottle_df of many unique bottles and price time series, plots one time series per bottle on 1 chart.
Be careful to only give this a reasonable number of unique bottles
'''
def plot_price_over_time(bottle_df):
    fig, ax = plt.subplots()
    for unique_bottle_key, grp in bottle_df.groupby(unique_bottle_keys):
        ax = grp.plot(ax=ax, kind='line', x=date_col, y=unit_price_col, label=unique_bottle_key)
    plt.legend(loc='best')
    plt.show()

'''
Given the price time series for a single bottle type, finds the slope of the linear regression
of price(ordinal date). Annualizes and normalizes the slope into % change/1 year
'''
def regress_bottle_price_time(bottle_df):
    y = bottle_df[unit_price_col]
    x = bottle_df[date_col].map(dt.datetime.toordinal)
    slope, intercept, r_value, p_value, std_err = stats.linregress(x,y)
    # Slope represents the marginal price change $ / 1 day
    # Annualize the slope to marginal price change $ / 1 year.
    # Normalize by the first observed price to get price change % / 1 year
    marginal_dollar_per_year = slope * 365
    first_price = float(bottle_df.sort_values(by=date_col).head(1)[unit_price_col])
    annualized_price_change = marginal_dollar_per_year / first_price
    #print(slope, intercept, r_value, p_value, std_err)
    #print(marginal_dollar_per_year, first_price, annualized_price_change)
    return annualized_price_change

'''
Given a bottle_df, for each unique_bottle_key computes the normalized price percent change
Enriches each row of bottle_df with the percent change for that bottle key
Removes all bottles of w/ fewer than count_threshold observations
'''
def enrich_bottle_price_percent_change(bottle_df, count_threshold = 25):
    # Start w/ the bottle dataframe - all lots of just type. UnitPriceUSD represents the per bottle price
    # Treat each lot as an individual observation. Get the slope of Price(Time). Slope will represent the marginal change in price per marginal change in time
    bottle_grouped = bottle_df.groupby(unique_bottle_keys).UnitPriceUSD.agg(['min', 'mean', 'max', "count"])
    # bottle_df.head()
    bottle_grouped = bottle_grouped.sort_values('count', ascending=False)
    # bottle_grouped.head()
    # Join the ungrouped df with the grouped attributes.
    bottle_df_with_grouped_attr = pd.merge(bottle_df, bottle_grouped.reset_index(), on=unique_bottle_keys)
    bottle_df_with_grouped_attr = bottle_df_with_grouped_attr.sort_values('count', ascending=False)

    # Only keep bottles that appear in more than count_threshold lots
    count_col = 'count'
    high_count_bottles = bottle_df_with_grouped_attr[bottle_df_with_grouped_attr[count_col] >= count_threshold]
    # show high count bottles w/ annual percent change
    # Compute the normalized slope for each high count bottle and stitch together w/ grouped attributes
    bottle_grouped_percent_change = high_count_bottles.groupby(unique_bottle_keys).apply(
        lambda x: pd.Series({annual_percent_change_col: regress_bottle_price_time(x)}))
    bottle_grouped_percent_change = pd.merge(bottle_grouped.reset_index(), bottle_grouped_percent_change.reset_index(),
                                             on=unique_bottle_keys)
    bottle_grouped_percent_change = bottle_grouped_percent_change.sort_values(annual_percent_change_col, ascending=False)

    return bottle_grouped_percent_change
