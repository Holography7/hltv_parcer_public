from class_Program import *

class PlayerException(Exception):
    pass

class Player(Program):
    """Object of individual player statistics."""
    """Объект индивидуальной статистики игрока."""

    def __str__(self): # displays player info
        table_1 = ((*self.titles[:3], self.titles[-3], self.titles[-2], self.titles[-1]), (*self.data[:3], self.data[-3], self.data[-2], self.data[-1]))
        if self.without_stats:
            return self.str_pseudo_table(*table_1, orientation='cols', title='Main information', to_log=self.str_to_log) # return pseudo-table
        else:
            tables_stats = tuple((self.titles[3 + 6 * i:9 + 6 * i], self.data[3 + 6 * i:9 + 6 * i]) for i in range(4))
            str_main_table = self.str_pseudo_table(*table_1, orientation='cols', title='Main information', to_log=self.str_to_log)
            str_tables_stats = tuple(self.str_pseudo_table(*table, orientation='cols', to_log=self.str_to_log) for table in tables_stats)
            str_tables_stats_lines = tuple(table.split('\n') for table in str_tables_stats)
            double_tables = ['', '']
            for i in range(len(double_tables)):
                for j in range(len(str_tables_stats_lines[0 + i])):
                    double_tables[i] += str_tables_stats_lines[0 + i][j] + '\t' + str_tables_stats_lines[2 + i][j] + '\n'
            str_tables_stats = '\n\n'.join(double_tables)
            return str_main_table + '\n\n' + str_tables_stats

    def __init__(self, nickname, url_player, only_current_team=False):
        if type(nickname) != str or type(url_player) != str or type(only_current_team) != bool: # cheking that input is correct
            raise PlayerException('Player stats error: wrong input type (only str, str and bool, getted {}, {} and {}).'.format(type(nickname), type(url_player), type(only_current_team)))
        if '?' not in url_player:
            raise PlayerException('Player stats error: wrong input url_player (URL must have qerry-string with dates).')
        else:
            url_to_data = url_player[0:url_player.find('?')] # this URL writing in data
        self.titles = ('ID', 'Nickname', 'Current team', 'Kills', 'Deaths', 'Kill / Death', 'Kill / Round', 'Rounds with kills', 'Kill - Death difference ', 'Total opening kills', 'Total opening deaths', 'Opening kill ratio', 'Opening kill rating', 'Team win % after first kill', 'First kill in won rounds', '0 kill rounds', '1 kill rounds', '2 kill rounds', '3 kill rounds', '4 kill rounds', '5 kill rounds', 'Rifle kills', 'Sniper kills', 'SMG kills', 'Pistol kills', 'Grenade', 'Other', 'Rating', 'URL', 'Date of download') # titles info
        self.str_to_log = False # difficult width of tabs for print and log
        self.data = []
        self.without_stats = only_current_team
        titles_data = ('ID', 'nickname', 'current team', 'rating', 'stats URL') # needet to display error
        table_rows_titles = ('Kills', 'Deaths', 'Kill / Death', 'Kill / Round', 'Rounds with kills', 'Kill - Death difference', 'Total opening kills', 'Total opening deaths', 'Opening kill ratio', 'Opening kill rating', 'Team win percent after first kill', 'First kill in won rounds', '0 kill rounds', '1 kill rounds', '2 kill rounds', '3 kill rounds', '4 kill rounds', '5 kill rounds', 'Rifle kills', 'Sniper kills', 'SMG kills', 'Pistol kills', 'Grenade', 'Other') # same
        self.log_and_print('Uploading player {} data: step 1...'.format(nickname))
        try:
            soup = self.download_html(url_player) # https://www.hltv.org/stats/players/[ID]/[Nickname]?startDate=[Date 3 month ago]&endDate=[Date today]
            self.data.append(self.get_id_from_url(url_player)) # ID
        except ProgramException as e:
            raise PlayerException('Player stats error while downloading HTML <- {}'.format(e))
        else:
            try:
                self.data.append(soup.find('h1', class_='summaryNickname text-ellipsis').text) # Nickname
                self.data.append(soup.find(class_='SummaryTeamname text-ellipsis').text) # Current team
                rating = float(soup.find(class_='summaryStatBreakdownDataValue').text) # Rating
                url_stats = Program.source_urls[0] + soup.find('a', class_='stats-top-menu-item stats-top-menu-item-link')['href'] # stat URL where will get another data from
                Program.loading_progress['loading_points'] += 1
            except (AttributeError, TypeError) as e:
                raise PlayerException('Player stats error while downloading HTML: {} not found.'.format(titles_data[len(data)]))
        if not self.without_stats:
            self.log_and_print('Uploading player {} data: step 2...'.format(nickname))
            try:
                soup = self.download_html(url_stats) # https://www.hltv.org/stats/players/individual/[Number player]/[Nickname]?startDate=[Date 3 month ago]&endDate=[Date today]
            except ProgramException as e:
                raise PlayerException('Player stats error while downloading HTML <- {}'.format(e))
            else:
                try:
                    stats = soup.find_all(class_='stats-row') # stats table
                    if len(stats) != 24:
                        raise PlayerException('Player stats error while downloading HTML: not enought stats rows (getted {}, must be 24).'.format(len(stats)))
                    stats = [stat.span.next_sibling.text for stat in stats] # clearing tags
                    try:
                        for stat in stats: # converting to correct types
                            if '%' in stat:
                                self.data.append(float(stat.replace('%', '')))
                            elif stat == 'K - D diff.':
                                self.data.append(self.data[3] - self.data[4])
                            elif '.' in stat:
                                self.data.append(float(stat))
                            elif 'NaN' in stat:
                                self.data.append(0)
                            else:
                                self.data.append(int(stat))
                        Program.loading_progress['loading_points'] += 1
                    except ValueError as e:
                        raise PlayerException('Player stats error while converting stats to digits: {}'.format(e))
                except (AttributeError, TypeError) as e:
                    raise PlayerException('Player stats error while downloading HTML: {} not found.'.format(titles_data[len(table_rows_titles)]))
        self.data.append(rating) # Rating
        self.data.append(url_to_data) # URL
        self.data.append(datetime.isoformat(datetime.today())) # date last update
        self.data = tuple(self.data) # if self.without_stats == False then len = 29, else len = 5
