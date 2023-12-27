import pandas as pd
import requests
import json
import seaborn
import matplotlib.pyplot as plt
import warnings
import os
from dotenv import load_dotenv
warnings.filterwarnings("ignore")

load_dotenv()

DATE_BEGIN = os.getenv('DATE_BEGIN')
DATE_END = os.getenv('DATE_END')
API_URL = os.getenv('API_URL')


def run_all():
    visits = pd.read_csv(r'charts_project/data/visits_1k.csv')
    regs = pd.read_csv(r'charts_project/data/regs_1k.csv')
    v = requests.get(f'{API_URL}/visits?begin={DATE_BEGIN}&end={DATE_END}')
    vis = v.json()
    r = requests.get(f'{API_URL}/registrations?begin={DATE_BEGIN}&end={DATE_END}')
    reg = r.json()

    df_vis = pd.json_normalize(vis)
    df_vis = df_vis.loc[~df_vis['user_agent'].str.contains('bot')]
    df_reg = pd.json_normalize(reg)

    df_vis['datetime'] = pd.to_datetime(df_vis['datetime']).dt.date
    df_vis = df_vis.groupby(['datetime', 'platform', 'user_agent', 'visit_id'], as_index=False).agg({'datetime':'max'})
    df_vis = df_vis.groupby(['datetime', 'platform'], as_index=False).agg({'visit_id':'count'})

    df_reg['datetime'] = pd.to_datetime(df_reg['datetime']).dt.date
    df_reg = df_reg.groupby(['datetime', 'platform', 'registration_type'], as_index=False).agg({'user_id':'count'})

    mrg = pd.merge(df_vis, df_reg, on=['datetime','platform'], how='inner')
    mrg.rename(columns={'datetime':'date_group', 'visit_id':'visits', 'user_id':'registrations'}, inplace=True)
    mrg['conversion'] = mrg['registrations']/mrg['visits']
    mrg.sort_values(by='date_group', inplace=True)

    ads = pd.read_csv(r'charts_project/data/ads.csv')
    ads['date'] = pd.to_datetime(ads['date']).dt.date

    to_mrg = mrg.groupby(by='date_group', as_index=False).agg({'visits':'sum','registrations':'sum'})
    to_mrg_2 = ads.groupby(by=['date','utm_campaign'], as_index=False).agg({'cost':'sum'})
    fin = pd.merge(to_mrg, to_mrg_2, left_on='date_group', right_on='date', how='left')
    fin.drop('date', axis=1, inplace=True)
    fin.fillna('none', inplace=True)
    fin.sort_values(by='date_group', inplace=True)
    fin.to_json('ads.json')



    fig, ax = plt.subplots(figsize=(60, 10))
    dat = seaborn.barplot(data=mrg.groupby(by='date_group', as_index=False).agg({'visits':'sum'}), x='date_group' , y='visits', ax=ax)
    dat.set_xticklabels(dat.get_xticklabels(), rotation=45)
    dat.bar_label(ax.containers[0], fontsize=10)

    plt.savefig('./charts/total_visits.png')



    fig2, ax2 = plt.subplots(figsize=(60, 10))
    dat2 = mrg.groupby(by=['date_group','platform']).agg({'visits':'sum'}).unstack().plot(kind='bar', stacked=True, ax=ax2)
    ax2.legend(['android', 'ios', 'web'])

    plt.savefig('./charts/total_visits_by_platform.png')

    fig3, ax3 = plt.subplots(figsize=(60, 10))
    dat3 = seaborn.barplot(data=mrg.groupby(by='date_group', as_index=False).agg({'registrations':'sum'}), x='date_group' , y='registrations', ax=ax3)
    dat3.set_xticklabels(dat.get_xticklabels(), rotation=45)
    dat3.bar_label(ax3.containers[0], fontsize=10)

    plt.savefig('./charts/total_registrations.png')



    fig4, ax4 = plt.subplots(figsize=(60, 10))
    dat4 = mrg.groupby(by=['date_group','platform']).agg({'registrations':'sum'}).unstack().plot(kind='bar', stacked=True, ax=ax4)
    ax4.legend(['android', 'ios', 'web'])

    plt.savefig('./charts/total_registrations_by_platform.png')


    fig5, ax5 = plt.subplots(figsize=(60, 10))
    dat5 = mrg.groupby(by=['date_group','registration_type']).agg({'registrations':'sum'}).unstack().plot(kind='bar', stacked=True, ax=ax5)
    ax5.legend(['apple', 'email', 'google', 'yandex'])

    plt.savefig('./charts/total_registrations_by_type.png')


    fig6, ax6 = plt.subplots(figsize=(60, 10))
    dat6 = seaborn.lineplot(data=mrg.groupby(by='date_group', as_index=False).agg({'conversion':'mean'}), x='date_group' , y='conversion', ax=ax6)

    for x, y in zip(mrg.groupby(by='date_group', as_index=False).agg({'conversion':'mean'})['date_group'], mrg.groupby(by='date_group', as_index=False).agg({'conversion':'mean'})['conversion']):
        plt.text(x = x, y = y, s = '{:.2f}%'.format(y*100))


    plt.savefig('./charts/conversion.png')


    inf = mrg.groupby(by=['date_group','platform'], as_index=False).agg({'conversion':'mean'})
    inf['conversion'] = round(inf['conversion'],2)
    dat7 = seaborn.FacetGrid(inf, col='platform', col_wrap=1, aspect=3)

    dat7.map(seaborn.lineplot, 'date_group', 'conversion')

    def annotate_points(x,y,t, **kwargs):
        ax = plt.gca()
        data = kwargs.pop('data')
        for i,row in data.iterrows():
            ax.annotate(row[t], xy=(row[x],row[y]), fontsize=5)

    dat7.map_dataframe(annotate_points, "date_group", "conversion", 'conversion')

    plt.savefig('./charts/conversion_by_platforms.png')


    fin.groupby(by='utm_campaign', as_index=False).agg({'date_group':['min','max']})




    fig8, ax8 = plt.subplots(figsize=(60, 10))
    dat8 = seaborn.barplot(data=ads.groupby(by='date', as_index=False).agg({'cost':'sum'}), x='date' , y='cost', ax=ax8)
    dat8.set_xticklabels(dat8.get_xticklabels(), rotation=45)
    dat8.bar_label(ax8.containers[0], fontsize=10)

    plt.savefig('./charts/ads_cost.png')


    fig9, ax9 = plt.subplots(figsize=(60, 10))
    inf = fin.groupby(by='utm_campaign', as_index=False).agg({'date_group':['min','max']})
    dat9 = seaborn.lineplot(data=fin.groupby(by='date_group', as_index=False).agg({'visits':'sum'}),
                           x='date_group' , y='visits', ax=ax9, marker='o')

    colors=['b', 'g', 'r', 'c', 'm', 'y']
    for index, i in inf.iterrows():
        if i['utm_campaign'].iloc[0] == 'none':
            continue
        ax9.axvspan(xmin=i['date_group']['min'], xmax=i['date_group']['max'], alpha=0.2, facecolor =colors[index],
                   label=i['utm_campaign'].iloc[0])
    plt.legend(loc='upper right')

    plt.savefig('./charts/foo9.png')



    fig10, ax10 = plt.subplots(figsize=(60, 10))
    inf = fin.groupby(by='utm_campaign', as_index=False).agg({'date_group':['min','max']})
    dat10 = seaborn.lineplot(data=fin.groupby(by='date_group', as_index=False).agg({'registrations':'sum'}),
                           x='date_group' , y='registrations', ax=ax10, marker='o')

    colors=['b', 'g', 'r', 'c', 'm', 'y']
    for index, i in inf.iterrows():
        if i['utm_campaign'].iloc[0] == 'none':
            continue
        ax10.axvspan(xmin=i['date_group']['min'], xmax=i['date_group']['max'], alpha=0.2, facecolor =colors[index],
                   label=i['utm_campaign'].iloc[0])
    plt.legend(loc='upper right')
    plt.savefig('./charts/foo10.png')
