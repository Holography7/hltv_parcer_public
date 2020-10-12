from class_Program import *

class MatchException(Exception):
    pass

class Match(Program):
    """Object match."""
    """Объект матча."""

    def __str__(self):
        table_1 = tables_2_3 = table_4 = ''
        titles = ('ID', 'Title', 'Team 1 ID', 'Team 2 ID', 'Team 1 Players IDs', 'Team 2 Players IDs', 'Date', 'Tournament', 'Format', 'Maps', 'Status', 'Result', 'URL') # generating titles
        table_1 = self.str_pseudo_table(titles, self.data, orientation='cols', title='Match', to_log=self.str_to_log) # pseudo-table of match
        titles = (('ID', 'Team', 'URL team'), ('Team', 'URL lineup of team'))
        if self.teams:
            teams_titles = ('Teams', 'Teams lineups')
            teams_data = (tuple((team[0], team[1], team[2]) for team in self.teams), tuple((team[1], team[3]) for team in self.teams))
            tables_2_3 = '\n' + '\n'.join(tuple(self.str_pseudo_table(titles[i], *teams_data[i], orientation='rows', title=teams_titles[i], to_log=self.str_to_log) for i in range(2))) # pseudo-tables of teams
        if self.players:
            titles = ('ID', 'Player', 'URL')
            table_4 = '\n' + self.str_pseudo_table(titles, *self.players, orientation='rows', title='Players', to_log=self.str_to_log) # pseudo-table of players
        return table_1 + tables_2_3 + table_4

    def __init__(self, title, date_match, tournament, format, url):
        self.str_to_log = False # difficult width of tabs for print and log in pseudo table
        self.data = []
        self.teams = [] # Teams names, URLs and stats URLs (lineups)
        self.players = [] # Player nicknames and URLs with qerry-string of date
        titles_data = ('ID', 'title', 'team 1 ID', 'team 2 ID', 'team 1 players IDs', 'team 2 players IDs', 'date', 'tournament', 'format', 'maps', 'status', 'result', 'URL') # needet to display error
        self.log_and_print('Uploading match data...')
        self.log_and_print('Match: {}'.format(title))
        self.log_and_print('Date: {}'.format(date_match))
        self.log_and_print('Tournament: {}'.format(tournament))
        self.log_and_print('Format: Best of {}'.format(str(format)))
        try:
            soup = self.download_html(url) # https://www.hltv.org/matches/[ID]/[matchName]
            self.data.append(self.get_id_from_url(url)) # ID
        except ProgramException as e:
            raise MatchException('Match error while downloading HTML <- {}'.format(e))
        else:
            try:
                teams_titles = [team.text for team in soup.find('div', class_='standard-box teamsBox').find_all('div', class_='teamName')]
                if teams_titles != ['', '']:
                    self.data.append(teams_titles[0] + ' vs ' + teams_titles[1]) # title
                    if title != self.data[1]:
                        self.log_and_print('Match title "{}" changed to "{}"'.format(title, self.data[1]))
                else:
                    self.data.append(title)
                teams_urls = ['https://www.hltv.org' + team.find('a')['href'] for team in soup.find('div', class_='lineups').find_all('div', class_='box-headline flex-align-center')] # team 1 and team 2 URLs
                self.data.extend([self.get_id_from_url(team_url) for team_url in teams_urls]) # team 1 and team 2 IDs
                if len(self.data) == 2: # if both teams unknown
                    self.data.extend([None, None])
                    self.teams = self.players = None
                    teams_urls = [None, None]
                elif len(self.data) == 3: # if 1 team unknown
                    self.data.append(None)
                    teams_urls.append(None)
                if self.data[2] or self.data[3]:
                    players = [[player for player in team.tr.next_sibling.next_sibling.find_all('td', class_='player') if player.find('a') or player.find('div', class_='player-compare')] for team in soup.find('div', class_='lineups').find_all('div', class_='players')]
                    if players[0][0].find('a'):
                        players_IDs = [[self.get_id_from_url(player.find('a')['href']) for player in team] for team in players]
                    else:
                        players_IDs = [[int(player.find('div', class_='player-compare')['data-player-id']) for player in team] for team in players]
                    self.data.extend([', '.join([str(player_id) for player_id in team]) for team in players_IDs]) # players IDs
                    if len(self.data) == 5: # if 1 team unknown
                        self.data.append(None)
                else:
                    self.data.extend([None, None])  # if both teams unknown
                self.data.append(datetime.fromtimestamp(float(soup.find('div', class_='time')['data-unix']) / 1000).isoformat(' ') + '.000') # Local time
                if date_match != self.data[6]:
                    self.log_and_print('Match date "{}" changed to "{}"'.format(date_match, self.data[6]))
                self.data.append(soup.find('div', class_='event text-ellipsis').find('a').text) # Tournament
                if tournament != self.data[7]:
                    self.log_and_print('Match tournament "{}" changed to "{}"'.format(tournament, self.data[7]))
                self.data.append(int(soup.find('div', class_='padding preformatted-text').text.replace('Best of ', '')[0])) # format
                if format != self.data[8]:
                    self.log_and_print('Match format "Best of {}" changed to "Best of {}"'.format(str(format), str(self.data[8])))
                self.data.append(', '.join([map.text.strip() for map in soup.find_all(class_='map-name-holder')])) # maps
                self.data.append(soup.find('div', class_='countdown').text) # status. It can be chenged soon
                if self.data[10] not in ('Match over', 'Match deleted', 'Match postponed', 'LIVE'): # if getted time, considered that match upcoming
                    if not self.data[2] and not self.data[3]: # but only if both teams known
                        self.data[10] = 'Teams unknown'
                    elif not self.data[2] or not self.data[3]:
                        self.data[10] = 'Team {} unknown'.format(str(self.data[2:4].index(None) + 1))
                    else:
                        self.data[10] = 'Match upcoming'
                if self.data[10] != 'Match over':
                    self.data.append(None) # Empty result for matches that not ended
                else:
                    self.data.append(', '.join([':'.join([result.text for result in map_cs.find_all('div', class_='results-team-score')]) for map_cs in soup.find_all('div', class_='results played')])) # string of results on maps
                self.data.append(url) # URL
                # Now getting URLs on teams, lineups and players
                if self.data[7] not in ('Teams unknown', 'Match postponed', 'Match deleted'):
                    self.teams = [[self.data[2 + i], teams_titles[i], teams_urls[i], 'https://www.hltv.org/stats/lineup/maps?lineup=' + '&lineup='.join(self.data[4 + i].split(', ')) + '&minLineupMatch=3&startDate={}&endDate={}'.format(date.isoformat(date.today() - timedelta(days=90)), date.isoformat(date.today()))] for i in range(2) if self.data[2 + i]]
                    self.players = [[players_IDs[i][j], players[i][j].text.strip(), 'https://www.hltv.org/stats/players/' + str(players_IDs[i][j]) + '/' + players[i][j].text.strip() + '?startDate={}&endDate={}'.format(date.isoformat(date.today() - timedelta(days=90)), date.isoformat(date.today()))] for i in range(len(players)) for j in range(len(players[i]))] # getting list of players with nicknames and URLs stats
                    if len(self.players) < 10 and 'unknown' not in self.data[10] and self.data[10] != 'Match over':
                        self.data[10] = '{} player(s) unknown'.format(str(10 - len(self.players)))
            except (AttributeError, TypeError) as e:
                raise MatchException('Match error while downloading HTML: {} not found.'.format(titles_data[len(self.data)]))
        self.data = tuple(self.data) # locking data
        if self.teams:
            self.teams = tuple(tuple(team) for team in self.teams)
        else:
            self.teams = ()
        if self.players:
            self.players = tuple(tuple(player) for player in self.players)
        else:
            self.players = ()
