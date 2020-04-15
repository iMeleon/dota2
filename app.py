from datetime import datetime
from datetime import datetime
import time
import json
import requests as req
import numpy as np
import pandas as pd
import pickle
from flask import Flask, jsonify, request, make_response, abort, render_template
import pandas as pd


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

    def get_teams_rating_db(self):
        url = "https://api.opendota.com/api/explorer?sql=select%20R.team_id,%20name,%20rating,%20wins,%20losses,%20last_match_time,%20tag%20from%20teams%20T%20join%20team_rating%20R%20on%20T.team_id=R.team_id"
        teams_rating = sorted(self._call(url, None, tries=2)['rows'], key=lambda team: team['rating'], reverse=True)
        return pd.DataFrame(teams_rating, index=[team['team_id'] for team in teams_rating])
    def get_pro_matches_custom_sql(self,limit = 100000):
        err = True
        url = "https://api.opendota.com/api/explorer?sql=select%20m.match_id,%20m.radiant_win,%20p.patch,%20m.start_time,%20m.leagueid,%20m.game_mode,%20m.radiant_team_id,%20m.dire_team_id,%20m.radiant_team_complete,%20m.dire_team_complete,%20m.radiant_captain,%20m.dire_captain,%20max(case%20when%20pm.rn%20=%201%20then%20pm.account_id%20end)%20account_id_1,%20max(case%20when%20pm.rn%20=%202%20then%20pm.account_id%20end)%20account_id_2,%20max(case%20when%20pm.rn%20=%203%20then%20pm.account_id%20end)%20account_id_3,%20max(case%20when%20pm.rn%20=%204%20then%20pm.account_id%20end)%20account_id_4,%20max(case%20when%20pm.rn%20=%205%20then%20pm.account_id%20end)%20account_id_5,%20max(case%20when%20pm.rn%20=%206%20then%20pm.account_id%20end)%20account_id_6,%20max(case%20when%20pm.rn%20=%207%20then%20pm.account_id%20end)%20account_id_7,%20max(case%20when%20pm.rn%20=%208%20then%20pm.account_id%20end)%20account_id_8,%20max(case%20when%20pm.rn%20=%209%20then%20pm.account_id%20end)%20account_id_9,%20max(case%20when%20pm.rn%20=%2010%20then%20pm.account_id%20end)%20account_id_10%20from%20matches%20m%20inner%20join(%20select%20pm.*,%20row_number()%20over(partition%20by%20match_id%20order%20by%20player_slot)%20rn%20from%20player_matches%20pm)%20pm%20on%20pm.match_id%20=%20m.match_id%20join%20match_patch%20p%20on%20m.match_id=p.match_id%20%20group%20by%20m.match_id,p.patch%20order%20by%20m.match_id%20desc%20limit%20{}%20".format(limit)#where m.start_time < 1577750400
        while err:
            resp = self._call(url, None,tries= 2)
            if resp['err'] is None:
                err = False
                continue
            print(resp['err'])
        matches = resp['rows']
        return pd.DataFrame(matches, index = [match['match_id'] for match in matches])
    def get_teem_players(self, team_id):
        url = "https://api.opendota.com/api/teams/{}/players".format(team_id)
        return self._call(url, None, tries=2)

    def get_teams(self):
        url = "https://api.opendota.com/api/teams"
        return self._call(url, None, tries=2)

    # Return a dictionary with match information
    # Return a list of 100 recent matches; save smaller match_id
    def get_recent_matches(self, use_last_match=False):
        params = dict()
        if use_last_match:
            params['less_than_match_id'] = self.last_match_id
        url = "https://api.opendota.com/api/publicMatches"
        matches = self._call(url, params)
        self.last_match_id = min([item['match_id'] for item in matches])
        return matches
        # Return a list of 100 recent matches; save smaller match_id

    def get_recent_pro_matches(self, use_last_match=False):
        params = dict()
        if use_last_match:
            params['less_than_match_id'] = use_last_match
        url = "https://api.opendota.com/api/proMatches"
        matches = self._call(url, params)
        self.last_match_id = min([item['match_id'] for item in matches])
        return matches

    # Return a dictionary with match information

    def get_recent_pro_matches(self, use_last_match=False):
        params = dict()
        if use_last_match:
            params['less_than_match_id'] = use_last_match
        url = "https://api.opendota.com/api/proMatches"
        matches = self._call(url, params)
        self.last_match_id = min([item['match_id'] for item in matches])
        return matches

    def get_player_wr(self, player_id):
        params = dict()
        params['game_mode'] = 2
        url = "https://api.opendota.com/api/players/{}/wl".format(player_id)
        matches = self._call(url, params)
        return matches

    def get_match_info(self, match_id):
        url = "https://api.opendota.com/api/matches/" + str(match_id)
        return self._call(url, None)

    def get_team_info(self, match_id, ):
        url = "https://api.opendota.com/api/teams/" + str(match_id)
        return self._call(url, None, tries=1)


def solve(row):
    match = row
    if match['radiant_team_id'] not in team_wr:
        team_wr[match['radiant_team_id']] = {
            'win': 0,
            'losses': 0
        }
    if match['dire_team_id'] not in team_wr:
        team_wr[match['dire_team_id']] = {
            'win': 0,
            'losses': 0
        }
    # ///////////team
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
    for i in range(1, 11):
        if match['account_id_{}'.format(i)] not in account_wr:
            account_wr[match['account_id_{}'.format(i)]] = {
                'win': 0,
                'losses': 0
            }

        match['account_{}_wins'.format(i)] += account_wr[match['account_id_{}'.format(i)]]['win']
        match['account_{}_losses'.format(i)] += account_wr[match['account_id_{}'.format(i)]]['losses']

        if i < 6:
            account_wr[match['account_id_{}'.format(i)]]['win'] += match['radiant_win']
            account_wr[match['account_id_{}'.format(i)]]['losses'] += (1 - match['radiant_win'])
        else:
            account_wr[match['account_id_{}'.format(i)]]['win'] += (1 - match['radiant_win'])
            account_wr[match['account_id_{}'.format(i)]]['losses'] += match['radiant_win']

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
    if match['radiant_team_id'] not in elo_teams:
        elo_teams[match['radiant_team_id']] = 1000
    if match['dire_team_id'] not in elo_teams:
        elo_teams[match['dire_team_id']] = 1000
    match['r_rating'] = elo_teams[match['radiant_team_id']]
    match['d_rating'] = elo_teams[match['dire_team_id']]
    currRating1 = elo_teams[match['radiant_team_id']]
    currRating2 = elo_teams[match['dire_team_id']]
    r1 = 10 ** (currRating1 / 400)
    r2 = 10 ** (currRating2 / 400)
    e1 = r1 / (r1 + r2)
    e2 = r2 / (r1 + r2)
    win1 = int(match['radiant_win'])
    win2 = 1 - win1
    ratingDiff1 = kFactor * (win1 - e1)
    ratingDiff2 = kFactor * (win2 - e2)
    elo_teams[match['radiant_team_id']] += ratingDiff1
    elo_teams[match['dire_team_id']] += ratingDiff2
    return match


def solve2(matches):
    X = pd.DataFrame(matches)
    X = X.iloc[::-1]
    X = X[X['game_mode'] !=1]
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
    return X




def predict(id1, id2):
    r_df = pd.DataFrame()
    d_df = pd.DataFrame()
    r_df[['account_id_1', 'account_id_2', 'account_id_3', 'account_id_4', 'account_id_5',
          'radiant_captain']] = pd.DataFrame(find_team_cap(id1)).T.reset_index(drop=True)
    d_df[['account_id_6', 'account_id_7', 'account_id_8', 'account_id_9', 'account_id_10',
          'dire_captain']] = pd.DataFrame(find_team_cap(id2)).T.reset_index(drop=True)
    res_df = pd.concat([r_df, d_df], axis=1)
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

    for i in range(1, 11):
        res_df['account_{}_wins'.format(i)] = account_wr[res_df['account_id_{}'.format(i)].values[0]]['win']
        res_df['account_{}_losses'.format(i)] = account_wr[res_df['account_id_{}'.format(i)].values[0]]['losses']

    res_df['r_rating'] = elo_teams[id1]
    res_df['d_rating'] = elo_teams[id2]

    res_df['r_team_winrate'] = res_df.apply(lambda row: winrate(row['r_wins'], row['r_losses']), axis=1)
    res_df['d_team_winrate'] = res_df.apply(lambda row: winrate(row['d_wins'], row['d_losses']), axis=1)

    res_df['r_capitan_winrate'] = res_df.apply(lambda row: winrate(row['r_cap_wins'], row['r_cap_losses']), axis=1)
    res_df['d_capitan_winrate'] = res_df.apply(lambda row: winrate(row['d_cap_wins'], row['d_cap_losses']), axis=1)
    for i in range(1, 11):
        res_df['account_id_{}_winrate'.format(i)] = res_df.apply(
            lambda row: winrate(row['account_{}_wins'.format(i)], row['account_{}_losses'.format(i)]), axis=1)

    res_df['winrate_team_ratio'] = res_df['r_team_winrate'] / res_df['d_team_winrate']
    res_df['winrate_capitan_ratio'] = res_df['r_capitan_winrate'] / res_df['d_capitan_winrate']
    res_df['sum_r_team_winrate'] = res_df[['account_id_{}_winrate'.format(i) for i in range(1, 6)]].sum(axis=1)
    res_df['sum_d_team_winrate'] = res_df[['account_id_{}_winrate'.format(i) for i in range(6, 11)]].sum(axis=1)
    res_df['sum_winrate_team_ratio'] = res_df['sum_r_team_winrate'] / res_df['sum_d_team_winrate']
    res_df['r_total_cap_games'] = res_df['r_cap_wins'] + res_df['r_cap_losses']
    res_df['d_total_cap_games'] = res_df['d_cap_wins'] + res_df['d_cap_losses']
    res_df['total_r_games'] = res_df[
        ['account_1_wins', 'account_1_losses', 'account_2_wins', 'account_2_losses', 'account_3_wins',
         'account_3_losses',
         'account_4_wins', 'account_4_losses', 'account_5_wins',
         'account_5_losses']].sum(axis=1)
    res_df['total_d_games'] = res_df[['account_6_wins', 'account_6_losses',
                                      'account_7_wins', 'account_7_losses', 'account_8_wins',
                                      'account_8_losses', 'account_9_wins', 'account_9_losses',
                                      'account_10_wins', 'account_10_losses']].sum(axis=1)
    res_df['total_capitan_games_tario'] = res_df['r_total_cap_games'] / res_df['d_total_cap_games']
    res_df['total_players_games_tario'] = res_df['total_r_games'] / res_df['total_d_games']
    res_df['elo_rating_ratio'] = res_df['r_rating'] / res_df['d_rating']
    # res_df = res_df.drop([ 'account_1_wins',
    #        'account_1_losses', 'account_2_wins', 'account_2_losses',
    #        'account_3_wins', 'account_3_losses', 'account_4_wins',
    #        'account_4_losses', 'account_5_wins', 'account_5_losses',
    #        'account_6_wins', 'account_6_losses', 'account_7_wins',
    #        'account_7_losses', 'account_8_wins', 'account_8_losses',
    #        'account_9_wins', 'account_9_losses', 'account_10_wins',
    #        'account_10_losses','account_id_1_winrate', 'account_id_2_winrate',
    #        'account_id_3_winrate', 'account_id_4_winrate', 'account_id_5_winrate',
    #        'account_id_6_winrate', 'account_id_7_winrate', 'account_id_8_winrate',
    #  'account_id_9_winrate', 'account_id_10_winrate','r_cap_wins', 'd_cap_wins', 'r_cap_losses', 'd_cap_losses'],axis = 1)
    res = res_df[['r_wins', 'd_wins', 'r_losses', 'd_losses', 'r_cap_wins', 'd_cap_wins',
                  'r_cap_losses', 'd_cap_losses', 'r_rating', 'd_rating',
                  'account_1_wins', 'account_1_losses', 'account_2_wins',
                  'account_2_losses', 'account_3_wins', 'account_3_losses',
                  'account_4_wins', 'account_4_losses', 'account_5_wins',
                  'account_5_losses', 'account_6_wins', 'account_6_losses',
                  'account_7_wins', 'account_7_losses', 'account_8_wins',
                  'account_8_losses', 'account_9_wins', 'account_9_losses',
                  'account_10_wins', 'account_10_losses', 'r_team_winrate',
                  'd_team_winrate', 'r_capitan_winrate', 'd_capitan_winrate',
                  'account_id_1_winrate', 'account_id_2_winrate', 'account_id_3_winrate',
                  'account_id_4_winrate', 'account_id_5_winrate', 'account_id_6_winrate',
                  'account_id_7_winrate', 'account_id_8_winrate', 'account_id_9_winrate',
                  'account_id_10_winrate', 'winrate_team_ratio', 'winrate_capitan_ratio',
                  'sum_r_team_winrate', 'sum_d_team_winrate', 'sum_winrate_team_ratio',
                  'r_total_cap_games', 'd_total_cap_games', 'total_r_games',
                  'total_d_games', 'total_capitan_games_tario',
                  'total_players_games_tario', 'elo_rating_ratio']]

    return res


def get_id_by_name(name1, name2):
    id1 = None
    id2 = None
    name1 = name1.replace("-", "")
    name2 = name2.replace("-", "")
    name1 = name1.replace(".", "")
    name2 = name2.replace(".", "")
    name1 = name1.lower().strip()
    name2 = name2.lower().strip()
    team_info_new = team_info.sort_values(by='last_match_time', ascending=False)
    for row in team_info_new.iterrows():
        team_name = row[1]['name']
        team_name = team_name.replace("-", "")
        team_name = team_name.replace(".", "")
        team_name = team_name.lower().strip()
        team_tag = row[1]['tag']
        team_tag = team_tag.replace("-", "")
        team_tag = team_tag.replace(".", "")
        team_tag = team_tag.lower().strip()
        if ((name1 == team_name) or (name1 == team_tag)):
            id1 = row[1]['team_id']
            break
        else:
            name1_list = name1.split()
            name_from_teams_list = team_name.split()
            for word in ['team', 'gaming', '!']:
                if word in name1_list: name1_list.remove(word)
                if word in name_from_teams_list: name_from_teams_list.remove(word)
            if name1_list[0] in name_from_teams_list:
                id1 = row[1]['team_id']
                break

    for row in team_info_new.iterrows():
        team_name = row[1]['name']
        team_name = team_name.replace("-", "")
        team_name = team_name.replace(".", "")
        team_name = team_name.lower().strip()
        team_tag = row[1]['tag']
        team_tag = team_tag.replace("-", "")
        team_tag = team_tag.replace(".", "")
        team_tag = team_tag.lower().strip()
        if ((name2 == team_name) or (name2 == team_tag)):
            id2 = row[1]['team_id']
            break
        else:
            name2_list = name2.split()
            name_from_teams_list = team_name.split()
            for word in ['team', 'gaming', '!']:
                if word in name2_list: name2_list.remove(word)
                if word in name_from_teams_list: name_from_teams_list.remove(word)
            if name2_list[0] in name_from_teams_list:
                id2 = row[1]['team_id']
                break
    return id1, id2
def winrate(win,loss):
    if loss+win == 0:
        return 0.47722
    else:
        return win/(loss+win)
def make_row(id1,id2):
    r_df = pd.DataFrame()
    d_df = pd.DataFrame()
    print('228')
    r_df[['account_id_1','account_id_2', 'account_id_3', 'account_id_4', 'account_id_5','radiant_captain']] = pd.DataFrame(find_team_cap(id1)).T.reset_index(drop=True)

    d_df[['account_id_6', 'account_id_7', 'account_id_8', 'account_id_9','account_id_10','dire_captain']] = pd.DataFrame(find_team_cap(id2)).T.reset_index(drop=True)
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

    res_df['r_rating'] = elo_teams[id1]
    res_df['d_rating'] = elo_teams[id2]

    res_df['r_team_winrate'] = res_df.apply(lambda row:winrate(row['r_wins'],row['r_losses']), axis = 1)
    res_df['d_team_winrate'] = res_df.apply(lambda row:winrate(row['d_wins'],row['d_losses']), axis = 1)

    res_df['r_capitan_winrate'] = res_df.apply(lambda row:winrate(row['r_cap_wins'],row['r_cap_losses']), axis = 1)
    res_df['d_capitan_winrate'] = res_df.apply(lambda row:winrate(row['d_cap_wins'],row['d_cap_losses']), axis = 1)
    for i in range(1,11):
        res_df['account_id_{}_winrate'.format(i)] = res_df.apply(lambda row:winrate(row['account_{}_wins'.format(i)],row['account_{}_losses'.format(i)]), axis = 1)

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
    # res_df = res_df.drop([ 'account_1_wins',
    #        'account_1_losses', 'account_2_wins', 'account_2_losses',
    #        'account_3_wins', 'account_3_losses', 'account_4_wins',
    #        'account_4_losses', 'account_5_wins', 'account_5_losses',
    #        'account_6_wins', 'account_6_losses', 'account_7_wins',
    #        'account_7_losses', 'account_8_wins', 'account_8_losses',
    #        'account_9_wins', 'account_9_losses', 'account_10_wins',
    #        'account_10_losses','account_id_1_winrate', 'account_id_2_winrate',
    #        'account_id_3_winrate', 'account_id_4_winrate', 'account_id_5_winrate',
    #        'account_id_6_winrate', 'account_id_7_winrate', 'account_id_8_winrate',
    #  'account_id_9_winrate', 'account_id_10_winrate','r_cap_wins', 'd_cap_wins', 'r_cap_losses', 'd_cap_losses'],axis = 1)
    res = res_df[['r_wins', 'd_wins', 'r_losses', 'd_losses', 'r_cap_wins', 'd_cap_wins',
                  'r_cap_losses', 'd_cap_losses', 'r_rating', 'd_rating',
                  'account_1_wins', 'account_1_losses', 'account_2_wins',
                  'account_2_losses', 'account_3_wins', 'account_3_losses',
                  'account_4_wins', 'account_4_losses', 'account_5_wins',
                  'account_5_losses', 'account_6_wins', 'account_6_losses',
                  'account_7_wins', 'account_7_losses', 'account_8_wins',
                  'account_8_losses', 'account_9_wins', 'account_9_losses',
                  'account_10_wins', 'account_10_losses', 'r_team_winrate',
                  'd_team_winrate', 'r_capitan_winrate', 'd_capitan_winrate',
                  'account_id_1_winrate', 'account_id_2_winrate', 'account_id_3_winrate',
                  'account_id_4_winrate', 'account_id_5_winrate', 'account_id_6_winrate',
                  'account_id_7_winrate', 'account_id_8_winrate', 'account_id_9_winrate',
                  'account_id_10_winrate', 'winrate_team_ratio', 'winrate_capitan_ratio',
                  'sum_r_team_winrate', 'sum_d_team_winrate', 'sum_winrate_team_ratio',
                  'r_total_cap_games', 'd_total_cap_games', 'total_r_games',
                  'total_d_games', 'total_capitan_games_tario',
                  'total_players_games_tario', 'elo_rating_ratio']]
    print('END')
    return res
def find_team_cap(id_team):
    for row in pro_matches.iterrows():
        match = row[1]
        if match['game_mode'] == 1:
            continue
        if id_team == match['radiant_team_id']:
            print('rrr')
            return match[['account_id_1','account_id_2', 'account_id_3', 'account_id_4', 'account_id_5','radiant_captain']]
        elif id_team == match['dire_team_id']:
            print('ddd')
            return match[['account_id_6', 'account_id_7', 'account_id_8', 'account_id_9','account_id_10','dire_captain']]
    abort(400, description="id2 is None")
app = Flask(__name__)
api = OpenDotaAPI(verbose=True)

# pro_matches = api.get_pro_matches_custom_sql()
# pro_matches.to_csv('pro_matches.csv') #update pro_matches
# team_info = api.get_teams_rating_db()
# team_info = team_info.fillna('_')
# team_info['team_id'].loc[6488512] = 7217630
# team_info['team_id'].loc[7136526] = 7217630
# team_info['team_id'].loc[5528463] = 5922927
# team_info = team_info.fillna('__')
# team_info.to_csv('team_info.csv')
# team_wr = {}
# capitan_wr = {}
# account_wr = {}
# elo_teams = {}
# print(123)
# X = solve2(pro_matches)
# with open('team_wr.pickle', 'wb') as f:
#     pickle.dump(team_wr,f)
# with open('capitan_wr.pickle', 'wb') as f1:
#     pickle.dump(capitan_wr,f1)
# with open('account_wr.pickle', 'wb') as f2:
#     pickle.dump(account_wr,f2)
# with open('elo_teams.pickle', 'wb') as f3:
#     pickle.dump(elo_teams,f3)

team_info = pd.read_csv('team_info.csv',index_col=0)
team_info = team_info.fillna('_')
model = pickle.load(open('model.pickle', 'rb'))
pro_matches = pd.read_csv('pro_matches.csv',index_col=0)
team_wr = pickle.load(open('team_wr.pickle', 'rb'))
capitan_wr = pickle.load(open('capitan_wr.pickle', 'rb'))
account_wr = pickle.load(open('account_wr.pickle', 'rb'))
elo_teams = pickle.load(open('elo_teams.pickle', 'rb'))
print(pro_matches.shape)

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
    id1, id2 = get_id_by_name(name1, name2)
    print(id1, id2)
    if id1 is None:
        abort(400, description="Name 1 not found")
    if id2 is None:
        abort(400, description="Name 2 not found")

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
    id1, id2 = get_id_by_name(name1, name2)
    print(id1, id2)
    if id1 is None or id is None:
        return render_template('index.html', prediction_text='{},{} fix name pls'.format(id1,id2))
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
