import pandas as pd
import pickle
team_info = pd.read_csv('team_info.csv', index_col=0)
elo_teams = pickle.load(open('elo_teams.pickle', 'rb'))

def get_id_by_name(name1):
    id1 = None
    name1 = name1.replace("-", "")
    name1 = name1.replace(" ", "")
    name1 = name1.replace(".", "")
    name1 = name1.lower().strip()
    for word in ['team', 'gaming', '!']:
        if word in name1:
            name1 = name1.replace(word, "")
    team_info_new = team_info.sort_values(by='last_match_time', ascending=False)
    if name1 == 'og':
        id1 = 2586976
    else:
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
            team_tag = team_tag.replace(".", " ")
            team_tag = team_tag.lower().strip()
            if row[1]['team_id'] ==7553952:
                print(name1)
                print(team_name )
            if (name1 == team_name) or (name1 == team_tag):
                id1 = row[1]['team_id']
                break
            else:
                if (len(team_name) != 0) and (name1 == team_name.split()[0]):
                    id1 = row[1]['team_id']
                    break

    return id1

def func(x):
    return x + 2


def test_answer():
    assert get_id_by_name('Geek Fam') == 3586078
    assert get_id_by_name('F.R.I.E.N.D.S') == 7683797
    assert get_id_by_name('Chicken Fighters') == 7553952
    for row in team_info[:50].iterrows():
        assert get_id_by_name(row[1]['name']) == row[1]['team_id']

# print(get_id_by_name('Chicken Fighters'))
print(team_info.shape)