from flask import *
import pandas as pd
app = Flask(__name__)
import json
import urllib3
from datetime import datetime


@app.route("/tables")
def show_tables():
    # ------- Get Todays Date
    i = datetime.now()
    now = i.strftime('%Y-%m-%d ')

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
    new_data = pd.concat([cryptocurrency_final,data.loc[data.Type == 'Deposit']])

    new_data.set_index(['Name'], inplace=True)
    new_data.index.name=None
    cryptocurrency = new_data.loc[new_data.Type == 'Cryptocurrency']
    deposit = new_data.loc[new_data.Type == 'Deposit']
    return render_template('view.html', tables=[cryptocurrency.to_html(classes='Cryptocurrency'),
                                                deposit.to_html(classes='Deposit')],
                           titles=['na', 'Cryptocurrencies', 'Deposits'])

if __name__ == "__main__":
    app.run(debug=True)