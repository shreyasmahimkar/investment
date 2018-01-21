from flask import *
import pandas as pd
app = Flask(__name__)
import json
import urllib3
from datetime import datetime
from forex_python.converter import CurrencyRates


@app.route("/tables")
def show_tables():
    # ------- Get Todays Date
    i = datetime.now()
    now = i.strftime('%Y-%m-%d ')
    c = CurrencyRates()

    data = pd.read_excel('data.xlsx')
    cryptocurrency_temp = data.loc[data.Type == 'Cryptocurrency']
    ## Get todays Value of cryptocurrencies
    http = urllib3.PoolManager()
    r = http.request('GET', 'https://api.coinmarketcap.com/v1/ticker/')
    all_data = json.loads(r.data.decode('utf-8'))
    all_data_df = pd.DataFrame(all_data)

    cryptocurrency_popular = cryptocurrency_temp.merge(all_data_df[['id','price_usd']],left_on='Name',right_on='id',how='inner')
    cryptocurrency_popular.Units = cryptocurrency_popular.Units.apply(float)
    cryptocurrency_popular.price_usd = cryptocurrency_popular.price_usd.apply(float)
    cryptocurrency_popular.Todays_Value = cryptocurrency_popular.price_usd * cryptocurrency_popular.Units
    cryptocurrency_popular.drop(['id', 'price_usd'], axis=1, inplace=True)
    cryptocurrency_popular.Maturity_Date = now

    cryptocurrency_ico = cryptocurrency_temp[~cryptocurrency_temp.Name.isin(cryptocurrency_popular.Name.unique())]
    cryptocurrency_ico.Maturity_Date = 'TBD'
    cryptocurrency_final = pd.concat([cryptocurrency_popular,cryptocurrency_ico])

    deposit_temp = data.loc[data.Type == 'Deposit']
    deposit_temp.Currency = 'USD'
    deposit_temp.Money_Invested = deposit_temp.Money_Invested / c.get_rate('USD', 'INR')
    deposit_temp.Todays_Value = deposit_temp.Todays_Value / c.get_rate('USD', 'INR')



    new_data = pd.concat([cryptocurrency_final,deposit_temp])

    new_data.set_index(['Name'], inplace=True)
    new_data.index.name=None
    cryptocurrency = new_data.loc[new_data.Type == 'Cryptocurrency']
    deposit = new_data.loc[new_data.Type == 'Deposit']

    total = new_data.groupby('Currency').agg({'Money_Invested': 'sum', 'Todays_Value': 'sum'}).reset_index()
    return render_template('view.html', tables=[total.to_html(classes='Total'),
                                                cryptocurrency.to_html(classes='Cryptocurrency'),
                                                deposit.to_html(classes='Deposit')],
                           titles=['na', 'Total' ,'Cryptocurrencies', 'Deposits'])

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0')