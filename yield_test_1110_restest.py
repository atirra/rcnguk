from lxml import html
import requests
from urllib.parse import urljoin
import pandas as pd
import re
from datetime import datetime

def rules():
    """
    The 1st Filter: 
        • Ensure that the said horse lies within the top 3 in terms of betting forecast.
        • Ensure the odds are less than 5/1 or 6.0 on Betfair.
    The 2nd Filter: 
        • If the horse is favourite add 2 Marks.
        • If horse is second/joint first favourite add 1 Mark.
        • If the horse lies outside first two betting positions subtract 1 Mark
    The 3rd Filter: 
        • If the horse has ran in the last 5 days add 1 Mark.
        • If the horse hasn’t ran in the last 5 days subtract 1 Mark.
    The 4th Filter: 
        • If the horse has won in his last 3 runs award 2 Marks.
        • If the horse hasn't won in his last 3 runs subtract 1 Mark.
    The 5th Filter: 
        • If the horse has won over this ground before (i.e. hard/soft/good) award 3 Marks.
        • If horse has won over similar ground add 1 Mark.
        • If horse hasn’t won over same/similar ground subtract 2 Marks
    The 6th Filter: 
        • If the horse has won at this course before award 2 Marks.
        • If horse has came 2nd at this course award 1 Mark.
        • If horse has done neither, subtract 2 Marks.

    Once you have gone through the selection process, any horse that has +3 Marks and
    above, you leave alone! In other words, the higher the Negative (-) Mark, the better
    chances of the horse losing, and you should Lay those horses! """

race_cols = [
    'Date','Time','City',
    'RaceID','Course','Distance','Yards',
    'Runners','Horse','Sex','Form','Lastrun',
    'Timeform','OR','Odds','LayRate','Placed']

race = {
    'date'      :   '',
    'time'      :   '',
    'city'      :   '',
    "raceid"    :   '',
    'course'    :   '',
    'dist'      :   '',
    'yards'     :   '',
    'runners'   :   '',
    'h_name'    :   '',
    'h_sex'     :   '', # sex female/male
    'h_form'    :   '',
    'h_lastr'   :   '', # last run 3 days ago
    'h_tform'   :   '', # timeform 1,2,3
    'h_OR'      :   '',
    'h_odds'    :   '',
    'h_myrt'    :   '',  # my LAY rate
    'h_placed'  :   '' }

df_temp = pd.DataFrame(columns=race_cols)
df_race = pd.DataFrame(columns=race_cols)
# df_race = pd.DataFrame(race, columns=race_cols)

def calc_yards(distance):
    miles = re.search(r'([0-9]*)M', distance)
    furls = re.search(r'([0-9]*)F', distance)
    yards = re.search(r'([0-9]*)Y', distance)
    if miles: miles = int(miles.group(1))*1760 
    else: miles = 0
    if furls: furls = int(furls.group(1))*220
    else: furls = 0
    if yards: yards = int(yards.group(1))
    else: yards = 0
    # print ('m:',miles,'f:',furls,'y:',yards)
    newdist = miles + furls + yards
    return newdist
""" 
nr_user = input('City# Race#: ')
try: 
    nr_city = int(nr_user[:1])
    nr_race = int(nr_user[1:])
except:
    nr_city=int(-1)
    nr_race=int(-1)
 """
nr_city=4 
nr_race=7
print('City# Race#:',nr_city,nr_race)

# today = str(datetime.date.today())
# xlsxname = today
""" 
df = pd.DataFrame(data=race)

try:
    dfs = pd.read_excel(xlsxname, sheet_name=None)
except:
    print ('no file')
else:
    print('file open')
"""

url_lnk = 'https://www.racinguk.com/racecards'
countries = ['gbr','ire']
min_runners = 0
max_odds = 0

# today_races = '/ul/li/div[@class="race-selector__race"]'
today_races = '/html/body/div[1]/div/div/div[2]/div/div/div[3]/ul/li/div[@class="race-selector__race"]'
race_cntry = './div/div/svg[contains(@class,"svg-flag_")]/@class'
race_times = './div[@class="race-selector__times"]/a'

page = requests.get (url_lnk)
tree = html.fromstring (page.text)
race_cities = tree.xpath (today_races)

print ('-----------------------------------------------------------')

for city_cnt, race_filt in enumerate(race_cities):
    if nr_city != -1 and nr_city != city_cnt: continue
    act_cntry = race_filt.xpath(race_cntry)[0].split(' ')[1][-3:]
    if act_cntry not in countries: continue # SAR, FRA, HGK or another non-UK excluded
    all_races = race_filt.xpath(race_times)

    for race_cnt, race in enumerate (all_races):
        if nr_race != -1 and nr_race != race_cnt: continue

        r_lnk = race.xpath('@href')
        # print(r_link, r_link.extract())
        race_link = urljoin(url_lnk, r_lnk[0])
        race_time = race.xpath('text()')

        c_r_id = re.search(r'\/(\d+)', r_lnk[0]).groups() # Race_ID ++++
        df_temp.loc[0,'RaceID'] = c_r_id[0]

        race_page = requests.get(race_link)
        act_race = html.fromstring(race_page.text)

        c_race = act_race.xpath('/html/body/div[1]/div/div/div[2]/div[@class="columns__main"]/div[@class="race-selector"]')
        c_name = act_race.xpath('.//div[@class="race-selector__venue"]/a/text()')
        df_temp.loc[0,'City'] = act_cntry.upper() + ' | ' + c_name[0]
        c_date = act_race.xpath('.//div/div[@class="race-selector__icons"]/span[@class="text-muted"]/text()')[0]
        df_temp.loc[0,'Date'] = datetime.strptime(c_date, '%d %b %Y').strftime('%Y-%m-%d')
        df_temp.loc[0,'Time'] = act_race.xpath('.//div[@class="race-selector"]/div[@class="race-selector__times tabs tabs--secondary"]/a[@class=" tabs__item tabs__item--active"]/text()')[0]
        c_crse = act_race.xpath('.//div[@class="race-selector__track-type"]/text()')
        df_temp.loc[0,'Course'] = c_crse[0].split('(')[0].strip()
        c_rslt = r_lnk[0].find('results') != -1

        if not c_rslt:
            # === description (dist, title, runners)
            c_desc = act_race.xpath('.//div[@class="race__title__description"]/div[@class="text-muted"]/text()')
            c_dist = ' '.join(re.findall(r'(\d+[MFY])\s', c_desc[0]))
            c_yard = calc_yards(c_dist)
            df_temp.loc[0,'Distance'] = c_dist
            df_temp.loc[0,'Yards'] = str(c_yard)
            df_temp.loc[0,'Runners'] = re.findall(r'(\d+)\srunners', c_desc[0])[0] # runners (12 runner)
            # === end Description ===
        else:
            c_dist = act_race.xpath('.//div/div[@class="race-subtitle"]/p/text()')
            print('C_DIST:', c_dist)
            pass

        c_r_hrse = act_race.xpath('.//div[@class="racecard__runner__column racecard__runner__name"]/a')

        for cnt_horse, act_horse in enumerate(c_r_hrse):
            if cnt_horse <8: continue # Test purpose: Only the 1st Horse parsed
            h_lnk = act_horse.xpath('@href')
            horse_link = urljoin(url_lnk, h_lnk[0])
            horse_name = act_horse.xpath('text()')
            df_temp.loc[0,'Horse'] = horse_name[0]

            tfrm_faves = act_race.xpath('/html[1]/body[1]/div[1]/div[1]/div[1]/div[2]/div[1]/div[5]/div[7]/div[2]/div[2]/div/div[@class="racecard__runner__header"]/div[@class="racecard__runner__column racecard__runner__name"]/text()')
            print (tfrm_faves,horse_name)

            if horse_name[0] in tfrm_faves: df_temp.loc[0,'Timeform'] = tfrm_faves.index(horse_name[0]) + 1

            horse_page = requests.get(horse_link)
            act_horse = html.fromstring(horse_page.text)

            act_horse_inf_tbl = act_horse.xpath('/html/body/div[1]/div/div/div[2]/div/div/div[1]/div[2]/div')
            df_temp.loc[0,'Form'] = act_horse.xpath('.//div[starts-with(span,"Form:")]/span/text()')[1]
            df_temp.loc[0,'Lastrun'] = act_horse.xpath('.//div[starts-with(span,"Last Ran:")]/span/text()')[1]
            df_temp.loc[0,'OR'] = act_horse.xpath('.//div[starts-with(span,"Official Rating:")]/span/text()')[1]
            df_temp.loc[0,'Sex'] = act_horse.xpath('.//div[starts-with(span,"Sex:")]/span/text()')[1]

            h_odds = act_horse.xpath('//div[@class="racecard__runner__column racecard__runner__column--price"]/live-odds/text()')
            if len(h_odds) == 0: 
                df_temp.loc[0,'Odds'] = 999
            else:
                d_odds = round(float(eval(h_odds[0])+1.0), 2)
                df_temp.loc[0,'Odds'] = d_odds

            print (df_temp)
            df_temp = df_temp[0:0]

            # df_race.append(df_temp)

        # print (df_race)
