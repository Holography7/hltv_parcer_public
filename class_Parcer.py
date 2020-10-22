from class_Program import *
from class_Database import *
from class_Match import *
from class_Team import *
from class_Player import *

class ParcerException(Exception):
    pass

class Parcer(Program):

    def __str__(self): # return pseudo-table
        if not self.teams and not self.players:
            titles = ('ID', 'Title', 'Date', 'Tournament')
            table = self.str_pseudo_table(titles, *[match[:-1] for match in self.matches[0]], *[match[:-1] for match in self.matches[1]], orientation='rows', to_log=self.str_to_log)
        else:
            titles = ('Team', 'URL team', 'URL lineup of team')
            table = self.str_pseudo_table(titles, *self.teams, orientation='rows', to_log=self.str_to_log) # print pseudo-table
            titles = ('Player', 'URL')
            table += '\n' + self.str_pseudo_table(titles, *self.players, orientation='rows', to_log=self.str_to_log) # print pseudo-table
        return table

    def __init__(self):

        def get_match_title(match_tag):
            if str(type(match_tag)) != "<class 'bs4.element.Tag'>":
                raise ParcerException("""Parcer error while getting title upcoming match: wrong input (getted "{}", must be <class 'bs4.BeautifulSoup'>).""".format(type(match_tag)))
            if match_tag.find('div', class_='matchTeams text-ellipsis'):
                if '\n\n\n\n' in match_tag.find('div', class_='matchTeams text-ellipsis').text.strip():
                    return '{} vs {}'.format(*match_tag.find('div', class_='matchTeams text-ellipsis').text.strip().split('\n\n\n\n'))
                else:
                    return '{} vs {}'.format(*match_tag.find('div', class_='matchTeams text-ellipsis').text.strip().split('\n\n\n'))
            else:
                return match_tag.find('span', class_='line-clamp-3').text

        def get_match_tournament(match_tag):
            if str(type(match_tag)) != "<class 'bs4.element.Tag'>":
                raise ParcerException("""Parcer error while getting title upcoming match: wrong input (getted "{}", must be <class 'bs4.BeautifulSoup'>).""".format(type(match_tag)))
            if match_tag.find('div', class_='matchEventName'):
                return match_tag.find('div', class_='matchEventName').text
            else:
                return match_tag.find('span', class_='line-clamp-3').text

        def check_proxies(): # checking that proxies working
            if not Program.settings['proxy_mode']:
                self.log_and_print('Proxy mode is disabled. If you want check proxies, you must set proxy_mode=True in settings file.')
            else:
                self.log_and_print('Chekicking that proxies works...')
                bad_proxies = []
                for proxy in Program.proxies.keys():
                    self.log_and_print('Chekicking {}...'.format(proxy))
                    unstable_proxy = False
                    proxy_works = False
                    for i in range(10):
                        try:
                            start_time = datetime.today() # start point of latency
                            test_proxy = requests.get('https://www.hltv.org/matches', headers={'User-Agent': Program.user_agent}, proxies={'https': 'https://' + proxy}, timeout=60)
                            work_time = datetime.today() - start_time # end point of latency
                            if test_proxy.status_code != 200:
                                raise Exception(str(test_proxy.status_code))
                            elif test_proxy.status_code  == 403:
                                self.log_and_print('This proxy banned on HLTV.')
                                bad_proxies.append(proxy)
                                break
                            elif test_proxy.status_code == 503:
                                self.log_and_print('Bad user agent. Changing...')
                                Program.user_agent = UserAgent().chrome
                        except Exception as e: # if proxy failed
                            self.log_and_print(e)
                            if str(e) == 503:
                                self.log_and_print('Bad user agent. Changing...')
                                Program.user_agent = UserAgent().chrome
                            else:
                                unstable_proxy = True
                        else:
                            self.log_and_print('Proxy is OK.')
                            Program.proxies[proxy] = work_time.seconds * 1000 + work_time.microseconds // 1000 # add to proxy value of latency
                            proxy_works = True
                            break
                    if not proxy_works:
                        bad_proxies.append(proxy)
                    if unstable_proxy and proxy_works:
                        self.log_and_print('Proxy {} works, but has problems with connection.'.format(proxy))
                for proxy in bad_proxies:
                    Program.proxies.pop(proxy)
                if Program.proxies: # getting faster proxy
                    min_latency = min(Program.proxies.values())
                    for proxy in Program.proxies.keys():
                        if Program.proxies[proxy] == min_latency:
                            Program.faster_proxy = proxy
                            break
                else:
                    self.log_and_print('Neither proxy works. Switching to standard mode!')
                    Program.settings['proxy_mode'] = False

        # begin __init__
        self.str_to_log = False # difficult width of tabs for print and log in pseudo table
        try:
            self.Program = Program('settings.cfg')
        except ProgramException as e:
            self.log_and_print(e)
        else:
            check_proxies()
            try:
                self.DB = Database(Program.settings['db_filename'])
            except DatabaseException as e:
                if str(e) == 'Database update cancelled by user.':
                    raise ParcerException(str(e))
                self.log_and_print(e) # Recreating DB if corrupt
                recreate_DB = self.question('Parcer cannot work with this database. Corrupt database will renamed to old_{} and created new. Continue? (Y/n): '.format(Program.settings['db_filename']))
                if recreate_DB:
                    os.rename(Program.settings['db_filename'], 'old_' + Program.settings['db_filename'])
                    try:
                        self.DB = Database(Program.settings['db_filename'])
                    except DatabaseException as e:
                        raise ParcerException('Parcer error while connecting database <- {}'.format(str(e)))
                else:
                    raise ParcerException('Database corrupted, but user cancelled creating new database.')
            else:
                self.log_and_print('This is a parcer for collecting statistics about teams and players on upcoming matches in CS:GO from hltv.org. Current version: 0.6.3 alpha.')
                run_parcer = self.question('Start parcer? (Y/n): ')
                if not run_parcer:
                    raise ParcerException('Start cancelled.')
                self.log_and_print('Preparing lists of matches...')
                try:
                    soup = self.download_html('https://www.hltv.org/matches') # Download HTML with upcoming matches
                except Program_exception as e:
                    raise ParcerException('Parcer error while downloading HTML <- {}'.format(str(e)))
                else:
                    new_upcoming_matches = [tuple([self.get_id_from_url(match['href']), get_match_title(match), datetime.fromtimestamp(float(match.find('div', class_='matchTime')['data-unix']) / 1000).isoformat(' ') + '.000', get_match_tournament(match), int(match.find('div', class_='matchMeta').text[-1]), 'https://www.hltv.org' + match['href']]) for match in soup.find(class_='upcomingMatchesWrapper').find_all('a', class_='match a-reset')] # All downloaded upcoming matches. List will have IDs, titles, dates, tournaments and URLs
                    new_matches_not_need_download = [match for match in new_upcoming_matches if ' vs ' not in match[1]] # matches where teams unknown not need to download, their information is already available
                    old_upcoming_matches = self.DB.get_upcoming_matches_short() # getting IDs, titles, dates, tournaments, formats, URLs and Status of upcoming matches that already downloaded in past. It's needed to update in future.
                    old_matches_not_need_update = []
                    for old_match in old_upcoming_matches: # generate list of upcoming matches, that downloaded, but his data not changed
                        for new_match in new_upcoming_matches:
                            if old_match[0] == new_match[0]:
                                if old_match[:-1] == new_match and (old_match[-1] == 'Match upcoming' or old_match[-1] == 'Teams unknown'):
                                    old_matches_not_need_update.append(old_match)
                                break
                    IDs_old_upcoming_matches = [match[0] for match in old_upcoming_matches] # cleaning upcoming matches that already downloaded
                    for i in range(len(new_upcoming_matches) - 1, -1, -1):
                        if new_upcoming_matches[i][0] in IDs_old_upcoming_matches:
                            new_upcoming_matches.pop(i)
                    for old_match in old_matches_not_need_update: # clearing downloaded upcoming matches that information not changed
                        old_upcoming_matches.remove(old_match)
                    IDs_matches_not_need_download = [match[0] for match in new_matches_not_need_download]
                    for i in range(len(new_upcoming_matches) - 1, -1, -1):
                        if new_upcoming_matches[i][0] in IDs_matches_not_need_download:
                            new_upcoming_matches.pop(i)
                    old_matches_where_teams_unknown = self.DB.get_upcoming_matches_both_teams_unknown() # matches where teams unknown in database
                    matches_where_both_teams_still_unknown = []
                    for old_match in old_matches_where_teams_unknown:
                        for new_match in new_matches_not_need_download:
                            if old_match[0] == new_match[0]:
                                if old_match[1] == new_match[1]:
                                    matches_where_both_teams_still_unknown.append(new_match)
                                elif ' vs ' not in new_match[1]:
                                    old_upcoming_matches.remove((*old_match, 'Teams unknown'))
                                break
                    for match in matches_where_both_teams_still_unknown: # clearing old matches where teams still unknown
                        new_matches_not_need_download.remove(match)
                    new_matches_not_need_download = tuple((match[0], match[1], None, None, None, None, match[2], match[3], match[4], ', '.join(['TBA'] * match[4]), 'Teams unknown', None, match[5]) for match in new_matches_not_need_download)
                    if new_matches_not_need_download:
                        self.log_and_print('Writing matches where teams unknown in database.')
                        for match in new_matches_not_need_download:
                            self.DB.write_data(match)
                    self.matches = (tuple(old_upcoming_matches), tuple(new_upcoming_matches))
                    self.log_and_print('Lists of matches ready.')
                    self.teams = [] # list of teams that need to download
                    self.players = [] # list of players that need to download

    def download_matches(self):
        """Update matches from database and download new matches"""
        """Обновление матчей из БД и загрузка новых"""
        message = ('Step 1: Updating exist matches...', 'Step 2: Downloading new matches...')
        next = Program.settings['auto_mode']
        IDs_teams = []
        IDs_players = []
        for i in range(2):
            self.log_and_print(message[i])
            self.init_progress_bar('Step {} of 6: {}'.format(str(i + 1), message[i][8:-3]), len(self.matches[i])) # initialization loading progress bar
            for match in self.matches[i]: # 1 - update old matches, 2 - download new matches
                if i == 0:
                    match_obj = Match(*match[1:-1]) # download match
                else:
                    match_obj = Match(*match[1:])
                self.log_and_print(match_obj)
                if (match_obj.data[10] == 'Match over' or (match[-1] in ('Team 1 unknown', 'Team 2 unknown', *['{} player(s) unknown' for i in range(1, 11)]) and match_obj.data[10] == 'Match upcoming') or i == 1) and match_obj.data[10] not in ('Match deleted', 'Match postponed', 'Teams unknown'):
                    for team in match_obj.teams: # adding teams to queue of download without duplicating
                        if team[0] not in IDs_teams: # cheking that team not in self.teams (by ID)
                            date_last_update = self.DB.get_date_last_update(team[0], table='teams')
                            date_last_played_match = self.DB.get_date_last_played_match(team[0], obj='team')
                            if date_last_update < date_last_played_match or datetime.today() - datetime.fromisoformat(date_last_update) > timedelta(days=90): # if last update was before last match or was more than 90 days ago
                                self.teams.append(team[1:]) # add teams of this match to queue to download
                                IDs_teams.append(team[0]) # add ID team that not duplicate this team in future
                    for player in match_obj.players: # same for players
                        if player[0] not in IDs_players:
                            date_last_update = self.DB.get_date_last_update(player[0], table='players')
                            date_last_played_match = self.DB.get_date_last_played_match(player[0], obj='player')
                            if date_last_update < date_last_played_match or datetime.today() - datetime.fromisoformat(date_last_update) > timedelta(days=90):
                                self.players.append(player[1:])
                                IDs_players.append(player[0])
                if match_obj.data[10] == 'Match deleted': # Delete match from database if cancelled
                    self.DB.delete_data('matches', match_obj.data[0])
                else: # Write match to DB
                    self.DB.write_data(match_obj.data)
                Program.loading_progress['loading_points'] += 1
                if not Program.settings['auto_mode']:
                    next = self.question('Continue? (Y/n): ')
                    if not next:
                        raise ParcerException('User stopped parcer.')
            self.close_progress_bar()
        self.log_and_print(self)

    def download_teams(self):
        self.log_and_print('Step 3: Downloading teams stats...')
        maps = ('cache', 'cobblestone', 'dust2', 'inferno', 'mirage', 'nuke', 'overpass', 'season', 'train', 'tuscan', 'vertigo')
        self.init_progress_bar('Step 3 of 6: Downloading teams stats', len(self.teams) * (len(tuple(Program.settings[map_cs] for map_cs in maps if Program.settings[map_cs] == True)) + 2))
        for team in self.teams:
            team_obj = Team(*team) # download team stats
            self.log_and_print(team_obj)
            self.DB.write_data(team_obj.data)
            if not Program.settings['auto_mode']:
                next = self.question('Continue? (Y/n): ')
                if not next:
                    raise ParcerException('User stopped parcer.')
        self.close_progress_bar()

    def download_players(self):
        self.log_and_print('Step 4: Downloading players stats...')
        self.init_progress_bar('Step 4 of 6: Downloading players stats', len(self.players) * 2)
        for player in self.players:
            player_obj = Player(*player) # download player stats
            self.log_and_print(player_obj)
            self.DB.write_data(player_obj.data)
            if not Program.settings['auto_mode']:
                next = self.question('Continue? (Y/n): ')
                if not next:
                    raise ParcerException('User stopped parcer.')
        self.close_progress_bar()

    def check_current_team_of_players(self):
        self.log_and_print('Step 5: Updating current teams for some players...')
        players = self.DB.get_players_short()
        self.init_progress_bar('Step 5 of 6: Updating current teams for some players', len(players))
        current_team = players[0][2]
        players_current_team = []
        for player in players:
            if current_team == player[2]:
                players_current_team.append(player)
            else:
                if len(players_current_team) > 5:
                    self.log_and_print('Detected team "{}" with more that 5 players. Updating current team of this players...'.format(current_team))
                    for update_player in players_current_team:
                        player_obj = Player(update_player[1], update_player[3] + '?startDate={}&endDate={}'.format(date.isoformat(date.today() - timedelta(days=90)), date.isoformat(date.today())), only_current_team=True)
                        self.log_and_print(player_obj)
                        if current_team != player_obj.data[2]:
                            self.log_and_print('Player "{}" change current team at {}. Writing into database...'.format(update_player[1], player_obj.data[2]))
                            self.DB.update_current_team(player_obj.data[0], player_obj.data[2])
                current_team = player[2]
                players_current_team = [player]
            Program.loading_progress['loading_points'] += 1
        self.close_progress_bar()

    def dump_matches(self):
        self.log_and_print('Step 6: Dumping stats of matches...')
        dumped_upcoming_matches = self.DB.get_dump_upcoming_matches()
        new_upcoming_matches = self.DB.get_upcoming_matches_full()
        ID_matches_already_dumped = [match[0] for match in dumped_upcoming_matches]
        matches_already_dumped = []
        for match in new_upcoming_matches: # ckearing matches that already dumped
            if match[0] in ID_matches_already_dumped:
                matches_already_dumped.append(match)
        for match in matches_already_dumped:
            new_upcoming_matches.remove(match)
        self.init_progress_bar('Step 6 of 6: Dumping stats of matches', len(dumped_upcoming_matches) + len(new_upcoming_matches))
        cols = ('id', 'title', 'team_1_id', 'team_2_id', 'team_1_players_ids', 'team_2_players_ids', 'date', 'tournament', 'format', 'maps', 'status', 'result')
        if dumped_upcoming_matches:
            for match in dumped_upcoming_matches:
                current_match = self.DB.get_upcoming_match(match[0])
                if match[:12] != current_match[:12]:
                    self.log_and_print('Updating match "{}" info...'.format(match[1]))
                    for i in range(1, 12):
                        if match[i] != current_match[i]:
                            self.DB.update_dump_value(match[0], cols[i], current_match[i])
                            self.log_and_print('Data "{}" updated from "{}" to "{}"'.format(cols[i], str(match[i]), str(current_match[i])))
                            if i in (2, 3, 4, 5):
                                self.log_and_print('WARNING! Changed critical data! Stats shoud be updated!')
                Program.loading_progress['loading_points'] += 1
        if new_upcoming_matches:
            for match in new_upcoming_matches:
                data = list(match[:12])
                for i in range(2, 4):
                    data.extend(self.DB.get_team(match[i])[2:-2])
                players = [*match[4].split(', '), *match[5].split(', ')]
                for player in players:
                    data.extend(self.DB.get_player(int(player))[3:-2])
                self.DB.write_data(data)
                Program.loading_progress['loading_points'] += 1
        self.close_progress_bar()
