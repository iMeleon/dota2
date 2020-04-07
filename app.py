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



    def get_team_info(self, id, sleep_time=1.3):
        time.sleep(sleep_time)
        team = api.get_team_info(id)
        if team == None:
            return False
        if 'error' not in team:
            if (team['wins'] is None or team['losses'] is None):
                team['WR'] = 0.5
                team['rating'] = 988.488
                team['wins'] = 10
                team['losses'] = 10
            else:
                team['WR'] = team['wins'] / (team['losses'] + team['wins'])
            team_d = {key: [team[key]] for key in team}
            if team['team_id'] in self.team_info.index:
                self.team_info.append(pd.DataFrame(team_d, index=[team['team_id']]))
            else:
                self.team_info = pd.concat([pd.DataFrame(team_d, index=[team['team_id']]), self.team_info])
            self.team_info.to_csv("teams1.csv")
            self.team_info.to_csv("teams2.csv")
            return True
        else:
            return False

    def get_player_wr(self, id, sleep_time=1.39):
        time.sleep(sleep_time)
        player = api.get_player_wr(id)
        if 'error' not in player:
            player_dict = {}
            if (player['lose'] + player['win']) == 0:
                player_dict['WR'] = 0.5
            else:
                player_dict['WR'] = player['win'] / (player['lose'] + player['win'])
            player_dict['player_id'] = id
            players_d = {key: [player_dict[key]] for key in player_dict}
            if id in self.players_wr.index:
                self.players_wr.update(pd.DataFrame(players_d, index=[id]))
            else:
                self.players_wr = pd.concat([pd.DataFrame(players_d, index=[id]), self.players_wr])
            self.players_wr.to_csv("player_wr_1.csv")
            self.players_wr.to_csv("player_wr_2.csv")
        else:
            print(player)
            print(id)
        print(self.players_wr.shape)
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
        self.matches.to_csv("matches8_12.csv")

    def add_tean_info_row(self, row):
        radiant_id = row['radiant_team_id']
        dire_id = row['dire_team_id']
        new_row = row

        if radiant_id not in self.team_info.index:
            if self.get_team_info(radiant_id) == False:
                radiant_id = 0
        if dire_id not in self.team_info.index:
            if self.get_team_info(dire_id) == False:
                dire_id = 0
        r = 0
        d = 0
        for i, id in enumerate(row[['player_{}'.format(x) for x in range(10)]]):
            if id not in self.players_wr.index:
                self.get_player_wr(id)
                print('123')
                print(id)
                print(id not in self.players_wr.index)

            player_winrate = self.players_wr.loc[id]['WR']
            new_row['player_{}_wr'.format(i)] = player_winrate
            if i < 5:
                r += player_winrate
            else:
                d += player_winrate
        row['r_rating'] = self.team_info.loc[radiant_id]['rating']
        row['r_wr_team'] = self.team_info.loc[radiant_id]['WR']

        row['d_rating'] = self.team_info.loc[dire_id]['rating']
        row['d_wr_team'] = self.team_info.loc[dire_id]['WR']
        if (row['r_wr_team'] == 0):
            row['r_wr_team'] = 0.5
        if (row['d_wr_team'] == 0):
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

    def get_id_by_name(self, name1, name2):


        teams = api.get_teams()

        resp = {}
        id1 = None
        id2 = None
        for team in teams:
            if name1 == team['name'] or name1 == team['tag']:
                id1 = team['team_id']
        if id1 is None:
            if name1 in self.team_info['name'].values:
                id1 = self.team_info[self.team_info['name'] == name1].sort_values(by=['rating']).index[-1]
            elif name1 in data.team_info['tag'].values:
                id1 = self.team_info[self.team_info['tag'] == name1].sort_values(by=['rating']).index[-1]
        if id1 is None:
            id1 = 0
            resp['error'] = 'name1 dont exist'
        resp['id1'] = id1

        for team in teams:
            if name2 == team['name'] or name2 == team['tag']:
                id2 = team['team_id']
        if id2 is None:
            if name2 in self.team_info['name'].values:
                id2 = self.team_info[self.team_info['name'] == name2].sort_values(by=['rating']).index[-1]
            elif name2 in data.team_info['tag'].values:
                id2 = self.team_info[self.team_info['tag'] == name2].sort_values(by=['rating']).index[-1]
        if id2 is None:
            id2 = 0
            resp['error'] = 'name2 dont exist'
        resp['id2'] = id2
        return resp


app = Flask(__name__)
model = pickle.load(open('model.pkl', 'rb'))
df = pd.DataFrame()
team_info = pd.read_csv('teams1.csv', index_col=0)
player_wr = pd.read_csv("player_wr_1.csv", index_col=0)

api = OpenDotaAPI(verbose=True)
data = DataPreprocessing(team_info=team_info, players_wr=player_wr)
model = pickle.load(open('model2.pkl', 'rb'))

#print(data.players_wr.shape, data.team_info.shape)
#print(data.players_wr.loc[19672354])
#print(data.players_wr[:2])

@app.route('/predict', methods=['GET'])
def get_tasks():
    id1 = request.args.get('id1', None)
    id2 = request.args.get('id2', None)
    if id1 is None:
        abort(400, description="id1 is None")
    if id2 is None:
        abort(400, description="id2 is None")
    x1 = data.solve(int(id1), int(id2))
    result = model.predict_proba(x1)
    x2 = data.solve(int(id2), int(id1))
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
    dic = data.get_id_by_name(name1, name2)
    print(dic)
    id1 = dic['id1']
    id2 = dic['id2']
    x1 = data.solve(int(id1), int(id2))
    result = model.predict_proba(x1)
    x2 = data.solve(int(id2), int(id1))
    result2 = model.predict_proba(x2)
    resp = {'Team_1': (result[0][1] + result2[0][0]) / 2,
            'Team_2': (result[0][0] + result2[0][1]) / 2}
    if 'error' in dic:
        resp['error'] = dic['error']
    return jsonify(resp)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.errorhandler(400)
def not_found2(error):
    return make_response(jsonify({'error': error.description}), 400)


if __name__ == '__main__':
    app.run(debug=True)
