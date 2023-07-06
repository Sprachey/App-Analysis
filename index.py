from flask import Flask, render_template
import pandas as pd
import plotly.express as px
import plotly.io as pio


app = Flask(__name__)
app.debug = True

pd.options.display.float_format = '{:,.2f}'.format

df_apps = pd.read_csv('data/apps.csv')

df_apps.drop(['Last_Updated', 'Android_Ver'], axis=1, inplace=True)

nan_rows = df_apps[df_apps.Rating.isna()]

df_apps_clean = df_apps.dropna()

duplicated_rows = df_apps_clean[df_apps_clean.duplicated()]

df_apps_clean = df_apps_clean.drop_duplicates(subset=['App', 'Type', 'Price'])
df_apps_clean[df_apps_clean.App == 'Instagram']


M_ra_apps=df_apps_clean.sort_values('Rating', ascending=False).head()

lrg_apps=df_apps_clean.sort_values('Size_MBs', ascending=False).head()

M_rev_apps=df_apps_clean.sort_values('Reviews', ascending=False).head()

ratings = df_apps_clean.Content_Rating.value_counts()

df_apps_clean[['App', 'Installs']].groupby('Installs').count()

df_apps_clean.Installs = df_apps_clean.Installs.astype(str).str.replace(',', "")
df_apps_clean.Installs = pd.to_numeric(df_apps_clean.Installs)
df_apps_clean[['App', 'Installs']].groupby('Installs').count()

df_apps_clean.Price = df_apps_clean.Price.astype(str).str.replace('$', "")
df_apps_clean.Price = pd.to_numeric(df_apps_clean.Price)
df_apps_clean.sort_values('Price', ascending=False).head(20)

df_apps_clean = df_apps_clean[df_apps_clean['Price'] < 250]
df_apps_clean.sort_values('Price', ascending=False).head(5)

df_apps_clean['Revenue_Estimate'] = df_apps_clean.Installs.mul(df_apps_clean.Price)
h_paid_apps=df_apps_clean.sort_values('Revenue_Estimate', ascending=False)[:10]

top10_category = df_apps_clean.Category.value_counts()[:10]

category_installs = df_apps_clean.groupby('Category').agg({'Installs': pd.Series.sum})
category_installs.sort_values('Installs', ascending=True, inplace=True)

cat_number = df_apps_clean.groupby('Category').agg({'App': pd.Series.count})
cat_merged_df = pd.merge(cat_number, category_installs, on='Category', how="inner")
cat_merged_df.sort_values('Installs', ascending=False)

stack = df_apps_clean.Genres.str.split(';', expand=True).stack()
num_genres = stack.value_counts()

df_free_vs_paid = df_apps_clean.groupby(["Category", "Type"],
                                      as_index=False).agg({'App': pd.Series.count})

@app.route('/')
def home():
    fig = px.pie(labels=ratings.index, 
             values=ratings.values,
             title="Content Rating",
             names=ratings.index,
             hole=0.6)
    fig.update_traces(textposition='inside', textfont_size=15, textinfo='percent')
    
    graph_jsonbr=pio.to_json(fig)
    return render_template('layouts/index.html',ddata=df_apps.sample(10).to_html(),cdata=df_apps_clean.sample(10).to_html(),graph_jsonbr=graph_jsonbr)

@app.route('/stats')
def basic_stats():
    dstats=df_apps.describe()
    cstats=df_apps_clean.describe()
    return render_template('layouts/statistics.html',dstats_table=dstats.to_html(),cstats_table=cstats.to_html(),
                          M_ra_apps=M_ra_apps.to_html(),
                           M_rev_apps=M_rev_apps.to_html(),
                            lrg_apps=lrg_apps.to_html(),
                          h_paid_apps=h_paid_apps.to_html()    )

@app.route('/data')
def used_data():

    return render_template('layouts/UsedData.html',data_table=df_apps_clean.to_html())

@app.route('/graphs')
def graph():
    fig1 = px.pie(labels=ratings.index, 
             values=ratings.values,
             title="Content Rating",
             names=ratings.index)
    fig1.update_traces(textposition='outside', textinfo='percent+label')
    graph_json1=pio.to_json(fig1)

    bar = px.bar(
        x = top10_category.index, # index = category name
        y = top10_category.values)
    graph_json2=pio.to_json(bar)

    h_bar = px.bar(
        x = category_installs.Installs,
        y = category_installs.index,
        orientation='h',
        title='Category Popularity')
    h_bar.update_layout(xaxis_title='Number of Downloads', yaxis_title='Category')
    graph_json3=pio.to_json(h_bar)

    scatter = px.scatter(cat_merged_df, # data
                     x='App', # column name
                     y='Installs',
                     title='Category Concentration',
                     size='App',
                     hover_name=cat_merged_df.index,
                     color='Installs') 
    scatter.update_layout(xaxis_title="Number of Apps (Lower=More Concentrated)",
                      yaxis_title="Installs",
                      yaxis=dict(type='log'))
    graph_json4=pio.to_json(scatter)

    box = px.box(df_apps_clean, 
             y='Installs',
             x='Type',
             color='Type',
             notched=True,
             points='all',
             title='How Many Downloads are Paid Apps Giving Up?')

    box.update_layout(yaxis=dict(type='log'))
    graph_json5=pio.to_json(box)

    agbar = px.bar(
        x = num_genres.index[:15], # index = category name
        y = num_genres.values[:15], # count
        title='Top Genres',
        hover_name=num_genres.index[:15],
        color=num_genres.values[:15],
        color_continuous_scale='Agsunset')

    agbar.update_layout(xaxis_title='Genre',
                  yaxis_title='Number of Apps',
                  coloraxis_showscale=False)
    graph_json6=pio.to_json(agbar)

    g_bar = px.bar(df_free_vs_paid,
               x='Category',
               y='App',
               title='Free vs Paid Apps by Category',
               color='Type',
               barmode='group',)

    g_bar.update_layout(xaxis_title='Category',
                    yaxis_title='Number of Apps',
                    xaxis={'categoryorder':'total descending'},
                    yaxis=dict(type='log'),
                    )
    graph_json7=pio.to_json(g_bar)

    return render_template('layouts/Graph.html',
                           graph_json1=graph_json1,
                           graph_json2=graph_json2,
                           graph_json3=graph_json3,
                           graph_json4=graph_json4,
                           graph_json5=graph_json5,
                           graph_json6=graph_json6,
                           graph_json7=graph_json7
                           )


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
