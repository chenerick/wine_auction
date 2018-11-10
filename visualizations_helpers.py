import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")
from scipy import stats
import datetime as dt

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