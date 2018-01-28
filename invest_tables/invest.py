from flask import *
import pandas as pd
app = Flask(__name__)
import json
import urllib3
from datetime import datetime
from forex_python.converter import CurrencyRates

i = datetime.now()
now = i.strftime('%Y-%m-%d ')
data = pd.read_excel('data.xlsx')

def get_monthly_investment_factor(date_of_investment):
    monthly_investment_factor = pd.to_datetime(now) - pd.to_datetime(date_of_investment)
    mif = monthly_investment_factor.days // 30.0
    return mif

def get_cryptocurrency(df):
    cryptocurrency_temp = df.loc[df.Type == 'Cryptocurrency']
    ## Get todays Value of cryptocurrencies
    http = urllib3.PoolManager()
    r = http.request('GET', 'https://api.coinmarketcap.com/v1/ticker/')
    all_data = json.loads(r.data.decode('utf-8'))
    all_data_df = pd.DataFrame(all_data)

    cryptocurrency_popular = cryptocurrency_temp.merge(all_data_df[['id', 'price_usd']], left_on='Name', right_on='id',
                                                       how='inner')
    cryptocurrency_popular.Units = cryptocurrency_popular.Units.apply(float)
    cryptocurrency_popular.price_usd = cryptocurrency_popular.price_usd.apply(float)
    cryptocurrency_popular.Todays_Value = cryptocurrency_popular.price_usd * cryptocurrency_popular.Units
    cryptocurrency_popular.drop(['id', 'price_usd'], axis=1, inplace=True)
    cryptocurrency_popular.Maturity_Date = now

    cryptocurrency_ico = cryptocurrency_temp[~cryptocurrency_temp.Name.isin(cryptocurrency_popular.Name.unique())]
    cryptocurrency_ico.Maturity_Date = 'TBD'
    cryptocurrency_final = pd.concat([cryptocurrency_popular, cryptocurrency_ico])
    return cryptocurrency_final


@app.route("/cryptocurrency")
def show_cryptocurrency():
    df = data.copy()
    # Cryptocurrency
    cryptocurrency_final = get_cryptocurrency(df)
    new_data = pd.concat([cryptocurrency_final])
    new_data.set_index(['Name'], inplace=True)
    new_data.index.name = None
    cryptocurrency = new_data.loc[new_data.Type == 'Cryptocurrency']
    total = new_data.groupby('Currency').agg({'Money_Invested': 'sum', 'Todays_Value': 'sum'}).reset_index()
    total = total[['Currency', 'Money_Invested', 'Todays_Value']]
    return  render_template('view.html', tables=[total.to_html(classes='Total'),
                                                cryptocurrency.to_html(classes='Cryptocurrency')],
                           titles=['na', 'Total' ,'Cryptocurrencies'])

@app.route("/tables")
def show_tables():
    # ------- Get Todays Date
    c = CurrencyRates()
    df = data.copy()

    #Cryptocurrency
    cryptocurrency_final = get_cryptocurrency(df)

    #Deposit - RD FD ICICI
    deposit_temp = data.loc[data.Type == 'Deposit']
    deposit_temp.Currency = 'USD'
    deposit_temp.Money_Invested = deposit_temp.Money_Invested / c.get_rate('USD', 'INR')
    deposit_temp.Todays_Value = deposit_temp.Todays_Value / c.get_rate('USD', 'INR')

    #Acorns Investment
    acorns_data = data.loc[data.Type == 'Acorns']
    mif = get_monthly_investment_factor(acorns_data.Date_of_Investment.values[0])
    acorns_data.Money_Invested = acorns_data.Money_Invested + (mif * 100.0)
    acorns_data.Todays_Value = acorns_data.Money_Invested + (acorns_data.Money_Invested * 3) / 100.0
    acorns_data.Maturity_Date = now

    #Fundrise Investment
    fundrise_data = data.loc[data.Type == 'Fundrise']
    mif = get_monthly_investment_factor(fundrise_data.Date_of_Investment.values[0])
    fundrise_data.Money_Invested = fundrise_data.Money_Invested + (mif * 100.0)
    fundrise_data.Todays_Value = fundrise_data.Money_Invested + (fundrise_data.Money_Invested * 0.7) / 100.0

    #LendingClub Investment
    lendingClub_data = data.loc[data.Type == 'LendingClub']
    mif = get_monthly_investment_factor(lendingClub_data.Date_of_Investment.values[0])
    lendingClub_data.Money_Invested = lendingClub_data.Money_Invested + (mif * 100.0)
    lendingClub_data.Todays_Value = lendingClub_data.Money_Invested + ((lendingClub_data.Money_Invested * 5.61) / 1200.0) * 0

    new_data = pd.concat([cryptocurrency_final,deposit_temp,acorns_data,fundrise_data,lendingClub_data])

    new_data.set_index(['Name'], inplace=True)
    new_data.index.name=None
    cryptocurrency = new_data.loc[new_data.Type == 'Cryptocurrency']
    deposit = new_data.loc[new_data.Type == 'Deposit']
    acorns = new_data.loc[new_data.Type == 'Acorns']
    fundrise = new_data.loc[new_data.Type == 'Fundrise']
    lendingClub = new_data.loc[new_data.Type == 'LendingClub']

    total = new_data.groupby('Currency').agg({'Money_Invested': 'sum', 'Todays_Value': 'sum'}).reset_index()
    total = total[['Currency', 'Money_Invested', 'Todays_Value']]
    return render_template('view.html', tables=[total.to_html(classes='Total'),
                                                cryptocurrency.to_html(classes='Cryptocurrency'),
                                                deposit.to_html(classes='Deposit'),
                                                acorns.to_html(classes='Acorns'),
                                                fundrise.to_html(classes='Fundrise'),
                                                lendingClub.to_html(classes='LendingClub')],
                           titles=['na', 'Total' ,'Cryptocurrencies', 'Deposits','Acorns','Fundrise','LendingClub'])

if __name__ == "__main__":
    #app.run(debug=True,host='0.0.0.0')
    app.run(debug=True)