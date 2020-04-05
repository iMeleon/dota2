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

    def get_teem_players(self, team_id):
        url = "https://api.opendota.com/api/teams/{}/players".format(team_id)
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


class DataPreprocessing():
    def __init__(self, pro_matches=False, team_info=False, players_wr=False):
        # Initialize tables as empty dataframes
        if type(team_info) == pd.core.frame.DataFrame:
            self.team_info = team_info
        else:
            self.team_info = pd.DataFrame()

        if type(pro_matches) == pd.core.frame.DataFrame:
            self.pro_matches = pro_matches
        else:
            self.pro_matches = pd.DataFrame()

        if type(players_wr) == pd.core.frame.DataFrame:
            self.players_wr = players_wr
        else:
            self.players_wr = pd.DataFrame()

    def pro_matches_update(self, n=1, sleep_time=1.37, last=False):
        for i in range(n):
            if len(self.pro_matches) == 0:
                matches = api.get_recent_pro_matches(False)
                self.add_pro_match(matches[0])
            elif last:
                last_pro_match_id = self.pro_matches['match_id'].values[-1]
                matches = api.get_recent_pro_matches(last_pro_match_id)
            else:
                matches = api.get_recent_pro_matches(False)
            for i, match in enumerate(matches):
                if match['match_id'] not in self.pro_matches['match_id'].values:
                    time.sleep(sleep_time)
                    self.add_pro_match(match)
            data.pro_matches.to_pickle("./pro_maches.pkl")

    def add_pro_match(self, match):
        """ Get general information from the match and append to self.matches. """
        pro_match_col = ['match_id', 'radiant_team_id', 'radiant_name',
                         'dire_team_id', 'dire_name', 'radiant_win']
        dict_match = {key: [match[key]] for key in pro_match_col}

        local_match = api.get_match_info(match['match_id'])
        if 'error' in local_match:
            print(local_match)

        dict_match['game_mode'] = local_match['game_mode']
        dict_match['patch'] = local_match['patch']

        players = pd.DataFrame(pd.Series(
            {'player_{}'.format(i): player['account_id'] for i, player in enumerate(local_match['players'])})).T
        names = [*['r_hero_{}'.format(i) for i in range(1, 132)], *['d_hero_{}'.format(i) for i in range(1, 132)],
                 *['r_hero__ban_{}'.format(i) for i in range(1, 132)],
                 *['d_hero__ban_{}'.format(i) for i in range(1, 132)]]
        pick_bans = pd.Series({name: 0 for name in names})
        if (local_match['game_mode'] == 2) and (local_match['picks_bans'] != None):
            for move in local_match['picks_bans']:
                if move['team']:
                    if move['is_pick']:
                        pick_bans['d_hero_{}'.format(move['hero_id'])] = 1
                    else:
                        pick_bans['d_hero__ban_{}'.format(move['hero_id'])] = 1
                else:
                    if move['is_pick']:
                        pick_bans['r_hero_{}'.format(move['hero_id'])] = 1
                    else:
                        pick_bans['r_hero__ban_{}'.format(move['hero_id'])] = 1
        pi_bans_df = pd.DataFrame(pick_bans).T

        df_from_dict = pd.DataFrame(dict_match)
        self.pro_matches = self.pro_matches.append(pd.concat([df_from_dict, players, pi_bans_df], axis=1),
                                                   ignore_index=True)

    def get_team_info(self, id):
        team = api.get_team_info(id)
        if team == None:
            return False
        if 'error' not in team:
            team['WR'] = team['wins'] / (team['losses'] + team['wins'])
            team_d = {key: [team[key]] for key in team}

            if (len(self.team_info) == 0) or (id not in self.team_info['team_id'].values):
                self.team_info = self.team_info.append(pd.DataFrame(team_d), ignore_index=True)
                self.team_info.to_pickle("./teams1.pkl")
                self.team_info.to_pickle("./teams2.pkl")
            return True
        else:
            print(team)

    def get_player_wr(self, id):
        player = api.get_player_wr(id)
        if 'error' not in player:
            player_dict = {}
            if (player['lose'] + player['win']) == 0:
                player_dict['WR'] = 0.5
            else:
                player_dict['WR'] = player['win'] / (player['lose'] + player['win'])
            player_dict['player_id'] = id
            players_d = {key: [player_dict[key]] for key in player_dict}
            if (len(self.players_wr) == 0) or (id not in self.players_wr['player_id'].values):
                self.players_wr = self.players_wr.append(pd.DataFrame(players_d), ignore_index=True)
                self.players_wr.to_pickle("./player_wr_1.pkl")
                self.players_wr.to_pickle("./player_wr_2.pkl")
        else:
            print(player)
            print(id)


    def add_match_by_id(self, id, sleep_time=1.3):
        time.sleep(sleep_time)
        match = api.get_match_info(id)

        if 'error' not in match:
            self.add_match(match)
        else:
            print(match, id)

    def create_matches_from_pro(self):
        for id in self.pro_matches['match_id'].values:
            if len(self.matches) == 0:
                self.add_match_by_id(id)
                return
            if id not in self.matches['match_id'].values:
                self.add_match_by_id(id)
        self.matches.to_pickle("./matches8_12.pkl")

    def add_tean_info_row(self, row):

        if row['radiant_team_id'] not in self.team_info['team_id'].values:
            if not self.get_team_info(row['radiant_team_id']):
                row['radiant_team_id'] = 0
        if row['dire_team_id'] not in self.team_info['team_id'].values:
            if not self.get_team_info(row['dire_team_id']):
                row['dire_team_id'] = 0
        r = 0
        d = 0
        for i, id in enumerate(row[['player_{}'.format(x) for x in range(10)]]):

            if id not in self.players_wr['player_id'].values:
                self.get_player_wr(id)
            row['player_{}_wr'.format(i)] = self.players_wr[self.players_wr['player_id'] == id]['WR'].values[0]
            if i < 5:
                r += self.players_wr[self.players_wr['player_id'] == id]['WR'].values[0]
            else:
                d += self.players_wr[self.players_wr['player_id'] == id]['WR'].values[0]
        row['r_rating'] = self.team_info[self.team_info['team_id'] == row['radiant_team_id']]['rating'].values[0]
        row['r_wr_team'] = self.team_info[self.team_info['team_id'] == row['radiant_team_id']]['WR'].values[0]

        row['d_rating'] = self.team_info[self.team_info['team_id'] == row['dire_team_id']]['rating'].values[0]
        row['d_wr_team'] = self.team_info[self.team_info['team_id'] == row['dire_team_id']]['WR'].values[0]
        if row['r_wr_team'] == 0:
            row['r_wr_team'] = 0.5
        if row['d_wr_team'] == 0:
            row['d_wr_team'] = 0.5
        row['wr_team_ratio'] = row['r_wr_team'] / row['d_wr_team']
        row['wr_players_ratio'] = r / d
        row['r_wr_sum_players'] = r / 5
        row['d_wr_sum_players'] = d / 5
        row['wr_rank_ratio'] = row['r_rating'] / row['d_rating']
        return row

    def get_ids(self, radiant_name, dire_name):
        if radiant_name in self.team_info['name'].values:
            print(1)
            radiant_team_id = self.team_info[self.team_info['name'] == radiant_name]['team_id']
        elif radiant_name in self.team_info['tag'].values:
            print(2)
            radiant_team_id = self.team_info[self.team_info['tag'] == radiant_name]['team_id']
        else:
            print('Cant find {}'.formate(radiant_name))
        if len(radiant_team_id) > 1:
            local_teams = []
            for i in range(len(radiant_team_id)):
                team = api.get_team_info(radiant_team_id.iloc[i])
                if 'error' not in team:
                    local_teams.append(team)
                else:
                    print(team)
            local_teams = sorted(local_teams, key=lambda team: team['last_match_time'])
            print(sorted(local_teams, key=lambda team: team['last_match_time']))
            radiant_team_id = local_teams[-1]['team_id']
        else:
            radiant_team_id = radiant_team_id.iloc[0]

        if dire_name in self.team_info['name'].values:
            dire_name_id = self.team_info[self.team_info['name'] == dire_name]['team_id']
        elif dire_name in self.team_info['tag'].values:
            dire_name_id = self.team_info[self.team_info['tag'] == dire_name]['team_id']
        else:
            print('Cant find {}'.formate(dire_name))
        if len(dire_name_id) > 1:
            local_teams = []
            for i in range(len(dire_name_id)):
                team = api.get_team_info(dire_name_id.iloc[i])
                if 'error' not in team:
                    local_teams.append(team)
                else:
                    print(team)
            local_teams = sorted(local_teams, key=lambda team: team['last_match_time'])
            dire_name_id = local_teams[0]['team_id']
        else:
            dire_name_id = dire_name_id.iloc[0]
        return radiant_team_id, dire_name_id

    def get_team_players(self, ID):
        players = api.get_teem_players(ID)
        if 'error' in players:
            print(players)
        players = [player for player in players if
                   ((player['is_current_team_member'] == True) or (player['is_current_team_member'] is None))]
        if len(players) < 5:
            players = [player for player in players if
                       ((player['is_current_team_member'] == True) or (player['is_current_team_member'] is None))]
            for i in range(5 - len(players)):
                players.append(
                    {'account_id': 0, 'name': None, 'games_played': 10, 'wins': 5, 'is_current_team_member': None})
        else:
            players = [player for player in players if
                       ((player['is_current_team_member'] == True) or (player['is_current_team_member'] is None))]
        players = sorted(players, key=lambda player: 0 if (player['is_current_team_member'] == True) else 1)
        return players[:5]

    def solve(self, id_radiant, id_dire):
        dic = {'radiant_team_id': id_radiant, 'dire_team_id': id_dire}
        players_r = self.get_team_players(id_radiant)
        for i in range(5):
            dic['player_{}'.format(i)] = players_r[i]['account_id']
        players_d = self.get_team_players(id_dire)
        for i in range(5):
            dic['player_{}'.format(i + 5)] = players_d[i]['account_id']
        dic_1 = {key: [dic[key]] for key in dic}
        df = pd.DataFrame(dic_1)
        df = df.apply(self.add_tean_info_row, axis=1)
        df[['radiant_team_id', 'dire_team_id']] = df[['radiant_team_id', 'dire_team_id']].astype(int)
        df = df.drop(
            ['player_0', 'player_1', 'player_2', 'player_3', 'player_4', 'player_5', 'player_6', 'player_7', 'player_8',
             'player_9'], axis=1)
        return df

app = Flask(__name__)
model = pickle.load(open('model.pkl', 'rb'))
df = pd.DataFrame()
#eam_info = pd.read_pickle("teams1.pkl")

#player_wr = pd.read_pickle("./player_wr_1.pkl")



@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict',methods=['POST'])
def predict():
    '''
    For rendering results on HTML GUI
    '''
    int_features = [int(x) for x in request.form.values()]
    final_features = [np.array(int_features)]
    prediction = model.predict(final_features)

    output = round(prediction[0], 2)

    return render_template('index.html', prediction_text='Employee Salary should be $ {}'.format(output))


if __name__ == "__main__":
    app.run(debug=True)