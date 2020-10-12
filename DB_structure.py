"""Generating database structure"""
"""Генерирование структуры БД"""
# these values needed to generate columns titles in 'teams' table, used in generating of dict of database construction
maps = ('cache', 'cobblestone', 'dust2', 'inferno', 'mirage', 'nuke', 'overpass', 'season', 'train', 'tuscan', 'vertigo')
map_stats = ('times_played', 'wins', 'draws', 'losses', 'total_rounds_played', 'rounds_won', 'win_percent', 'pistol_rounds', 'pistol_rounds_won', 'pistol_round_win_percent', 'ct_round_win_percent', 't_round_win_percent')
# these values needed to generate dict of database construction
tables = ('matches', 'players', 'teams', 'dump', 'db_version') # 4 tables
col_titles = (
# 13 cols
('id', 'title', 'team_1_id', 'team_2_id', 'team_1_players_ids', 'team_2_players_ids', 'date', 'tournament', 'format', 'maps', 'status', 'result', 'url'),
# 29 cols
('id', 'player', 'current_team', 'kills', 'deaths', 'kill_per_death', 'kill_per_round', 'rounds_with_kills', 'kill_death_difference', 'total_opening_kills', 'total_opening_deaths', 'opening_kill_ratio', 'opening_kill_rating', 'team_win_percent_after_first_kill', 'first_kill_in_won_rounds', *['{}_kill_rounds'.format(count) for count in ('zero', 'one', 'double', 'triple', 'quadro', 'penta')], *['{}_kills'.format(weapon) for weapon in ('rifle', 'sniper', 'smg', 'pistol', 'grenade', 'other')], 'rating', 'url', 'date_last_update'),
# 136 cols
('id', 'team', 'rating', *['_'.join((map_cs, map_stat)) for map_cs in maps for map_stat in map_stats], 'url', 'date_last_update'),
# 528 cols
('id', 'title', 'team_1_id', 'team_2_id', 'team_1_players_ids', 'team_2_players_ids', 'date', 'tournament', 'format', 'maps', 'status', 'result', 'team_1_rating', *['_'.join(('team_1', '_'.join((map_cs, map_stat)))) for map_cs in maps for map_stat in map_stats], 'team_2_rating', *['_'.join(('team_2', '_'.join((map_cs, map_stat)))) for map_cs in maps for map_stat in map_stats], *['_'.join(('player_{}'.format(str(i + 1)), stat)) for i in range(10) for stat in ('kills', 'deaths', 'kill_per_death', 'kill_per_round', 'rounds_with_kills', 'kill_death_difference', 'total_opening_kills', 'total_opening_deaths', 'opening_kill_ratio', 'opening_kill_rating', 'team_win_percent_after_first_kill', 'first_kill_in_won_rounds', *['{}_kill_rounds'.format(count) for count in ('zero', 'one', 'double', 'triple', 'quadro', 'penta')], *['{}_kills'.format(weapon) for weapon in ('rifle', 'sniper', 'smg', 'pistol', 'grenade', 'other')], 'rating')]),
# 1 col
('build', )
)
col_types = (
('INTEGER PRIMARY KEY', 'TEXT', *['INTEGER'] * 2, *['TEXT'] * 4, 'INTEGER', *['TEXT'] * 4),
('INTEGER PRIMARY KEY', *['TEXT'] * 2, *['INTEGER'] * 2, *['REAL'] * 2, *['INTEGER'] * 4, *['REAL'] * 4, *['INTEGER'] * 12, 'REAL', 'TEXT', 'TEXT'),
('INTEGER PRIMARY KEY', 'TEXT', 'INTEGER', *[*['INTEGER'] * 6, 'REAL', *['INTEGER'] * 2, *['REAL'] * 3] * 11, 'TEXT', 'TEXT'),
('INTEGER PRIMARY KEY', 'TEXT', *['INTEGER'] * 2, *['TEXT'] * 4, 'INTEGER', *['TEXT'] * 3, *['INTEGER', *[*['INTEGER'] * 6, 'REAL', *['INTEGER'] * 2, *['REAL'] * 3] * 11] * 2, *[*['INTEGER'] * 3, *['REAL'] * 2, *['INTEGER'] * 4, *['REAL'] * 4, *['INTEGER'] * 12, 'REAL'] * 10),
('INTEGER PRIMARY KEY', )
)
TABLES = {tables[i]: {col_titles[i][j]: col_types[i][j] for j in range(len(col_titles[i]))} for i in range(len(tables))} # dict of database construction
"""Generating OLD database structure (build 4) without types"""
"""Генерирование СТАРОЙ структуры БД (билд 4) без типов"""
maps = ('Cache', 'Cobblestone', 'Dust_2', 'Inferno', 'Mirage', 'Nuke', 'Overpass', 'Season', 'Train', 'Tuscan', 'Vertigo')
map_stats = ('Times_played', 'Wins', 'Draws', 'Losses', 'Total_rounds_played', 'Rounds_won', 'Win_percent', 'Pistol_rounds', 'Pistol_rounds_won', 'Pistol_round_win_percent', 'CT_round_win_percent', 'T_round_win_percent')
tables = ('matches_upcoming', 'matches_completed', 'players', 'teams', 'DB_version') # 5 tables
col_titles = (
# 8 cols
('ID', 'Team_1', 'Team_2', 'Date_match', 'Tournament', 'Format_match', 'Maps', 'URL'),
# 10 cols
('ID', 'Team_1', 'Team_2', 'Date_match', 'Tournament', 'Format_match', 'Maps', 'Result_full', 'Result_maps', 'URL'),
# 29 cols
('ID', 'Player', 'Current_Team', 'Kills', 'Deaths', 'Kill_per_Death', 'Kill__per_Round', 'Rounds_with_kills', 'Kill_Death_difference', 'Total_opening_kills', 'Total_opening_deaths', 'Opening_kill_ratio', 'Opening_kill_rating', 'Team_win_percent_after_first_kill', 'First_kill_in_won_rounds', 'Zero_kill_rounds', 'One_kill_rounds', 'Double_kill_rounds', 'Triple_kill_rounds', 'Quadro_kill_rounds', 'Penta_kill_rounds', 'Rifle_kills', 'Sniper_kills', 'SMG_kills', 'Pistol_kills', 'Grenade', 'Other', 'Rating_2_0', 'URL'),
# 136 cols
('ID', 'Team', 'Rating', *['_'.join((map_cs, map_stat)) for map_cs in maps for map_stat in map_stats], 'URL'),
# 1 col
('Build', )
)
col_types = (
('int', *['text'] * 4, 'int', *['text'] * 2),
('int', *['text'] * 4, 'int', *['text'] * 4),
('int', *['text'] * 2, *['int'] * 25, 'text'),
('int', 'text', *['int'] * 133, 'text'),
('int', )
)
OLD_TABLES = {tables[i]: {col_titles[i][j]: col_types[i][j] for j in range(len(col_titles[i]))} for i in range(len(tables))}

__all__ = ["TABLES", "OLD_TABLES"]
