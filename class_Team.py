from class_Program import *

class TeamException(Exception):
    pass

class Team(Program):
    """Object team statistics."""
    """Объект статистики команды."""

    def __str__(self): # displays team info
        maps = ('Cache', 'Cobblestone', 'Dust2', 'Inferno', 'Mirage', 'Nuke', 'Overpass', 'Season', 'Train', 'Tuscan', 'Vertigo')
        first_col = ('Statistics', 'Times played', 'Wins', 'Draws', 'Losses', 'Total rounds played', 'Rounds won', 'Win percent', 'Pistol rounds', 'Pistol rounds won', 'Pistol round win percent', 'CT round win percent', 'T round win percent')
        table_1 = (('ID', 'Team', 'Rating', 'URL', 'Date of download'), (self.data[0], self.data[1], self.data[2], self.data[-2], self.data[-1]))
        stats = list(self.data[3:-2])
        table_2 = [first_col]
        for i in range(11): # clearing maps where stats empty (= 0)
            if stats[12 * i] != 0:
                table_2.append((maps[i], *stats[12 * i:12 * (i + 1)]))
        team_info_table = self.str_pseudo_table(*table_1, orientation='cols', title='Main information', to_log=self.str_to_log)
        if len(table_2) > 1:
            team_stat_table = self.str_pseudo_table(*table_2, orientation='cols', to_log=self.str_to_log)
        else:
            team_stat_table = ''
        return team_info_table + team_stat_table # return pseudo-tables

    def __init__(self, team_title, url_team, url_lineup_stat):
        if type(team_title) != str or type(url_team) != str: # cheking that input is correct
            raise TeamException('Team stats error: wrong input type (only str, getted {} and {}).'.format(type(nickname), type(url_player)))
        self.str_to_log = False # difficult width of tabs for print and log
        self.data = []
        titles_data = ('ID', 'team name', 'rating', 'stats URL') # needet to display error
        self.log_and_print('Uploading team {} data: step 1...'.format(team_title))
        try:
            soup = self.download_html(url_team) # https://www.hltv.org/team/[ID]/[Team name]
            self.data.append(self.get_id_from_url(url_team)) # ID
        except ProgramException as e:
            raise TeamException('Team stats error while downloading HTML <- {}'.format(e))
        else:
            try:
                self.data.append(soup.find(class_='profile-team-name text-ellipsis').text) # Team name
                rating = soup.find(class_='profile-team-stat').span.text
                if '#' in rating:
                    self.data.append(int(rating.replace('#', ''))) # Rating
                else:
                    self.data.append(-1) # Rating
            except (AttributeError, TypeError) as e:
                raise TeamException('Team stats error while downloading HTML: {} not found.'.format(titles_data[len(self.data)]))
        Program.loading_progress['loading_points'] += 1
        added_loading_points = 1
        try:
            self.log_and_print('Uploading team {} data: step 2...'.format(team_title))
            soup = self.download_html(url_lineup_stat) # https://www.hltv.org/stats/lineup/maps?lineup=[ID player 1]&lineup=[ID player 2]&lineup=[ID player 3]&lineup=[ID player 4]&lineup=[ID player 5]&minLineupMatch=3&startDate=[Date 3 month ago]&endDate=[Date today]
        except ProgramException as e:
            raise TeamException('Team stats error while downloading HTML <- {}'.format(e))
        else:
            try:
                if soup.find(class_='tabs standard-box').find_next(class_='tabs standard-box'):
                    maps = soup.find(class_='tabs standard-box').find_next(class_='tabs standard-box').find_all('a') # tags with URLs map stats
                else:
                    maps = ()
                Program.loading_progress['loading_points'] += 1
                added_loading_points += 1
                init_map_stat = [0, 0, 0, 0, 0, 0, 0., 0, 0, 0., 0., 0.] # needed to write correct types
                maps_stats = {'Cache': init_map_stat, 'Cobblestone': init_map_stat, 'Dust2': init_map_stat, 'Inferno': init_map_stat, 'Mirage': init_map_stat, 'Nuke': init_map_stat, 'Overpass': init_map_stat, 'Season': init_map_stat, 'Train': init_map_stat, 'Tuscan': init_map_stat, 'Vertigo': init_map_stat} # init maps data
                for map_cs in maps: # download maps data
                    if Program.settings[map_cs.text.lower()]: # if map cheked in active pool
                        maps_stats[map_cs.text] = [] # delete zeros
                        self.log_and_print('Uploading team {} data: step 3: map {}...'.format(team_title, map_cs.text))
                        try:
                            soup = self.download_html(Program.source_urls[0] + map_cs['href']) # https://www.hltv.org/stats/lineup/map/[ID map]?lineup=[ID player 1]&lineup=[ID player 2]&lineup=[ID player 3]&lineup=[ID player 4]&lineup=[ID player 5]&minLineupMatch=3&startDate=[Date 3 month ago]&endDate=[Date today]
                        except ProgramException as e:
                            raise TeamException('Team stats error while downloading HTML <- {}'.format(e))
                        else:
                            stats = soup.find_all(class_='stats-row') # stats table
                            if len(stats) != 10:
                                raise TeamException('Team stats error while downloading HTML: not enought stats rows (getted {}, must be 10).'.format(len(stats)))
                            stats = [stat.span.next_sibling.text for stat in stats] # convert stats to text
                            try: # convert stats to correct types
                                for stat in stats: # dowbloaded data writing to dict maps_stats because order of writing is important
                                    if '/' in stat:
                                        maps_stats[map_cs.text].extend(list(map(int, stat.split(' / '))))
                                    elif '%' in stat:
                                        maps_stats[map_cs.text].append(float(stat.replace('%', '')))
                                    else:
                                        maps_stats[map_cs.text].append(int(stat))
                                Program.loading_progress['loading_points'] += 1
                                added_loading_points += 1
                            except ValueError as e:
                                raise TeamException('Team stats error while converting stats to digits: {}'.format(e))
                for map_cs in maps_stats.values(): # maps stats
                    self.data.extend(map_cs)
                self.data.append(url_team) # URL
                self.data.append(datetime.isoformat(datetime.today())) # date last update
            except (AttributeError, TypeError) as e:
                raise TeamException('Team stats error while downloading HTML: {} not found.'.format(titles_data[len(self.data)]))
        self.data = tuple(self.data)
        maps_all = ('cache', 'cobblestone', 'dust2', 'inferno', 'mirage', 'nuke', 'overpass', 'season', 'train', 'tuscan', 'vertigo')
        if added_loading_points < (len(tuple(Program.settings[map_cs] for map_cs in maps_all if Program.settings[map_cs] == True)) + 2):
            Program.loading_progress['loading_points'] += (len(tuple(Program.settings[map_cs] for map_cs in maps_all if Program.settings[map_cs] == True)) + 2) - added_loading_points
