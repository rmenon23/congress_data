#import all needed libraries
import requests
import pandas as pd
import numpy as np
import os
from tqdm import tqdm

# enter key
key = {'X-API-Key' : os.getenv('PROPUBLICA_KEY')}

# gather congressmen demographic data
r_senate = requests.get('https://api.propublica.org/congress/v1/115/senate/members.json', headers = key)
r_house = requests.get('https://api.propublica.org/congress/v1/115/house/members.json', headers = key)

temp_senate = r_senate.json()
temp_house = r_house.json()

#gather all members
senate_json = temp_senate['results'][0]['members']
house_json = temp_house['results'][0]['members']

# create dataframe for each chamber and keep desired columns
senate_df = pd.DataFrame(senate_json)
house_df = pd.DataFrame(house_json)
needed_headers = ["id","first_name","last_name","party","state","phone","votes_with_party_pct"]

# create a clean dataframe with a markers for which chamber of Congress they are a member of
house_df_clean = house_df[needed_headers]
house_df_clean["chamber"] = "H"

senate_df_clean = senate_df[needed_headers]
senate_df_clean["chamber"] = "S"

# append the two dataframes to create one clean data frame
congress_members = house_df_clean.append(senate_df_clean)
congress_members.head()

# get summary voting records to each bill in the house
r_house_votes_1 = requests.get('https://api.propublica.org/congress/v1/house/votes/2017/01.json', headers = key).json()
r_house_votes_2 = requests.get('https://api.propublica.org/congress/v1/house/votes/2017/02.json', headers = key).json()
r_house_votes_3 = requests.get('https://api.propublica.org/congress/v1/house/votes/2017/03.json', headers = key).json()
r_house_votes_4 = requests.get('https://api.propublica.org/congress/v1/house/votes/2017/04.json', headers = key).json()


# create one large dataframe for all of the House votes
# check the number of House bills
roll_calls_jan = len(r_house_votes_1['results']['votes'])
roll_calls_feb = len(r_house_votes_2['results']['votes'])
roll_calls_mar = len(r_house_votes_3['results']['votes'])
roll_calls_apr = len(r_house_votes_4['results']['votes'])
roll_calls_total = roll_calls_jan + roll_calls_feb + roll_calls_mar + roll_calls_apr

all_house_votes = pd.DataFrame()
for rc in tqdm(range(1, roll_calls_total)):
    try:
        rc_votes_temp_house = requests.get("https://api.propublica.org/congress/v1/115/house/sessions/1/votes/" + str(rc) + ".json", headers = key).json()
        temp_df = pd.DataFrame(rc_votes_temp_house['results']['votes']['vote']['positions'])
        all_house_votes = all_house_votes.append(temp_df)
        all_house_votes['bill_id'] = rc_votes_temp_house['results']['votes']['vote']['bill']['bill_id']
    except KeyError as error:
        print error

# get summary voting records to each bill in the house
r_senate_votes_1 = requests.get('https://api.propublica.org/congress/v1/senate/votes/2017/01.json', headers = key).json()
r_senate_votes_2 = requests.get('https://api.propublica.org/congress/v1/senate/votes/2017/02.json', headers = key).json()
r_senate_votes_3 = requests.get('https://api.propublica.org/congress/v1/senate/votes/2017/03.json', headers = key).json()
r_senate_votes_4 = requests.get('https://api.propublica.org/congress/v1/senate/votes/2017/04.json', headers = key).json()

# create one large dataframe for all of the Senate votes
senate_roll_calls_jan = len(r_senate_votes_1['results']['votes'])
senate_roll_calls_feb = len(r_senate_votes_2['results']['votes'])
senate_roll_calls_mar = len(r_senate_votes_3['results']['votes'])
senate_roll_calls_apr = len(r_senate_votes_4['results']['votes'])
senate_roll_calls_total = senate_roll_calls_jan + senate_roll_calls_feb + senate_roll_calls_mar + senate_roll_calls_apr

all_senate_votes = pd.DataFrame()
for rc in tqdm(range(1,senate_roll_calls_total)):
    print rc
    try:
        rc_votes_temp_senate = requests.get("https://api.propublica.org/congress/v1/115/senate/sessions/1/votes/" + str(rc) + ".json", headers = key).json()
        temp_df = pd.DataFrame(rc_votes_temp_senate['results']['votes']['vote']['positions'])
        all_senate_votes = all_senate_votes.append(temp_df)
        all_senate_votes['bill_id'] = rc_votes_temp_senate['results']['votes']['vote']['bill']['bill_id']
    except KeyError as error:
        print error


# merge in membes with votes
all_votes = pd.concat([all_house_votes,all_senate_votes])
all_votes['counter'] = 1

# count the votes for each congressmeen by ID and the type of vote
count_by_congressman = all_votes.groupby(['member_id','vote_position']).count()
count_by_congressman_df = pd.DataFrame(count_by_congressman['counter'])
# reset the index to fix some issues with unwanted vote position
count_by_congressman_df = count_by_congressman_df.reset_index(level = ['member_id','vote_position'])
count_by_congressman_df = count_by_congressman_df[count_by_congressman_df['vote_position'] != "Present"]

# merge in the members DataFrame with the votes
full_df = congress_members.merge(count_by_congressman_df, how = "inner", left_on = "id", right_on = "member_id")

# fix encoding issues with first and last names
full_df['first_name'] = full_df['first_name'].str.encode('utf-8', errors='strict')
full_df['last_name'] = full_df['last_name'].str.encode('utf-8', errors='strict')

# drop the member id because id already exits
full_df = full_df.drop(['member_id'], axis = 1)

# export file to the lib folder in the app
full_df.to_json('/Users/rmenon/Projects/congress_app/lib/data/congress_vote_distribution.json')
