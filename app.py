from datetime import datetime
from datetime import datetime
import time
import json
import requests as req
import pickle
from flask import Flask, jsonify, request, make_response, abort, render_template
import pandas as pd
import itertools
import math
import trueskill
def win_probability(team1, team2):
    delta_mu = sum(r.mu for r in team1) - sum(r.mu for r in team2)
    sum_sigma = sum(r.sigma ** 2 for r in itertools.chain(team1, team2))
    size = len(team1) + len(team2)
    denom = math.sqrt(size * (4.166666666666667 * 4.166666666666667) + sum_sigma)
    ts = trueskill.global_env()
    return ts.cdf(delta_mu / denom)


class OpenDotaAPI():
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.last_match_id = 0

    def _call(self, url, parameters, tries=10):
        for i in range(tries):
            try:
                if self.verbose: print("Sending API request... ", end="", flush=True)
                resp = req.get(url, params=parameters, timeout=20)
                load_resp = json.loads(resp.text)
                if self.verbose: print("done")
                return load_resp
            except Exception as e:
                print("failed. Trying again in 5s")
                print(e)
                time.sleep(5)
        else:
            ValueError("Unable to connect to OpenDota API")


    def get_pro_matches_custom_sql(self,limit = 100000):
        err = True
        url = "https://api.opendota.com/api/explorer?sql=select team_r.name radiant_team_name, team_d.name dire_team_name, team_r.tag radiant_team_tag, team_d.tag dire_team_tag, m.match_id, m.radiant_win, p.patch, m.start_time, m.leagueid, m.game_mode, m.radiant_team_id, m.dire_team_id, m.radiant_team_complete, m.dire_team_complete, m.radiant_captain, m.dire_captain, max(case when pm.rn = 1 then pm.account_id end) account_id_1, max(case when pm.rn = 2 then pm.account_id end) account_id_2, max(case when pm.rn = 3 then pm.account_id end) account_id_3, max(case when pm.rn = 4 then pm.account_id end) account_id_4, max(case when pm.rn = 5 then pm.account_id end) account_id_5, max(case when pm.rn = 6 then pm.account_id end) account_id_6, max(case when pm.rn = 7 then pm.account_id end) account_id_7, max(case when pm.rn = 8 then pm.account_id end) account_id_8, max(case when pm.rn = 9 then pm.account_id end) account_id_9, max(case when pm.rn = 10 then pm.account_id end) account_id_10 from matches m inner join( select pm.*, row_number() over(partition by match_id order by player_slot) rn from player_matches pm) pm on pm.match_id = m.match_id join match_patch p on m.match_id=p.match_id join teams team_r on m.radiant_team_id=team_r.team_id join teams team_d on m.dire_team_id=team_d.team_id group by m.match_id,p.patch,team_r.name,team_d.name,team_r.tag,team_d.tag order by m.match_id desc "
        #where m.start_time < 1577750400
        while err:
            resp = self._call(url, None,tries= 2)
            if resp['err'] is None:
                err = False
                continue
            print(resp['err'])
        matches = resp['rows']
        return pd.DataFrame(matches, index = [match['match_id'] for match in matches])


def solve(row):
    match = row
    if match['radiant_team_id'] not in team_wr:
        team_wr[match['radiant_team_id']] = {
            'team_id': int(match['radiant_team_id']),
            'win': 0,
            'losses': 0,
            'name': match['radiant_team_name'] if type(match['radiant_team_name']) != float else '_',
            'tag': match['radiant_team_tag'] if type(match['radiant_team_tag']) != float else '_',
            'last_match_time': int(match['start_time']),
            'rating': 1000,
            'TS_rating': trueskill.Rating(),
            'capitan': match['radiant_captain']
        }
    else:
        team_wr[match['radiant_team_id']]['last_match_time'] = int(match['start_time'])
        team_wr[match['radiant_team_id']]['tag'] = match['radiant_team_tag'] if type(
            match['radiant_team_tag']) != float else '_'
        team_wr[match['radiant_team_id']]['name'] = match['radiant_team_name'] if type(
            match['radiant_team_name']) != float else '_'
        team_wr[match['radiant_team_id']]['capitan'] = match['radiant_captain']

    if match['dire_team_id'] not in team_wr:
        team_wr[match['dire_team_id']] = {
            'team_id': int(match['dire_team_id']),
            'win': 0,
            'losses': 0,
            'name': match['dire_team_name'] if type(match['dire_team_name']) != float else '_',
            'tag': match['dire_team_tag'] if type(match['dire_team_tag']) != float else '_',
            'last_match_time': int(match['start_time']),
            'rating': 1000,
            'TS_rating': trueskill.Rating(),
            'capitan': match['dire_captain']
        }
    else:
        team_wr[match['dire_team_id']]['last_match_time'] = int(match['start_time'])
        team_wr[match['dire_team_id']]['tag'] = match['dire_team_tag'] if type(match['dire_team_tag']) != float else '_'
        team_wr[match['dire_team_id']]['name'] = match['dire_team_name'] if type(
            match['dire_team_name']) != float else '_'
        team_wr[match['dire_team_id']]['capitan'] = match['dire_captain']

    if match['radiant_captain'] not in capitan_wr:
        capitan_wr[match['radiant_captain']] = {
            'win': 0,
            'losses': 0
        }
    if match['dire_captain'] not in capitan_wr:
        capitan_wr[match['dire_captain']] = {
            'win': 0,
            'losses': 0
        }
    # ////////////////capitan
    radiant_player = 1
    dire_player = 1
    for i in range(1, 11):
        if match['account_id_{}'.format(i)] not in account_wr:
            account_wr[match['account_id_{}'.format(i)]] = {
                'win': 0,
                'losses': 0,
                'rating': env_players.Rating()
            }

        match['account_{}_wins'.format(i)] += account_wr[match['account_id_{}'.format(i)]]['win']
        match['account_{}_losses'.format(i)] += account_wr[match['account_id_{}'.format(i)]]['losses']

        if i < 6:
            account_wr[match['account_id_{}'.format(i)]]['win'] += match['radiant_win']
            account_wr[match['account_id_{}'.format(i)]]['losses'] += (1 - match['radiant_win'])
            team_wr[match['radiant_team_id']]['player_{}'.format(radiant_player)] = match['account_id_{}'.format(i)]
            radiant_player += 1
        else:
            account_wr[match['account_id_{}'.format(i)]]['win'] += (1 - match['radiant_win'])
            account_wr[match['account_id_{}'.format(i)]]['losses'] += match['radiant_win']
            team_wr[match['dire_team_id']]['player_{}'.format(dire_player)] = match['account_id_{}'.format(i)]
            dire_player += 1

    # ////////////////////player

    match['r_wins'] += team_wr[match['radiant_team_id']]['win']
    match['d_wins'] += team_wr[match['dire_team_id']]['win']

    match['r_losses'] += team_wr[match['radiant_team_id']]['losses']
    match['d_losses'] += team_wr[match['dire_team_id']]['losses']

    match['r_cap_wins'] += capitan_wr[match['radiant_captain']]['win']
    match['d_cap_wins'] += capitan_wr[match['dire_captain']]['win']

    match['r_cap_losses'] += capitan_wr[match['radiant_captain']]['losses']
    match['d_cap_losses'] += capitan_wr[match['dire_captain']]['losses']

    team_wr[match['radiant_team_id']]['win'] += match['radiant_win']
    team_wr[match['radiant_team_id']]['losses'] += (1 - match['radiant_win'])

    team_wr[match['dire_team_id']]['win'] += (1 - match['radiant_win'])
    team_wr[match['dire_team_id']]['losses'] += match['radiant_win']

    capitan_wr[match['radiant_captain']]['win'] += match['radiant_win']
    capitan_wr[match['radiant_captain']]['losses'] += (1 - match['radiant_win'])

    capitan_wr[match['dire_captain']]['win'] += (1 - match['radiant_win'])
    capitan_wr[match['dire_captain']]['losses'] += match['radiant_win']
    kFactor = 32
    match['r_rating'] = team_wr[match['radiant_team_id']]['rating']
    match['d_rating'] = team_wr[match['dire_team_id']]['rating']
    currRating1 = team_wr[match['radiant_team_id']]['rating']
    currRating2 = team_wr[match['dire_team_id']]['rating']
    r1 = 10 ** (currRating1 / 400)
    r2 = 10 ** (currRating2 / 400)
    e1 = r1 / (r1 + r2)
    e2 = r2 / (r1 + r2)
    win1 = int(match['radiant_win'])
    win2 = 1 - win1
    ratingDiff1 = kFactor * (win1 - e1)
    ratingDiff2 = kFactor * (win2 - e2)
    team_wr[match['radiant_team_id']]['rating'] += ratingDiff1
    team_wr[match['dire_team_id']]['rating'] += ratingDiff2

    r1 = team_wr[match['radiant_team_id']]['TS_rating']
    r2 = team_wr[match['dire_team_id']]['TS_rating']
    match['TSr_rating'] = r1.mu
    match['TSd_rating'] = r2.mu
    t1 = [r1]  # Team A contains just 1P
    t2 = [r2]  # Team B contains 2P and 3P
    match['teams_win_prob'] = win_probability(t1, t2)
    new_r1, new_r2 = trueskill.rate([t1, t2], ranks=[1 - match['radiant_win'], match['radiant_win']])
    new_r1, new_r2 = new_r1[0], new_r2[0]
    team_wr[match['radiant_team_id']]['TS_rating'] = new_r1
    team_wr[match['dire_team_id']]['TS_rating'] = new_r2
    TSrating[match['radiant_team_id']] = new_r1
    TSrating[match['dire_team_id']] = new_r2

    r1 = account_wr[match['account_id_{}'.format(1)]]['rating']
    r2 = account_wr[match['account_id_{}'.format(2)]]['rating']
    r3 = account_wr[match['account_id_{}'.format(3)]]['rating']
    r4 = account_wr[match['account_id_{}'.format(4)]]['rating']
    r5 = account_wr[match['account_id_{}'.format(5)]]['rating']
    r6 = account_wr[match['account_id_{}'.format(6)]]['rating']
    r7 = account_wr[match['account_id_{}'.format(7)]]['rating']
    r8 = account_wr[match['account_id_{}'.format(8)]]['rating']
    r9 = account_wr[match['account_id_{}'.format(9)]]['rating']
    r10 = account_wr[match['account_id_{}'.format(10)]]['rating']
    match['player_1_TS_rating'] = r1.mu
    match['player_2_TS_rating'] = r2.mu
    match['player_3_TS_rating'] = r3.mu
    match['player_4_TS_rating'] = r4.mu
    match['player_5_TS_rating'] = r5.mu
    match['player_6_TS_rating'] = r6.mu
    match['player_7_TS_rating'] = r7.mu
    match['player_8_TS_rating'] = r8.mu
    match['player_9_TS_rating'] = r9.mu
    match['player_10_TS_rating'] = r10.mu
    t1 = [r1, r2, r3, r4, r5]  # Team A contains just 1P
    t2 = [r6, r7, r8, r9, r10]  # Team B contains 2P and 3P
    match['players_win_prob'] = win_probability(t1, t2)
    new_r1, new_r2 = trueskill.rate([t1, t2], ranks=[1 - match['radiant_win'], match['radiant_win']])
    r1, r2, r3, r4, r5 = new_r1
    r6, r7, r8, r9, r10 = new_r2
    account_wr[match['account_id_{}'.format(1)]]['rating'] = r1
    account_wr[match['account_id_{}'.format(2)]]['rating'] = r2
    account_wr[match['account_id_{}'.format(3)]]['rating'] = r3
    account_wr[match['account_id_{}'.format(4)]]['rating'] = r4
    account_wr[match['account_id_{}'.format(5)]]['rating'] = r5
    account_wr[match['account_id_{}'.format(6)]]['rating'] = r6
    account_wr[match['account_id_{}'.format(7)]]['rating'] = r7
    account_wr[match['account_id_{}'.format(8)]]['rating'] = r8
    account_wr[match['account_id_{}'.format(9)]]['rating'] = r9
    account_wr[match['account_id_{}'.format(10)]]['rating'] = r10

    return match


def solve2(matches):
    X = pd.DataFrame(matches)
    X = X.iloc[::-1]
    X = X[X['game_mode'] != 1]
    X[['radiant_team_id', 'dire_team_id', 'radiant_captain', 'dire_captain']] = X[
        ['radiant_team_id', 'dire_team_id', 'radiant_captain', 'dire_captain']].fillna(0)
    X['radiant_team_id'] = X['radiant_team_id'].astype(int)
    X['dire_team_id'] = X['dire_team_id'].astype(int)
    X['radiant_captain'] = X['radiant_captain'].astype(int)
    X['dire_captain'] = X['dire_captain'].astype(int)
    X['r_wins'] = 0
    X['d_wins'] = 0
    X['r_losses'] = 0
    X['d_losses'] = 0
    X['r_cap_wins'] = 0
    X['d_cap_wins'] = 0
    X['r_cap_losses'] = 0
    X['d_cap_losses'] = 0
    X['r_rating'] = 0
    X['d_rating'] = 0
    for i in range(1, 11):
        X['account_{}_wins'.format(i)] = 0
        X['account_{}_losses'.format(i)] = 0
    X = X.apply(lambda row: solve(row), axis=1)

    X['r_team_winrate'] = X.apply(lambda row: winrate(row['r_wins'], row['r_losses']), axis=1)
    X['d_team_winrate'] = X.apply(lambda row: winrate(row['d_wins'], row['d_losses']), axis=1)

    X['r_capitan_winrate'] = X.apply(lambda row: winrate(row['r_cap_wins'], row['r_cap_losses']), axis=1)
    X['d_capitan_winrate'] = X.apply(lambda row: winrate(row['d_cap_wins'], row['d_cap_losses']), axis=1)
    for i in range(1, 11):
        X['account_id_{}_winrate'.format(i)] = X.apply(
            lambda row: winrate(row['account_{}_wins'.format(i)], row['account_{}_losses'.format(i)]), axis=1)
    X['winrate_team_ratio'] = X['r_team_winrate'] / X['d_team_winrate']
    X['winrate_capitan_ratio'] = X['r_capitan_winrate'] / X['d_capitan_winrate']
    X['sum_r_team_winrate'] = X[['account_id_{}_winrate'.format(i) for i in range(1, 6)]].sum(axis=1)
    X['sum_d_team_winrate'] = X[['account_id_{}_winrate'.format(i) for i in range(6, 11)]].sum(axis=1)
    X['sum_winrate_team_ratio'] = X['sum_r_team_winrate'] / X['sum_d_team_winrate']
    X['r_total_cap_games'] = X['r_cap_wins'] + X['r_cap_losses']
    X['d_total_cap_games'] = X['d_cap_wins'] + X['d_cap_losses']
    X['total_r_games'] = X[
        ['account_1_wins', 'account_1_losses', 'account_2_wins', 'account_2_losses', 'account_3_wins',
         'account_3_losses',
         'account_4_wins', 'account_4_losses', 'account_5_wins',
         'account_5_losses']].sum(axis=1)
    X['total_d_games'] = X[['account_6_wins', 'account_6_losses',
                            'account_7_wins', 'account_7_losses', 'account_8_wins',
                            'account_8_losses', 'account_9_wins', 'account_9_losses',
                            'account_10_wins', 'account_10_losses']].sum(axis=1)
    X['total_capitan_games_tario'] = X['r_total_cap_games'] / X['d_total_cap_games']
    X['total_players_games_tario'] = X['total_r_games'] / X['total_d_games']
    X['elo_rating_ratio'] = X['r_rating'] / X['d_rating']
    X['TS_rating_ratio'] = X['TSr_rating'] / X['TSd_rating']
    X['total_r_TS_rating'] = X[['player_1_TS_rating', 'player_2_TS_rating', 'player_3_TS_rating', 'player_4_TS_rating',
                                'player_5_TS_rating']].sum(axis=1)
    X['total_d_TS_rating'] = X[['player_6_TS_rating', 'player_7_TS_rating', 'player_8_TS_rating', 'player_9_TS_rating',
                                'player_10_TS_rating']].sum(axis=1)
    X['teams_players_rating_TS_ratio'] = X['total_r_TS_rating'] / X['total_d_TS_rating']
    return X



team_names = {
    'LGD.int': 7667517,
    'OG': 2586976,
    'BOOM ID': 7732977,
    'Typhoon EC': 7099096,
    'VG.P': 7422511,
    'Keen Gaming.L': 7554790
}
def get_id_by_name(name1):
    id1 = None
    if name1 in team_names:
        return team_names[name1]
    name1 = name1.replace("-", "")
    name1 = name1.replace(" ", "")
    name1 = name1.replace(".", "")
    name1 = name1.lower().strip()
    for word in ['team', 'gaming', '!']:
        if word in name1:
            name1 = name1.replace(word, "")
    team_info_new = team_info.sort_values(by='last_match_time', ascending=False)
    for row in team_info_new.iterrows():
        team_name = row[1]['name']
        team_name = team_name.replace("-", "")
        team_name = team_name.replace(".", "")
        team_name = team_name.replace(" ", "")
        team_name = team_name.lower().strip()
        for word in ['team', 'gaming', '!']:
            if word in team_name:
                team_name = team_name.replace(word, "")
        team_tag = row[1]['tag']
        team_tag = team_tag.replace("-", "")
        team_tag = team_tag.replace(".", "")
#         team_tag = team_tag.lower().strip()
#         if row[1]['team_id'] ==7667517:
#             print(name1)
#             print(team_name )
        if (name1 == team_name) or (name1 == team_tag):
            id1 = row[1]['team_id']
            break
        else:
            if (len(team_name) != 0) and (name1 == team_name.split()[0]):
                id1 = row[1]['team_id']
                break

    return id1
def winrate(win,loss):
    if loss+win == 0:
        return 0.47722
    else:
        return win/(loss+win)
def make_row(id1,id2):
    r_df = pd.DataFrame()
    d_df = pd.DataFrame()
    r_df[['account_id_1','account_id_2', 'account_id_3', 'account_id_4', 'account_id_5','radiant_captain']] = pd.DataFrame(team_info.loc[id1][[ 'player_1', 'player_2', 'player_3', 'player_4', 'player_5','capitan']]).T.reset_index(drop=True)

    d_df[['account_id_6', 'account_id_7', 'account_id_8', 'account_id_9','account_id_10','dire_captain']] = pd.DataFrame(team_info.loc[id2][[ 'player_1', 'player_2', 'player_3', 'player_4', 'player_5','capitan']]).T.reset_index(drop=True)
    res_df = pd.concat([r_df,d_df], axis = 1)
    res_df['radiant_team_id'] = id1
    res_df['dire_team_id'] = id2

    res_df['radiant_captain'] = res_df['radiant_captain'].astype(int)
    res_df['dire_captain'] = res_df['dire_captain'].astype(int)

    res_df['r_wins'] = team_wr[id1]['win']
    res_df['d_wins'] = team_wr[id2]['win']

    res_df['r_losses'] = team_wr[id1]['losses']
    res_df['d_losses'] = team_wr[id2]['losses']

    res_df['r_cap_wins'] = capitan_wr[res_df['radiant_captain'].values[0]]['win']
    res_df['d_cap_wins'] = capitan_wr[res_df['dire_captain'].values[0]]['win']

    res_df['r_cap_losses'] = capitan_wr[res_df['radiant_captain'].values[0]]['losses']
    res_df['d_cap_losses'] = capitan_wr[res_df['dire_captain'].values[0]]['losses']

    for i in range(1,11):
        res_df['account_{}_wins'.format(i)] = account_wr[res_df['account_id_{}'.format(i)].values[0]]['win']
        res_df['account_{}_losses'.format(i)] = account_wr[res_df['account_id_{}'.format(i)].values[0]]['losses']

        res_df['player_{}_TS_rating'.format(i)] = account_wr[res_df['account_id_{}'.format(i)].values[0]]['rating'].mu

    res_df['r_rating'] = team_wr[id1]['rating']
    res_df['d_rating'] = team_wr[id2]['rating']
    res_df['TSr_rating'] = TSrating[id1].mu
    res_df['TSd_rating'] = TSrating[id2].mu
    t1 = [TSrating[id1]]  # Team A contains just 1P
    t2 = [TSrating[id2]]  # Team B contains 2P and 3P
    res_df['teams_win_prob'] = win_probability(t1, t2)

    res_df['r_team_winrate'] = res_df.apply(lambda row:winrate(row['r_wins'],row['r_losses']), axis = 1)
    res_df['d_team_winrate'] = res_df.apply(lambda row:winrate(row['d_wins'],row['d_losses']), axis = 1)

    res_df['r_capitan_winrate'] = res_df.apply(lambda row:winrate(row['r_cap_wins'],row['r_cap_losses']), axis = 1)
    res_df['d_capitan_winrate'] = res_df.apply(lambda row:winrate(row['d_cap_wins'],row['d_cap_losses']), axis = 1)
    for i in range(1,11):
        res_df['account_id_{}_winrate'.format(i)] = res_df.apply(lambda row:winrate(row['account_{}_wins'.format(i)],row['account_{}_losses'.format(i)]), axis = 1)

    r1 = account_wr[res_df['account_id_{}'.format(1)].values[0]]['rating']
    r2 = account_wr[res_df['account_id_{}'.format(2)].values[0]]['rating']
    r3 = account_wr[res_df['account_id_{}'.format(3)].values[0]]['rating']
    r4 = account_wr[res_df['account_id_{}'.format(4)].values[0]]['rating']
    r5 = account_wr[res_df['account_id_{}'.format(5)].values[0]]['rating']
    r6 = account_wr[res_df['account_id_{}'.format(6)].values[0]]['rating']
    r7 = account_wr[res_df['account_id_{}'.format(7)].values[0]]['rating']
    r8 = account_wr[res_df['account_id_{}'.format(8)].values[0]]['rating']
    r9 = account_wr[res_df['account_id_{}'.format(9)].values[0]]['rating']
    r10 = account_wr[res_df['account_id_{}'.format(10)].values[0]]['rating']

    t1 = [r1,r2,r3,r4,r5]  # Team A contains just 1P
    t2 = [r6,r7,r8,r9,r10]  # Team B contains 2P and 3P
    res_df['players_win_prob'] = win_probability(t1, t2)
    res_df['winrate_team_ratio'] = res_df['r_team_winrate']/res_df['d_team_winrate']
    res_df['winrate_capitan_ratio'] = res_df['r_capitan_winrate']/res_df['d_capitan_winrate']
    res_df['sum_r_team_winrate'] = res_df[['account_id_{}_winrate'.format(i)for i in range(1,6)]].sum(axis =1)
    res_df['sum_d_team_winrate'] = res_df[['account_id_{}_winrate'.format(i)for i in range(6,11)]].sum(axis =1)
    res_df['sum_winrate_team_ratio'] = res_df['sum_r_team_winrate']/res_df['sum_d_team_winrate']
    res_df['r_total_cap_games'] = res_df['r_cap_wins'] +res_df['r_cap_losses']
    res_df['d_total_cap_games'] = res_df['d_cap_wins'] +res_df['d_cap_losses']
    res_df['total_r_games'] = res_df[['account_1_wins', 'account_1_losses', 'account_2_wins','account_2_losses', 'account_3_wins', 'account_3_losses',
           'account_4_wins', 'account_4_losses', 'account_5_wins',
           'account_5_losses']].sum(axis =1)
    res_df['total_d_games'] = res_df[['account_6_wins', 'account_6_losses',
           'account_7_wins', 'account_7_losses', 'account_8_wins',
           'account_8_losses', 'account_9_wins', 'account_9_losses',
           'account_10_wins', 'account_10_losses']].sum(axis =1)
    res_df['total_capitan_games_tario']=res_df['r_total_cap_games'] /res_df['d_total_cap_games']
    res_df['total_players_games_tario']=res_df['total_r_games'] /res_df['total_d_games']
    res_df['elo_rating_ratio'] = res_df['r_rating'] / res_df['d_rating']
    res_df['TS_rating_ratio'] = res_df['TSr_rating'] / res_df['TSd_rating']
    res_df['total_r_TS_rating'] = res_df[['player_1_TS_rating', 'player_2_TS_rating', 'player_3_TS_rating', 'player_4_TS_rating', 'player_5_TS_rating']].sum(axis=1)
    res_df['total_d_TS_rating'] = res_df[['player_6_TS_rating', 'player_7_TS_rating', 'player_8_TS_rating', 'player_9_TS_rating', 'player_10_TS_rating']].sum(axis=1)
    res_df['teams_players_rating_TS_ratio'] = res_df['total_r_TS_rating'] / res_df['total_d_TS_rating']

    res = res_df[['teams_win_prob', 'players_win_prob', 'winrate_team_ratio',
       'winrate_capitan_ratio', 'sum_r_team_winrate', 'sum_d_team_winrate',
       'sum_winrate_team_ratio', 'total_r_games', 'total_d_games',
       'total_capitan_games_tario', 'total_players_games_tario',
       'TS_rating_ratio', 'teams_players_rating_TS_ratio']]
    return res

def rating_c(row):
    row['rating'] = elo_teams[row['team_id']]
    return row
app = Flask(__name__)
api = OpenDotaAPI(verbose=True)
env = trueskill.TrueSkill(mu = 1000, sigma = 100,draw_probability=0)
env.make_as_global()
env_players = trueskill.TrueSkill(draw_probability=0)
pro_matches = pd.read_csv('pro_matches.csv', index_col=0)
# pro_matches = api.get_pro_matches_custom_sql()
# pro_matches.to_csv('pro_matches.csv') #update pro_matches
#
# print('Start computing ...')
# team_wr = {}
# capitan_wr = {}
# account_wr = {}
# elo_teams = {}
# TSrating = {}
# X = solve2(pro_matches)
# with open('team_wr.pickle', 'wb') as f:
#     pickle.dump(team_wr,f)
# with open('capitan_wr.pickle', 'wb') as f1:
#     pickle.dump(capitan_wr,f1)
# with open('account_wr.pickle', 'wb') as f2:
#     pickle.dump(account_wr,f2)
# with open('elo_teams.pickle', 'wb') as f3:
#     pickle.dump(elo_teams, f3)
# with open('TSrating.pickle', 'wb') as f3:
#         pickle.dump(TSrating, f3)
# team_info = pd.DataFrame(team_wr).T
# team_info[['team_id', 'last_match_time']] = team_info[['team_id', 'last_match_time']].astype(int)
# team_info = team_info.fillna('_')
# team_info.to_csv('team_info.csv')
# team_info = team_info.drop(index = 5026801).sort_values(by=['rating'], ascending = False)
# print('Finish computing')
# #




model = pickle.load(open('model.pickle', 'rb'))

pro_matches = pd.read_csv('pro_matches.csv', index_col=0)
team_info = pd.read_csv('team_info.csv', index_col=0)
team_info = team_info.fillna('_')

team_wr = pickle.load(open('team_wr.pickle', 'rb'))
capitan_wr = pickle.load(open('capitan_wr.pickle', 'rb'))
account_wr = pickle.load(open('account_wr.pickle', 'rb'))
elo_teams = pickle.load(open('elo_teams.pickle', 'rb'))
TSrating = pickle.load(open('TSrating.pickle', 'rb'))


team_info.to_csv('team_info.csv')

print(pro_matches[:1]['match_id'])

#print(data.players_wr.shape, data.team_info.shape)
#print(data.players_wr.loc[19672354])


@app.route('/ppp')
def home():
    return render_template('index.html')
@app.route('/predict', methods=['GET'])
def get_tasks():
    id1 = request.args.get('id1', None)
    id2 = request.args.get('id2', None)
    if id1 is None:
        abort(400, description="id1 is None")
    if id2 is None:
        abort(400, description="id2 is None")
    x1 = make_row(int(id1), int(id2))
    result = model.predict_proba(x1)
    x2 = make_row(int(id2), int(id1))
    result2 = model.predict_proba(x2)
    return jsonify({'Team1': (result[0][1] + result2[0][0]) / 2, 'Team2': (result[0][0] + result2[0][1]) / 2})


@app.route('/predictbyname', methods=['GET'])
def get_tasks2():
    name1 = request.args.get('name1', None)
    name2 = request.args.get('name2', None)
    if name1 is None:
        abort(400, description="id1 is None")
    if name2 is None:
        abort(400, description="id2 is None")
    print(name1,name2)
    id1 = get_id_by_name(name1)
    if id1 is None:
        abort(400, description="Name 1 not found")
    id2 = get_id_by_name(name2)
    if id2 is None:
        abort(400, description="Name 2 not found")
    print(id1, id2)
    x1 = make_row(int(id1), int(id2))
    result = model.predict_proba(x1)

    x2 = make_row(int(id2), int(id1))

    result2 = model.predict_proba(x2)

    resp = {'Team_1': (result[0][1] + result2[0][0]) / 2,
            'Team_2': (result[0][0] + result2[0][1]) / 2,
            'Name_1': team_info.loc[id1]['name'],
            'Name_2': team_info.loc[id2]['name'],
            'id1' : id1,
            'id2' : id2
            }
    return jsonify(resp)

@app.route('/predict',methods=['POST'])
def predict():
    '''
    For rendering results on HTML GUI
    '''
    # int_features = [int(x) for x in request.form.values()]

    name1 = request.form['Name1']
    name2 = request.form['Name2']
    if name1 is None:
        abort(400, description="id1 is None")
    if name2 is None:
        abort(400, description="id2 is None")
    print(name1, name2)
    id1 = get_id_by_name(name1)
    if id1 is None:
        return render_template('index.html', prediction_text='{} fix name pls'.format(id1))
    id2 = get_id_by_name(name2)
    if id2 is None:
        return render_template('index.html', prediction_text='{} fix name pls'.format(id2))
    print(id1, id2)

    x1 = make_row(int(id1), int(id2))
    result = model.predict_proba(x1)
    x2 = make_row(int(id2), int(id1))

    result2 = model.predict_proba(x2)
    resp = {'Team_1': (result[0][1] + result2[0][0]) / 2,
            'Team_2': (result[0][0] + result2[0][1]) / 2,
            'Name_1': team_info.loc[id1]['name'],
            'Name_2': team_info.loc[id2]['name'],
            'id1': id1,
            'id2': id2
            }
    return render_template('index.html', prediction_text='{}'.format(resp))

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.errorhandler(400)
def not_found2(error):
    return make_response(jsonify({'error': error.description}), 400)


if __name__ == '__main__':
    app.run(debug=True)
