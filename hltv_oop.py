from bs4 import BeautifulSoup
import requests
import time
from datetime import datetime
import os
import shutil
import sqlite3
from datetime import date
from datetime import timedelta

class Program():
    """Main class"""
    """Основной класс"""

    def __init__(self):
        self.source_urls = ('https://www.hltv.org', '/matches', '/stats/players', '/team', '?startDate=', '&endDate=')
        self.questions = ('Start parcer? (Y/n): ',
        'The parser can work in automatic mode. If you disable it, you will be asked if you want to continue playing each match. In automatic mode, the parser operation time may take a long time. Enable automatic mode? (y/N): ',
        'Want to start? (Y/n): ',
        'Want to continue? (Y/n): ',
        'Want to recreate the database (if yes, the old database will saved as hltv_compact_old.db)? (Y/n): ',
        'Got error while downloading match. Do you want continue? (Y/n): ')
        self.DB = None
        self.DB_filename = None
        self.competitive_maps = [True, True, True, True, True, True, True, True, True, True, True] # Cache, Cobblestone, Dust2, Inferno, Mirage, Nuke, Overpass, Season, Train, Tuscan, Vertigo
        self.__settings_titles = ("filename='", "cache='", "cobblestone='", "dust2='", "inferno='", "mirage='", "nuke='", "overpass='", "season='", "train='", "tuscan='", "vertigo='")
        self.__soup = None
        self.__urls_matches_soup = None
        self.__urls_teams = []
        self.__urls_teams_stat = []
        self.__urls_players_stats = []

    def download_html(self, url):
        try:
            time.sleep(1) # If not do that, hltv.org get temporarily ban an IP address that is running the parser. (https://www.hltv.org/robots.txt)
            # Если этого не сделать, hltv.org временно забанит IP адрес, где запущен этот парсер. (https://www.hltv.org/robots.txt)
            req = requests.get(url)
            if (req.status_code == 200):
                return BeautifulSoup(req.text, 'html.parser')
            else:
                print('Error {} while uploading {} (HTML-error).'.format(str(req.status_code), url))
                return req.status_code
        except requests.Timeout as e:
            print('Error: timed out. Stopping parcing this page...')
            print(str(e))
            return 408

    def get_id_from_url(self, url):
        """Getting an ID from a URL."""
        """Получение ID из URL."""
        ID = 'None'
        for i in range(1, 4):
            if (url.count(self.source_urls[0] + self.source_urls[i])):
                ID = url.replace(self.source_urls[0] + self.source_urls[i] + '/', '')
                last_slash = ID.find('/')
                if (last_slash != -1):
                    ID = ID[0:ID.find('/')]
                else:
                    ID = '/'
                break
        if (ID.isdigit() == True):
            return ID
        else:
            print('Error 1470: ID not founded in URL {}.'.format(url))
            return '0'

    def question(self, question_message, default_answer):
        """Method for asking questions to the user."""
        """Метод для задавания вопросов пользователю."""
        while(True):
            answer = str(input(question_message))
            if answer == 'Y' or answer == 'y' or (answer == '' and default_answer):
                return True
            elif answer == 'N' or answer == 'n' or (answer == '' and not default_answer):
                return False
            else:
                print('Try again.')

    def parcing_auto(self):
        """Method for automatic parsing mode"""
        """Метод для автоматического режима парсинга"""
        for i in range(len(self.__urls_matches_soup)):
            match = Match()
            match_code_downloaded = match.download_data(self.__urls_matches_soup[i])
            if (match_code_downloaded == 200):
                match_data = match.get_data()
                urls_teams = match.get_urls_teams()
                if (not urls_teams):
                    return False
                urls_teams_stats = match.get_urls_stats_teams()
                if (not urls_teams_stats):
                    return False
                players_urls = (match.get_urls_stats_players(True), match.get_urls_stats_players(False))
                if (not players_urls[0]) and (not players_urls[1]):
                    return False
                update_stat = self.__download_stats_all(urls_teams, urls_teams_stats, players_urls, match_data)
                if (not update_stat):
                    return False
                elif (update_stat == 5136):
                    continue
            elif (match_code_downloaded == 5136):
                continue
            else:
                ignore_error = self.question(program.questions[5], True)
                if (ignore_error):
                    continue
                else:
                    print('Stopping parcer...')
                    return False
        return True

    def parcing_manually(self):
        """Method for manual parsing mode"""
        """Метод для ручного режима парсинга"""
        stop = self.question(self.questions[2], True)
        i = 0
        while (stop):
            match = Match()
            match_code_downloaded = match.download_data(self.__urls_matches_soup[i])
            if (match_code_downloaded == 200):
                match_data = match.get_data()
                urls_teams = match.get_urls_teams()
                if (not urls_teams):
                    return False
                urls_teams_stats = match.get_urls_stats_teams()
                if (not urls_teams_stats):
                    return False
                players_urls = (match.get_urls_stats_players(True), match.get_urls_stats_players(False))
                if (not players_urls[0]) and (not players_urls[1]):
                    return False
                update_stat = self.__download_stats_all(urls_teams, urls_teams_stats, players_urls, match_data)
                if (not update_stat):
                    return False
                elif (update_stat == 5136):
                    i += 1
                    if (i < len(self.__urls_matches_soup)):
                        stop = self.question(self.questions[3], True)
                    else:
                        stop = False
                    continue
            elif (match_code_downloaded == 5136):
                i += 1
                if (i < len(self.__urls_matches_soup)):
                    stop = self.question(self.questions[3], True)
                else:
                    stop = False
                continue
            else:
                ignore_error = self.question(program.questions[5], True)
                if (ignore_error):
                    continue
                else:
                    print('Stopping parcer...')
                    return False
            i += 1
            if (i < len(self.__urls_matches_soup)):
                stop = self.question(self.questions[3], True)
            else:
                stop = False
        return True


    def parcing_update(self):
        """Method to update data on added upcoming matches"""
        """Метод для обновления данных о добавленных предстоящих матчах"""
        print('Preparing list of matches...')
        self.__soup = self.download_html('https://www.hltv.org/matches')
        if (type(self.__soup) == int):
            return False
        self.__urls_matches_soup = self.__soup_get_urls_matches()
        if (not self.__urls_matches_soup):
            return False
        urls_matches_DB = self.DB.get_urls_upcomig_matches()
        if (not urls_matches_DB):
            print('Warning: list of URLs matches in DB is empty.')
            return True
        else:
            self.__urls_matches_soup = self.__soup_prepare_urls(self.__urls_matches_soup, urls_matches_DB)
            if (not self.__urls_matches_soup):
                return False
            urls_matches_DB = self.DB.get_urls_upcomig_matches()
            print('Updating info about exist matches...')
            for i in range(len(urls_matches_DB)):
                match = Match()
                match_code_downloaded = match.download_data(urls_matches_DB[i])
                if (match_code_downloaded == 200):
                    match_data = match.get_data()
                elif (match_code_downloaded == 5136):
                    continue
                elif (match_code_downloaded == 4313):
                    match_data = match.get_data()
                    id_match = match_data[4313]
                    self.DB.delete_data('matches_upcoming', id_match)
                else:
                    ignore_error = self.question(program.questions[5], True)
                    if (ignore_error):
                        continue
                    else:
                        print('Stopping parcer...')
                        return False
                if (type(match_data) == tuple):
                    if (len(match_data) == 7):
                        update = self.DB.update_data(match_data)
                        if (not update):
                            return False
                    elif (len(match_data) == 9):
                        self.DB.write_data(match_data)
                        self.DB.delete_data('matches_upcoming', match_data[0])
                        urls = match.get_urls_teams()
                        if (urls):
                            self.__urls_teams.append(urls)
                        else:
                            return False
                        urls = match.get_urls_stats_teams()
                        if (urls):
                            self.__urls_teams_stat.append(urls)
                        else:
                            return False
                        players_urls = (match.get_urls_stats_players(True), match.get_urls_stats_players(False))
                        if (players_urls[0]) and (players_urls[1]):
                            self.__urls_players_stats.append(players_urls)
                        else:
                            return False
                    else:
                        print('Error while getting match data: wrong data len. Parcer will stopped...')
                        return False
                elif (type(match_data) == int):
                    print('This match not updated. Probably, it should delete.')
            self.__urls_teams = tuple(self.__urls_teams)
            self.__urls_teams_stat = tuple(self.__urls_teams_stat)
            self.__urls_players_stats = tuple(self.__urls_players_stats)
            if (self.__urls_teams) and (self.__urls_teams_stat) and (self.__urls_players_stats):
                print('Parcer updating teams and players stats from completed matches...')
                for i in range(len(self.__urls_teams)):
                    update_stat = self.__download_stats_all(self.__urls_teams[i], self.__urls_teams_stat[i], self.__urls_players_stats[i], None)
                    if (not update_stat):
                        return False
                    elif (update_stat == 5136):
                        continue
            print('Parcer ready to collecting new matches.')
            return True

    def recreate_DB(self):
        """If DB is damaged, you must call this method to create a new one and save the old one."""
        """В случае если БД повреждена, необходимо вызвать этот метод для создания новой и сохранения старой."""
        print('Disconnecting database...')
        self.DB.disconnect()
        print('Renaming...')
        os.rename(self.DB_filename, 'old_' + self.DB_filename)
        self.DB.connect()
        DB_ready = DB.check()
        if (DB_ready):
            print('Database recreated.')
            return True
        else:
            print('Database recreate failed (unknown error).')
            return False

    def import_settings(self):
        """Importing parser settings from settings.cfg."""
        """Импортирование настроек парсера из файла settings.cfg."""
        if (os.path.isfile('settings.cfg')):
            file = open('settings.cfg', 'r')
        else:
            print("Error while reading settings.cfg: file not found.")
            return False
        file_data = file.read()
        for i in range(len(self.__settings_titles)):
            start_point = file_data.find(self.__settings_titles[i]) + len(self.__settings_titles[i])
            if (start_point == len(self.__settings_titles[i]) - 1):
                print("Error while reading settings.cfg: {} not found.".format(self.__settings_titles[i]))
                return False
            end_point = file_data.find("'", start_point)
            if (end_point == -1):
                print("Error while reading settings.cfg: symbol closing ' not found.")
                return False
            field_value = file_data[start_point:end_point]
            if (field_value):
                if (i == 0):
                    self.DB_filename = field_value
                    self.DB = Database(field_value)
                else:
                    if (field_value == 'True'):
                        self.competitive_maps[i-1] = True
                    elif (field_value == 'False'):
                        self.competitive_maps[i-1] = False
                    else:
                        print('Error while reading settings.cfg: {} value cannot be readen.'.format(self.__settings_titles[i]))
                        return False
            else:
                print('Error while reading settings.cfg: {} value cannot be readen.'.format(self.__settings_titles[i]))
                return False
        return True

    def __soup_get_urls_matches(self):
        """Parsing URLs to upcoming matches."""
        """Парсинг URL на предстоящие матчи."""
        block_upcomig_matches = self.__soup.find(class_='upcoming-matches')
        if (not block_upcomig_matches):
            print('Error while searching block "upcoming-matches". Parcer will stopped...')
            return None
        all_upcoming_matches = block_upcomig_matches.find_all('a', class_='a-reset')
        if (not all_upcoming_matches):
            print('Error while searching URLs on upcoming matches (there are not upcoming matches?). Parcer will stopped...')
            return None
        urls_matches_soup = [self.source_urls[0] + all_upcoming_matches[i]['href'] for i in range(len(all_upcoming_matches))]
        return urls_matches_soup

    def __soup_prepare_urls(self, urls_matches_soup, urls_matches_DB):
        """Changing the URLs in DB (with the same ID) and return the URLs of upcoming matches that are not in the DB."""
        """Изменение URL в БД (с одинаковыми ID) и вывод URL предстоящих матчей, которых нет в БД."""
        IDs_matches_soup = [int(self.get_id_from_url(urls_matches_soup[i])) for i in range(len(urls_matches_soup))]
        if (IDs_matches_soup.count(0) != 0):
            print('Error while getting IDs matches from URLs on upcoming matches (getted ID = 0). Parcer will stopped...')
            return None
        IDs_matches_DB = self.DB.get_ids_upcoming_matches()
        if (not IDs_matches_DB):
            print('Error while getting IDs matches from DB. Parcer will stopped...')
            return None
        for i in range(len(IDs_matches_DB)):
            if (IDs_matches_soup.count(IDs_matches_DB[i]) >= 1):
                if (IDs_matches_soup.count(IDs_matches_DB[i]) > 1):
                    print('Warning: probably, URL corrupted (all_upcoming_matches contains the same matches)')
                for j in range(IDs_matches_soup.count(IDs_matches_DB[i])):
                    index_ID_match_DB = IDs_matches_soup.index(IDs_matches_DB[i])
                    if (urls_matches_soup[index_ID_match_DB] != urls_matches_DB[i]):
                        print ('Changing URL "{}" to "{}"'.format(urls_matches_DB[i], urls_matches_soup[index_ID_match_DB]))
                        updated_url = self.DB.change_upcoming_match_url(IDs_matches_soup[index_ID_match_DB], urls_matches_soup[index_ID_match_DB])
                        if (not updated_url):
                            return None
                    IDs_matches_soup.pop(index_ID_match_DB)
                    urls_matches_soup.pop(index_ID_match_DB)
        return urls_matches_soup

    def __download_player_current_team(self, url): # Для этапа проверки принадлежности игроков к команде
        print('Uploading player data: step 1...')
        soup = self.download_html(url) # https://www.hltv.org/stats/players/[ID]/[Nickname]
        if (type(soup) == int):
            return None
        team_current = soup.find('a', class_='a-reset text-ellipsis')
        if (team_current):
            return team_current.text
        else:
            team_current = soup.find(class_='SummaryTeamname text-ellipsis')
            if (team_current):
                return team_current.text
            else:
                print('Error: cannot get current team. Skipping...')
                return None

    def __download_stats_all(self, urls_teams, urls_teams_stats, urls_players, match_data):
        """Getting statistics of teams and players and write into DB."""
        """Получение статистики команд и игроков и запись их в БД."""
        teams = (Team(), Team())
        teams_data = [[], []]
        players_data = [[], []]
        for i in range(len(teams)):
            success_download = teams[i].download_data(urls_teams[i], urls_teams_stats[i])
            if (success_download == 200):
                teams_data[i] = teams[i].get_data()
                if (teams_data[i]):
                    print(teams_data[i]) # For debug
                    print(len(teams_data[i])) # For debug
                else:
                    return None
            elif (success_download == 5136):
                return 5136
            else:
                return None
        teams_data = tuple(teams_data)
        players = ((Player(), Player(), Player(), Player(), Player()), ((Player(), Player(), Player(), Player(), Player())))
        for i in range(len(players)):
            for j in range(len(players[i])):
                success_download = players[i][j].download_data(urls_players[i][j])
                if (success_download == 200):
                    players_data[i].append(players[i][j].get_data())
                    if (players_data[i][j]):
                        print(players_data[i][j]) # For debug
                    else:
                        return None
                elif (success_download == 5136):
                    return 5136
                else:
                    return None
            players_data[i] = tuple(players_data[i])
        players_data = tuple(players_data)
        if (match_data):
            write_in_DB = self.__write_data_in_DB(match_data, teams_data, players_data)
        else:
            write_in_DB = self.__write_data_in_DB(None, teams_data, players_data)
        if (write_in_DB):
            return 200
        else:
            return None

    def __write_data_in_DB(self, match, teams, players):
        """Writing statistics of teams and players into DB."""
        """Запись статистики команд и игроков в БД."""
        if (match):
            written = self.DB.write_data(match)
            if (not written):
                return False
        if (teams):
            for i in range(len(teams)):
                written = self.DB.write_data(teams[i])
                if (not written):
                    return False
        if (players):
            for i in range(len(players)):
                for j in range(len(players[i])):
                    written = self.DB.write_data(players[i][j])
                    if (not written):
                        return False
        return True

    def backup_DB(self):
        if (os.path.exists('backup_db')):
            if (os.path.isfile(self.DB_filename)):
                shutil.copy(self.DB_filename, 'backup_db')
            else:
                print("Error while backuping DB: file DB not found.")
                return False
        else:
            os.mkdir('backup_db')
            if (os.path.isfile(self.DB_filename)):
                shutil.copy(self.DB_filename, 'backup_db')
            else:
                print("Error while backuping DB: file DB not found.")
                return False
        print('Database backuped successfully.')
        return True

    def update_current_team_of_players(self):
        """Update information about the player's current team."""
        """Обновление информации о текущей команде игрока."""
        print('Parcer updating current teams for players...')
        teams = self.DB.get_teams_titles()
        for i in range(len(teams)):
            players = self.DB.get_players_of_current_team(teams[i])
            if (len(players) > 5):
                for j in range(len(players)):
                    player = Player()
                    current_team = player.download_current_team(players[j][2], players[j][1])
                    if (current_team):
                        if (current_team != teams[i]):
                            print('Current team is "{}". Team in database is "{}". Changing...'.format(current_team, teams[i]))
                            success_update = self.DB.update_current_team(players[j][0], current_team)
                            if (not success_update):
                                return False
                    else:
                        return False
        return True

class Database(Program):

    def __init__(self, db_name):
        self.source_urls = ('https://www.hltv.org', '/matches', '/stats/players', '/team', '?startDate=', '&endDate=')
        self.__conn = sqlite3.connect(db_name)
        self.__cursor = self.__conn.cursor()
        self.__tables_tuple = ('matches_upcoming', 'matches_completed', 'players', 'teams', 'DB_version')
        self.__columns_tables = (
        ('ID', 'Team_1', 'Team_2', 'Date_match', 'Format_match', 'Maps', 'URL'),
        ('ID', 'Team_1', 'Team_2', 'Date_match', 'Format_match', 'Maps', 'Result_full', 'Result_maps', 'URL'),
        ('ID', 'Player', 'Current_Team', 'Kills', 'Deaths', 'Kill_per_Death', 'Kill__per_Round', 'Rounds_with_kills', 'Kill_Death_difference', 'Total_opening_kills', 'Total_opening_deaths', 'Opening_kill_ratio', 'Opening_kill_rating', 'Team_win_percent_after_first_kill', 'First_kill_in_won_rounds', 'Zero_kill_rounds', 'One_kill_rounds', 'Double_kill_rounds', 'Triple_kill_rounds', 'Quadro_kill_rounds', 'Penta_kill_rounds', 'Rifle_kills', 'Sniper_kills', 'SMG_kills', 'Pistol_kills', 'Grenade', 'Other', 'Rating_2_0', 'URL'),
        ('ID', 'Team', 'Rating', 'Cache_Times_played', 'Cache_Wins', 'Cache_Draws', 'Cache_Losses', 'Cache_Total_rounds_played', 'Cache_Rounds_won', 'Cache_Win_percent', 'Cache_Pistol_rounds', 'Cache_Pistol_rounds_won', 'Cache_Pistol_round_win_percent', 'Cobblestone_Times_played', 'Cobblestone_Wins', 'Cobblestone_Draws', 'Cobblestone_Losses', 'Cobblestone_Total_rounds_played', 'Cobblestone_Rounds_won', 'Cobblestone_Win_percent', 'Cobblestone_Pistol_rounds', 'Cobblestone_Pistol_rounds_won', 'Cobblestone_Pistol_round_win_percent', 'Dust_2_Times_played', 'Dust_2_Wins', 'Dust_2_Draws', 'Dust_2_Losses', 'Dust_2_Total_rounds_played', 'Dust_2_Rounds_won', 'Dust_2_Win_percent', 'Dust_2_Pistol_rounds', 'Dust_2_Pistol_rounds_won', 'Dust_2_Pistol_round_win_percent', 'Inferno_Times_played', 'Inferno_Wins', 'Inferno_Draws', 'Inferno_Losses', 'Inferno_Total_rounds_played', 'Inferno_Rounds_won', 'Inferno_Win_percent', 'Inferno_Pistol_rounds', 'Inferno_Pistol_rounds_won', 'Inferno_Pistol_round_win_percent', 'Mirage_Times_played', 'Mirage_Wins', 'Mirage_Draws', 'Mirage_Losses', 'Mirage_Total_rounds_played', 'Mirage_Rounds_won', 'Mirage_Win_percent', 'Mirage_Pistol_rounds', 'Mirage_Pistol_rounds_won', 'Mirage_Pistol_round_win_percent', 'Nuke_Times_played', 'Nuke_Wins', 'Nuke_Draws', 'Nuke_Losses', 'Nuke_Total_rounds_played', 'Nuke_Rounds_won', 'Nuke_Win_percent', 'Nuke_Pistol_rounds', 'Nuke_Pistol_rounds_won', 'Nuke_Pistol_round_win_percent', 'Overpass_Times_played', 'Overpass_Wins', 'Overpass_Draws', 'Overpass_Losses', 'Overpass_Total_rounds_played', 'Overpass_Rounds_won', 'Overpass_Win_percent', 'Overpass_Pistol_rounds', 'Overpass_Pistol_rounds_won', 'Overpass_Pistol_round_win_percent', 'Season_Times_played', 'Season_Wins', 'Season_Draws', 'Season_Losses', 'Season_Total_rounds_played', 'Season_Rounds_won', 'Season_Win_percent', 'Season_Pistol_rounds', 'Season_Pistol_rounds_won', 'Season_Pistol_round_win_percent', 'Train_Times_played', 'Train_Wins', 'Train_Draws', 'Train_Losses', 'Train_Total_rounds_played', 'Train_Rounds_won', 'Train_Win_percent', 'Train_Pistol_rounds', 'Train_Pistol_rounds_won', 'Train_Pistol_round_win_percent', 'Tuscan_Times_played', 'Tuscan_Wins', 'Tuscan_Draws', 'Tuscan_Losses', 'Tuscan_Total_rounds_played', 'Tuscan_Rounds_won', 'Tuscan_Win_percent', 'Tuscan_Pistol_rounds', 'Tuscan_Pistol_rounds_won', 'Tuscan_Pistol_round_win_percent', 'Vertigo_Times_played', 'Vertigo_Wins', 'Vertigo_Draws', 'Vertigo_Losses', 'Vertigo_Total_rounds_played', 'Vertigo_Rounds_won', 'Vertigo_Win_percent', 'Vertigo_Pistol_rounds', 'Vertigo_Pistol_rounds_won', 'Vertigo_Pistol_round_win_percent', 'URL'),
        ('Build',))
        self.__new_columns_tables = ('URL', 'Cache_Times_played', 'Cache_Wins', 'Cache_Draws', 'Cache_Losses', 'Cache_Total_rounds_played', 'Cache_Rounds_won', 'Cache_Win_percent', 'Cache_Pistol_rounds', 'Cache_Pistol_rounds_won', 'Cache_Pistol_round_win_percent', 'Cobblestone_Times_played', 'Cobblestone_Wins', 'Cobblestone_Draws', 'Cobblestone_Losses', 'Cobblestone_Total_rounds_played', 'Cobblestone_Rounds_won', 'Cobblestone_Win_percent', 'Cobblestone_Pistol_rounds', 'Cobblestone_Pistol_rounds_won', 'Cobblestone_Pistol_round_win_percent', 'Season_Times_played', 'Season_Wins', 'Season_Draws', 'Season_Losses', 'Season_Total_rounds_played', 'Season_Rounds_won', 'Season_Win_percent', 'Season_Pistol_rounds', 'Season_Pistol_rounds_won', 'Season_Pistol_round_win_percent', 'Tuscan_Times_played', 'Tuscan_Wins', 'Tuscan_Draws', 'Tuscan_Losses', 'Tuscan_Total_rounds_played', 'Tuscan_Rounds_won', 'Tuscan_Win_percent', 'Tuscan_Pistol_rounds', 'Tuscan_Pistol_rounds_won', 'Tuscan_Pistol_round_win_percent')
        self.__tables_db = {7: 'matches_upcoming', 9: 'matches_completed', 29: 'players', 114: 'teams'}
        self.__key_words = {7: 'match', 9: 'match', 29: 'player', 114: 'team'}
        self.__create_tables_commands = (
        """CREATE TABLE matches_upcoming({} int, {} text, {} text, {} text, {} int, {} text, {} text)""".format(*self.__columns_tables[0]),
        """CREATE TABLE matches_completed({} int, {} text, {} text, {} text, {} int, {} text, {} text, {} text, {} text)""".format(*self.__columns_tables[1]),
        """CREATE TABLE players({} int, {} text, {} text, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} text)""".format(*self.__columns_tables[2]),
        """CREATE TABLE teams({} int, {} text, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} text)""".format(*self.__columns_tables[3]),
        """CREATE TABLE DB_version({} int)""".format(*self.__columns_tables[4]))

    def __del__(self):
        self.__conn.close()

    def check(self):
        """Checking current database"""
        """Проверка текущей БД"""
        self.__cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        list_tables = self.__cursor.fetchall()
        if (list_tables):
            for i in range(len(list_tables)):
                list_tables[i] = list_tables[i][0]
            list_tables = tuple(list_tables)
        check_tables = [False, False, False, False, False]
        for i in range(len(check_tables)):
            if (list_tables.count(self.__tables_tuple[i]) == 1):
                check_tables[i] = True
        if (check_tables == [True, True, True, True, True]):
            """If the database has all tables, they will be checked for the contents of all columns"""
            """Если БД имеет все таблицы, то они будут проверены на содержание всех колонок"""
            columns_exist = self.check_columns_tables(5)
            if (columns_exist):
                DB_version = self.get_DB_build()
                if (DB_version == 3):
                    print('Database build 3.')
                    print('Database is ready.')
                    return True
                elif (DB_version == 2):
                    print('Database is outdated (build 2)! Updating...')
                    success_update = self.update_DB_from_2_build()
                    if (success_update == False):
                        return False
                    else:
                        print('Success updated.')
                        return True
                elif (DB_version == 1):
                    print('Wrong value of version database detected (when database was build 1 it has not table DB_version)! Parcer cannot use this database.')
                    return False
                elif (DB_version > 3):
                    print('This program using the database build 3, but build {} detected! Parcer cannot use this database.'.format(str(DB_version)))
                    return False
                else:
                    print('Wrong value of version database detected! Parcer cannot use this database.')
                    return False
            else:
                print('DB Error: some columns not exist.')
                return False
        elif (check_tables == [True, True, True, True, False]):
            """If the database does not have a table with the version of the database, it will be created, and the database is updated to build 2. But before that the columns in the tables will be checked"""
            """Если БД не имеет таблицы с версией БД, то она будет создана, а БД обновлена до билда 2. Но перед этим будут проверены колонки в таблицах"""
            print('Database is outdated (legacy)! Updating...')
            columns_exist = self.check_columns_tables(4)
            if (columns_exist):
                success_update = self.update_DB_from_legacy()
                if (success_update):
                    print('Success updated to build 2.')
                    success_update = self.update_DB_from_2_build()
                    if (success_update):
                        print('Success updated.')
                        return True
                    else:
                        return False
                    return True
                else:
                    return False
            else:
                print('DB Error: some columns not exist.')
                return False
        elif (check_tables == [False, False, False, False, False]):
            """If the database does not have all the tables, they will be created"""
            """Если БД не имеет всех таблиц, то они будут созданы"""
            print('Creating database...')
            success_creating = self.create()
            return success_creating
        else:
            print('Database is corrupted!')
            return False

    def write_data(self, data):
        """Writing data to the database: the size of the data tuple can only be 7, 9, 29, or 114.
        The sizes of input tuples can be changed in future versions of the parser.
        If the data is already exist in the table, it will be automatically updated."""
        """Запись данных в БД: размер кортежа data может быть только = 7, 9, 29 или 114.
        Размеры принимаемых кортежей могут быть изменены в будущих версиях парсера.
        Если данные уже существуют в таблице, они будут автоматически обновлены."""
        if ((len(data) == 7) or (len(data) == 9) or (len(data) == 29) or (len(data) == 114)):
            self.__cursor.execute("SELECT ID FROM {};".format(self.__tables_db[len(data)]))
            IDs = self.__cursor.fetchall()
            IDs_list = [IDs[i][0] for i in range(len(IDs))]
            Data_exist = IDs_list.count(int(data[0]))
            if (Data_exist):
                print('This {} already exist. Data will be updated...'.format(self.__key_words[len(data)]))
                self.update_data(data)
            else:
                if (len(data) == 7): # Upcoming match
                    self.__cursor.execute("INSERT INTO matches_upcoming VALUES(?, ?, ?, ?, ?, ?, ?);", data)
                elif (len(data) == 9): # Completed match
                    self.__cursor.execute("INSERT INTO matches_completed VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?);", data)
                elif (len(data) == 29): # Player data
                    self.__cursor.execute("INSERT INTO players VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", data)
                elif (len(data) == 114): # Team data

                    self.__cursor.execute("INSERT INTO teams VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", data)
                self.__conn.commit()
            return True
        else:
            print('Error: Size of "data" not a 7, 9, 29, or 114; data is not added into database.')
            return False

    def update_data(self, data):
        """Updating data in the database: the size of the data tuple can only be = 7, 9, 29, or 114.
        The sizes of accepted tuples will be changed in future versions of the parser.
        Determining the row whose data will be updated is performed by checking the ID match.
        Updating is carried out by deleting the old row and adding a new one."""
        """Обновление данных в БД: размер кортежа data может быть только = 7, 9, 29, или 114.
        Размеры принимаемых кортежей будут изменены в будущих версиях парсера.
        Определение строки, данные которой будут обновляться, осуществляется проверкой совпадения ID.
        Обновление осуществляется путём удаления старой строки и добавлением новой."""
        if ((len(data) == 7) or (len(data) == 9) or (len(data) == 29) or (len(data) == 114)):
            self.__cursor.execute("SELECT ID FROM {} WHERE ID = {};".format(self.__tables_db[len(data)], data[0]))
            founded_ID = self.__cursor.fetchall()
            if (founded_ID):
                err = self.delete_data(self.__tables_db[len(data)], founded_ID[0][0])
                if (err == 200):
                    if (len(data) == 7): # Upcoming match
                        self.__cursor.execute("INSERT INTO matches_upcoming VALUES(?, ?, ?, ?, ?, ?, ?);", data)
                    elif (len(data) == 9): # Completed match
                        self.__cursor.execute("INSERT INTO matches_completed VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?);", data)
                    elif (len(data) == 29): # Player data
                        self.__cursor.execute("INSERT INTO players VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", data)
                    elif (len(data) == 114): # Team data

                        self.__cursor.execute("INSERT INTO teams VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", data)
                    self.__conn.commit()
                    return True
                else:
                    print('While deleting old data getting error. Changes cancelled.')
                    return False
            else:
                print('Error: URL from "data" not founded; data is not updated.')
                return False
        else:
            print('Error: Size of "data" not a 7, 9, 29, or 114; data is not updated.')
            return False

    def delete_data(self, table, ID):
        """Deleting row from table."""
        """Удаление строки из таблицы."""
        if (self.__tables_tuple.count(table) == 1):
            if (str(ID).isdigit()):
                self.__cursor.execute("SELECT * FROM {} WHERE ID = {};".format(table, str(ID)))
                data_existing = self.__cursor.fetchall()
                if (data_existing != []):
                    self.__cursor.execute("DELETE FROM {} WHERE ID = {};".format(table, str(ID)))
                    self.__conn.commit()
                    return 200
                else:
                    print('Error: "ID" not founded; data is not deleted.')
                    return 1414
            else:
                print('Error: "ID" is not a number; data is not deleted.')
                return 1415
        else:
            print('Error: "table" not founded; data is not deleted.')
            return 6461

    def delete_all_data_from_table(self, table):
        """Deleting all rows from table."""
        """Удаление строки из таблицы."""
        if (self.__tables_tuple.count(table) == 1):
            self.__cursor.execute("DELETE FROM {};".format(table))
            self.__conn.commit()
            print('Data in table {} fully deleted.'.format(table))
            return 200
        else:
            print('Error: "table" not founded; data is not deleted.')
            return 6461

    def get_urls_upcomig_matches(self):
        """Getting the URLs of upcoming matches."""
        """Получение URL предстоящих матчей."""
        self.__cursor.execute("SELECT URL FROM matches_upcoming ORDER BY Date_match;")
        data = self.__cursor.fetchall()
        if (data):
            for i in range(len(data)):
                data[i] = data[i][0]
            data = tuple(data)
            return data
        else:
            return data

    def update_DB_from_legacy(self):
        """Updating DB from legacy version. Support for previous versions will soon be discontinued.""" # Legacy version was never released to the public, lol
        """Обновление БД с устаревшей версии. Поддержка предыдущих версий вскоре будет прекращена."""
        for i in range(4):
            self.__cursor.execute('SELECT ID, Link FROM {};'.format(self.__tables_tuple[i]))
            IDs_and_Links = self.__cursor.fetchall()
            IDs_and_Links_changing = [list(IDs_and_Links[j]) for j in range(len(IDs_and_Links))]
            for j in range(len(IDs_and_Links_changing)):
                new_id = self.get_id_from_url(IDs_and_Links_changing[j][1])
                if (new_id.isdigit()) and (new_id != '0'):
                    IDs_and_Links_changing[j][0] = int(new_id)
                    self.__cursor.execute("UPDATE {} SET ID = {} WHERE Link = '{}';".format(self.__tables_tuple[i], str(IDs_and_Links_changing[j][0]), IDs_and_Links_changing[j][1]))
                else:
                    return False
        self.__cursor.execute("""CREATE TABLE DB_version(Build int)""")
        self.__cursor.execute("INSERT INTO DB_version VALUES(2);")
        self.__conn.commit()
        return True

    def update_DB_from_2_build(self):
        """Updating DB from build 2. Support for previous versions will soon be discontinued."""
        """Обновление БД с билда 2. Поддержка предыдущих версий вскоре будет прекращена."""
        tables_names = ('players', 'teams', 'matches_upcoming', 'matches_completed')
        self.__cursor.execute('SELECT Build FROM DB_version;')
        DB_version = self.__cursor.fetchall()
        if (DB_version[0][0] == 3):
            print('Database build is 3.')
        elif (DB_version[0][0] == 2):
            for i in range(len(self.__tables_tuple) - 1):
                self.__cursor.execute('ALTER TABLE {} RENAME TO {}_old;'.format(self.__tables_tuple[i], self.__tables_tuple[i]))
                self.__cursor.execute(self.__create_tables_commands[i])
                if (i == 3):
                    self.__cursor.execute('SELECT * FROM teams_old;')
                    old_data = self.__cursor.fetchall()
                    new_data = [list(old_data[j][:3]) for j in range(len(old_data))]
                    for j in range(len(new_data)):
                        new_data[j].extend([0]*20)
                        new_data[j].extend(old_data[j][3:53])
                        new_data[j].extend([0]*10)
                        new_data[j].extend(old_data[j][53:63])
                        new_data[j].extend([0]*10)
                        new_data[j].extend(old_data[j][63:74])
                        self.__cursor.execute('INSERT INTO teams VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);', new_data[j])
                else:
                    self.__cursor.execute('INSERT INTO {} SELECT * FROM {}_old;'.format(self.__tables_tuple[i], self.__tables_tuple[i]))
                self.__cursor.execute('DROP TABLE {}_old;'.format(self.__tables_tuple[i]))
            self.__cursor.execute('UPDATE DB_version SET Build = 3 WHERE Build = 2;')
            self.__conn.commit()
            return True
        else:
            print ('Error while updating database: value of version database is corrupted (got version = "{}").'.format(DB_version))
            return False

    def check_columns_tables(self, count_tables):
        """Checking for columns in the table."""
        """Проверка наличия столбцов в таблице."""
        if (count_tables == 4):
            DB_version = 1
        else:
            DB_version = self.get_DB_build()
        back = 0
        if (type(count_tables) == int):
            success = True
            for i in range(count_tables):
                self.__cursor.execute("pragma table_info({});".format(self.__tables_tuple[i]))
                info_columns = self.__cursor.fetchall()
                names_columns = [info_columns[i][1] for i in range(len(info_columns))]
                for j in range(len(names_columns)):
                    if (names_columns[j-back] != self.__columns_tables[i][j]):
                        if (names_columns[j-back] == 'Link') and ((DB_version == 2) or (DB_version == 1)):
                            continue
                        elif (self.__new_columns_tables.count(self.__columns_tables[i][j]) == 1) and ((DB_version == 2) or (DB_version == 1)):
                            back += 1
                            continue
                        print('Column {} from table {} not exist!'.format(self.__columns_tables[i][j], self.__tables_tuple[i]))
                        success = False
                        break
                back = 0
                if (not success):
                    break
            return success
        else:
            return False

    def create(self):
        """Creating an empty database."""
        """Создание пустой БД."""
        try:
            for i in range(len(self.__create_tables_commands)):
                self.__cursor.execute(self.__create_tables_commands[i])
            self.__cursor.execute("INSERT INTO DB_version VALUES(3);")
            self.__conn.commit()
            return True
        except sqlite3.Error as e:
            print("Error while creating database: {}".format(str(e)))
            return False
        except Exception as e:
            print("Unknown error while creating database: {}".format(str(e)))
            return False

    def get_ids_upcoming_matches(self):
        """Getting the IDs of upcoming matches."""
        """Получение ID предстоящих матчей."""
        self.__cursor.execute('SELECT ID FROM matches_upcoming ORDER BY Date_match;')
        data = self.__cursor.fetchall()
        if (data):
            data_IDs = [data[i][0] for i in range(len(data))]
            data_IDs = tuple(data_IDs)
            return data_IDs
        else:
            return None

    def change_upcoming_match_url(self, ID_match, new_url):
        """Changing the URL of the upcoming match by ID."""
        """Изменение URL предстоящего матча по ID."""
        if (type(ID_match) == int) and (type(new_url) == str):
            self.__cursor.execute('UPDATE matches_upcoming SET URL = "{}" WHERE ID = {};'.format(new_url, str(ID_match)))
            self.__conn.commit()
            print('Changed.')
            return True
        else:
            print('Error while updating URL in matches_upcoming: wrong input data into function(getted ID_match = "{}" and new_url = "{}")'.format(ID_match, new_url))
            return False

    def get_DB_build(self):
        """Getting the build of DB."""
        """Получение билда БД."""
        try:
            self.__cursor.execute('SELECT Build FROM DB_version;')
            build = self.__cursor.fetchall()
            if (len(build) == 1):
                if (str(build[0][0]).isdigit()):
                    return build[0][0]
                else:
                    return False
            else:
                return False
        except sqlite3.Error as e:
            print("Error while getting build version database: {}".format(str(e)))
            return False
        except Exception as e:
            print("Unknown error while getting build version database: {}".format(str(e)))
            return False

    def get_teams_titles(self):
        self.__cursor.execute('SELECT Team FROM teams ORDER BY Team;')
        teams = self.__cursor.fetchall()
        return tuple([teams[i][0] for i in range(len(teams))])

    def get_players_of_current_team(self, team):
        self.__cursor.execute('SELECT ID, Player, URL FROM players WHERE Current_Team = "{}" ORDER BY Current_Team;'.format(team))
        return tuple(self.__cursor.fetchall())

    def update_current_team(self, ID, current_team):
        try:
            self.__cursor.execute('UPDATE players SET Current_Team = "{}" WHERE ID = {};'.format(current_team, str(ID)))
            self.__conn.commit()
            print('Changed successfully.')
            return True
        except sqlite3.Error as e:
            print("Error while updating current team of player: {}".format(str(e)))
            return False
        except Exception as e:
            print("Unknown error while updating current team of player: {}".format(str(e)))
            return False

class Match(Program):
    """Object match."""
    """Объект матча."""

    def __init__(self):
        self.__soup = None
        self.__url = None
        self.__ID = None
        self.__teams_titles = []
        self.__date = None
        self.__format = None
        self.__maps = None
        self.__result_full = None
        self.__result_maps = None
        self.status = None
        self.__urls_teams = []
        self.__urls_teams_stats = []
        self.__urls_players = [[], []]
        self.__score_types = ('won', 'tie', 'lost')
        self.source_urls = ('https://www.hltv.org', '/matches', '/stats/players', '/team', '?startDate=', '&endDate=')
        self.lineup_url = ('/stats/lineup/maps?', 'minLineupMatch=3', '&startDate=')

    def download_data(self, url):
        """Parsing match data."""
        """Парсинг данных матча."""
        print('Uploading match data...')
        self.__soup = self.download_html(url) # https://www.hltv.org/matches/[ID]/[matchName]
        if (type(self.__soup) == int):
            self.status = self.__soup
            return self.status
        self.__url = url
        self.__ID = self.get_id_from_url(url)
        if (self.__ID == '0'):
            self.status = 1470
            return self.status
        self.status = 5136
        if (self.__soup.find('div', class_='time')):
            self.__date = datetime.fromtimestamp(float(self.__soup.find('div', class_='time')['data-unix'])/1000).isoformat(' ') + '.000' # Местное время
            print('Date: ' + self.__date)
        else:
            print('Time of this match are still unknown. Skipping...')
            return 5136
        self.__teams_titles = (self.__soup_get_team_info(True, False), self.__soup_get_team_info(False, False))
        if (self.__teams_titles[0]) and (self.__teams_titles[1]):
            print('Match: {} vs {}'.format(self.__teams_titles[0], self.__teams_titles[1]))
        else:
            return 5136
        self.__urls_teams = (self.__soup_get_team_info(True, True), self.__soup_get_team_info(False, True))
        if (not self.__urls_teams[0]) or (not self.__urls_teams[1]):
            return 5136
        self.__format = self.__soup_get_match_format()
        if (self.__format):
            print('Format: Best of ' + str(self.__format))
        else:
            return 5136
        self.__maps = self.__soup_get_maps()
        if (self.__maps):
            print('Maps: ' + self.__maps)
        else:
            return 5136
        self.status = self.__soup_get_match_status()
        if (self.status == 10001) or (self.status == 10002):
            if (self.status == 10001):
                self.__result_maps = self.__soup_get_result_maps()
                if (not self.__result_maps):
                    return 5136
                self.__result_full = self.__soup_get_result_full()
                if (not self.__result_full):
                    return 5136
            self.__urls_teams_stats = (self.__soup_get_url_team_stat(True), self.__soup_get_url_team_stat(False))
            if (not self.__urls_teams_stats[0]) or (not self.__urls_teams_stats[1]):
                return 5136
            self.__urls_players = (self.__soup_get_urls_team_stats_players(True), self.__soup_get_urls_team_stats_players(False))
            if (not self.__urls_players[0]) or (not self.__urls_players[1]):
                return 5136
        elif (self.status == 4313):
            return 4313
        elif (self.status == 5136):
            return 5136
        self.status = 200
        return 200

    def get_data(self):
        """Getting match data."""
        """Получение данных матча."""
        if (self.status == 200):
            if ((self.__result_full == None) or (self.__result_maps == None)):
                data = (self.__ID, *self.__teams_titles, self.__date, self.__format, self.__maps, self.__url)
            else:
                data = (self.__ID, *self.__teams_titles, self.__date, self.__format, self.__maps, self.__result_full, self.__result_maps, self.__url)
            return data
        elif (self.status == 4313):
            return {self.status: self.__ID}
        else:
            print('Data is corrupted.')
            return self.status

    def get_urls_teams(self):
        """Getting URLs teams."""
        """Получение URL команд."""
        if (self.status == 200):
            data = tuple([*self.__urls_teams])
            return data
        else:
            print('Data is corrupted.')
            return None

    def get_urls_stats_teams(self):
        """Getting URLs teams stats."""
        """Получение URL статистик команд."""
        if (self.status == 200):
            data = tuple([*self.__urls_teams_stats])
            return data
        else:
            print('Data is corrupted.')

    def get_urls_stats_players(self, team_bool):
        """Getting URLs players stats."""
        """Получение URL статистик игроков."""
        team = {True: 0, False: 1}
        if (self.status == 200) or (self.status == 0):
            if (type(team_bool) == bool):
                data = self.__urls_players[team[team_bool]]
                return data
            else:
                print('Error: got variable not "bool".')
                return None
        else:
            print('Data is corrupted.')
            return None

    def __soup_get_team_info(self, team_1, url_bool):
        """Parsing the team name or URL depending on the boolean team_1 (True = team 1, False = team 2) and url_bool (False = team name, True = team URL)."""
        """Парсинг названия или URL команды в зависимости от булевых team_1 (True = команда 1, False = команда 2) и url_bool (False = название команды, True = URL команды)."""
        classes_dict = {True: 'team1-gradient', False: 'team2-gradient'}
        teams_dict = {True: '1', False: '2'}
        team = self.__soup.find('div', class_=classes_dict[team_1])
        if (team):
            if (url_bool):
                if (team.find('a')):
                    return self.source_urls[0] + team.find('a')['href']
                else:
                    print('In this match, team {} URL are still unknown. Skipping...'.format(teams_dict[team_1]))
                    return None
            else:
                return team.find(class_='teamName').text
        else:
            print('In this match, the team {} are still unknown. Skipping...'.format(teams_dict[team_1]))
            return None

    def __soup_get_match_format(self):
        """Parsing the match format (Best of 1, 2, 3...)."""
        """Парсинг формата матча (BO1, BO2, BO3...)."""
        text_map = self.__soup.find('div', class_='padding preformatted-text')
        if (text_map):
            text_map = text_map.text
            if (text_map.count('Best of') == 1):
                return int(text_map[8:9])
            else:
                print('This match has unstandart or corrupt maps block. Skipping...')
                return None
        else:
            print('This match has not maps block. Skipping...')
            return None

    def __soup_get_maps(self):
        """Parsing the maps of match."""
        """Парсинг карт матча."""
        maps = self.__soup.find_all(class_='map-name-holder')
        if (maps):
            maps_list = [maps[i].find(class_='mapname').text for i in range(len(maps))]
            maps_text = ''
            for i in range(len(maps_list)):
                maps_text += maps_list[i] + ', '
            return maps_text[0:len(maps_text)-2]
        else:
            print('This match has unstandart or corrupt maps block. Skipping...')
            return None

    def __soup_get_match_status(self):
        """Parsing the status of the match (not started (10002), over (10001), postponed (5136), deleted (4313))."""
        """Парсинг статуса матча (не начался (10002), завершился (10001), отложен (5136), удалён (4313))."""
        match_status = self.__soup.find('div', class_='countdown')
        if (match_status):
            if (match_status.text == 'Match over'):
                return 10001
            elif (match_status.text == 'Match deleted'):
                print('This match cancelled. Deleting...')
                return 4313
            elif (match_status.text == 'Match postponed'):
                print('This match postponed. Skipping...')
                return 5136
            else:
                return 10002
        else:
            print('This match has not div.countdown block. Skipping...')
            return 5136

    def __soup_get_result_maps(self):
        """Parsing the basic result of the match. Use only when status of the match is over!"""
        """Парсинг общего результата матча. Использовать только если статус матча завершён!"""
        team_1 = self.__soup.find('div', class_='team1-gradient')
        team_2 = self.__soup.find('div', class_='team2-gradient')
        team_1_result = team_1.find('div', class_=self.__score_types[0])
        team_2_result = team_2.find('div', class_=self.__score_types[2])
        f = 1
        while(not team_1_result):
            if (f > 2):
                print("This match has not results maps or there's unstandart or broken block. Skipping...")
                return None
            team_1_result = team_1.find('div', class_=self.__score_types[f])
            team_2_result = team_2.find('div', class_=self.__score_types[2-f])
            f += 1
        return '{}:{}'.format(team_1_result.text, team_2_result.text)

    def __soup_get_result_full(self):
        """Parsing the results of the match by maps. Use only when status of the match is over!"""
        """Парсинг результата матча по картам. Использовать только если статус матча завершён!"""
        full_result_list = self.__soup.find_all('div', class_='results played')
        if (full_result_list):
            full_result_str = ''
            for i in range(len(full_result_list)):
                full_results = full_result_list[i].find_all('div', class_='results-team-score')
                if (full_results):
                    full_result_str += '{}:{}, '.format(full_results[0].text, full_results[1].text)
                else:
                    print("This match has not result on map %d or there's unstandart or broken block. Skipping..." % i)
                    return None
            return full_result_str[0:len(full_result_str)-2]
        else:
            maps = self.__soup.find_all('div', class_='mapname')
            if (maps):
                for i in range(len(maps)):
                    maps[i] = maps[i].text
            else:
                print("This match has not maps or broken block. Skipping...")
                return None
            if (maps.count('Default') > 0):
                return 'Forfeit'
            else:
                print("This match has not results per map or there's unstandart or broken block. Skipping...")
                return None

    def __soup_get_url_team_stat(self, team_1):
        """Parsing URL for team statistics (if team_1 = True - team 1, False - team 2). If the match is over, the URL is generated by the parser, since it is not on the page."""
        """Парсинг URL на статистику команды (если team_1 = True - команда 1, False - команда 2). Если матч окончен, URL генерируется парсером, так как на странице она отсутствует."""
        teams_dict = {True: 0, False: 1}
        if (self.status == 10002):
            teams_stats = self.__soup.find(class_='map-stats-infobox-header')
            if (teams_stats):
                urls_teams_stats = teams_stats.find_all(class_='team')
                if (urls_teams_stats):
                    return self.source_urls[0] + urls_teams_stats[teams_dict[team_1]].find('a')['href']
                else:
                    print('This match has not URL for team %d stat. Skipping...' % (teams_dict[team_1] + 1))
                    return None
            else:
                print('This match has not URLs for teams stats. Skipping...')
                return None
        elif (self.status == 10001):
            lineups = self.__soup.find_all('div', class_='lineup standard-box')
            if (lineups):
                tr = lineups[teams_dict[team_1]].find_all('tr')
                if (tr):
                    players = tr[1].find_all('div', class_='flagAlign')
                    if (players):
                        if (len(players) == 5):
                            IDs_players = []
                            for i in range(5):
                                if (players[i].text == '\nTBA\n') or (players[i].text == '\nTBD\n'):
                                    print('This match has not player {} in team {}. Skipping...'.format(str(i + 1), str(teams_dict[team_1] + 1)))
                                    return None
                                else:
                                    IDs_players.append('lineup=' + players[i]['data-player-id'] + '&')
                            url = '{}{}{}{}{}{}{}{}{}{}{}{}'.format(self.source_urls[0], self.lineup_url[0], *IDs_players, self.lineup_url[1], self.lineup_url[2], date.isoformat(date.today() - timedelta(days=90)), self.source_urls[5], date.isoformat(date.today()))
                            return url
                        else:
                            print('In this match team {} have less than 5 players. Skipping...'.format(str(teams_dict[team_1] + 1)))
                            return None
                    else:
                        print('This match has not players blocks. Skipping...')
                        return None
                else:
                    print("This match has not tr blocks. Skipping...")
                    return None
            else:
                print("This match has not lineups blocks. Skipping...")
                return None

        else:
            print("Error while getting team stat URL: status match is incorrect. Skipping...")
            return None

    def __soup_get_urls_team_stats_players(self, team_1):
        """Parsing URL for players statistics (if team_1 = True - from team 1, False - from team 2)."""
        """Парсинг URL на статистику игроков (если team_1 = True - из команды 1, False - из команды 2)."""
        teams_dict = {True: 0, False: 1}
        lineups = self.__soup.find_all('div', class_='lineup standard-box')
        if (not lineups):
            print("This match has not lineups. Skipping...")
            return None
        players_nicknames = lineups[teams_dict[team_1]].find_all('div', class_='text-ellipsis')
        if (len(players_nicknames) < 5):
            print('In team %d some players still unknown. Skipping...' % (teams_dict[team_1] + 1))
            return None
        if (self.status == 10002):
            players_compare = lineups[teams_dict[team_1]].find_all('div', class_='player-compare')
            if (len(players_compare) < 10):
                print('In team %d some players have not statistic page. Skipping...' % (teams_dict[team_1] + 1))
                return None
            for i in range(int(len(players_compare)/2-1), -1, -1):
                players_compare.pop(i)
        elif (self.status == 10001):
            tr = lineups[teams_dict[team_1]].find_all('tr')
            if (tr):
                players = tr[1].find_all('div', class_='flagAlign')
                if (not players):
                    print("This match has not players blocks. Skipping...")
                    return None
            else:
                print("This match has not tr blocks. Skipping...")
                return None
        else:
            print("Error while getting players stats URLs: status match is incorrect. Skipping...")
            return None
        date_today = date.isoformat(date.today())
        date_3_month_ago = date.isoformat(date.today() - timedelta(days=90))
        urls_players = []
        for i in range(5):
            nickname = players_nicknames[i].text
            if (nickname == 'TBA') or (nickname == 'TBD'):
                print('In team %d some players still unknown. Skipping...' % (teams_dict[team_1] + 1))
                return None
            if (self.status == 10002):
                id_player = players_compare[i]['data-player-id']
            elif (self.status == 10001):
                id_player = players[i]['data-player-id']
            else:
                print("Error while getting players stats URLs: status match is incorrect. Skipping...")
                return None
            if (id_player == '0'):
                print('In team %d some players has not ID. Skipping...' % (teams_dict[team_1] + 1))
                return None
            urls_players.append('{}{}/{}/{}{}{}{}{}'.format(self.source_urls[0], self.source_urls[2], id_player, nickname, self.source_urls[4], date_3_month_ago, self.source_urls[5], date_today))
        return tuple(urls_players)

class Team(Program):
    """Object team statistics."""
    """Объект статистики команды."""

    def __init__(self):
        self.__soup_1 = None
        self.__soup_2 = None
        self.__url = None
        self.__ID = 0
        self.__team = None
        self.__rating = None
        self.__maps_data = (Map_stats(), Map_stats(), Map_stats(), Map_stats(), Map_stats(), Map_stats(), Map_stats(), Map_stats(), Map_stats(), Map_stats(), Map_stats())
        #                     Cache     Cobblestone     Dust 2      Inferno       Mirage        Nuke       Overpass      Season       Train        Tuscan      Vertigo
        self.status = None
        self.__active_maps = program.competitive_maps
        self.__maps_titles = ('Cache', 'Cobblestone', 'Dust2', 'Inferno', 'Mirage', 'Nuke', 'Overpass', 'Season', 'Train', 'Tuscan', 'Vertigo')
        self.source_urls = ('https://www.hltv.org', '/matches', '/stats/players', '/team', '?startDate=', '&endDate=')

    def download_data(self, url_1, url_2):
        """Parsing team data."""
        """Парсинг данных команды."""
        print('Uploading team data: step 1...')
        self.__soup_1 = self.download_html(url_1) # https://www.hltv.org/team/[ID]/[Team name]
        if (type(self.__soup_1) == int):
            self.status = self.__soup_1
            return self.status
        self.__url = url_1
        self.__ID = self.get_id_from_url(url_1)
        if (self.__ID == '0'):
            self.status = 1470
            return 1470
        self.status = 5136
        self.__team = self.__soup_1.find(class_='profile-team-name text-ellipsis')
        if (self.__team):
            self.__team = self.__team.text
        else:
            print('This team has not name block. Skipping...')
            return 5136
        self.__rating = self.__soup_get_team_rating()
        if (not self.__rating):
            return 5136
        print('Uploading team {} data: step 2...'.format(self.__team))
        self.__soup_2 = self.download_html(url_2) # https://www.hltv.org/stats/lineup/maps?lineup=[ID player 1]&lineup=[ID player 2]&lineup=[ID player 3]&lineup=[ID player 4]&lineup=[ID player 5]&minLineupMatch=3&startDate=[Date 3 month ago]&endDate=[Date today]
        if (type(self.__soup_2) == int):
            self.status = self.__soup_2
            return self.status
        stats_urls = self.__soup_get_stats_urls()
        if (stats_urls):
            for i in range(len(self.__maps_data)):
                download_map_stat = self.__maps_data[i].download_data(stats_urls[i], self.__team, self.__maps_titles[i])
                if (download_map_stat != 5136) and (download_map_stat != 200):
                    return download_map_stat
                elif (download_map_stat == 5136):
                    return 5136
            print('Team statistics download complete.')
            self.status = 200
            return 200
        elif (stats_urls == [None, None, None, None, None, None, None, None, None, None, None]):
            print('Not critical error while getting team stats URLs: tuple have not any URL (team not played any competitive map?). Skipping...')
            return 5136
        else:
            return 5136

    def get_data(self):
        """Getting team data."""
        """Получение данных команды."""
        if (self.status == 200):
            data = [self.__ID, self.__team, self.__rating]
            for i in range(len(self.__maps_data)):
                data.extend(self.__maps_data[i].get_data())
            data.append(self.__url)
            data = tuple(data)
            return data
        elif (self.status == 5136):
            return None
        else:
            print('Data is corrupted.')
            return None

    def __soup_get_team_rating(self):
        """Parcing team rating."""
        """Парсинг рейтинга команды."""
        rating = self.__soup_1.find(class_='profile-team-stat')
        if (rating):
            rating_text = rating.text
            rating_text = rating_text.replace('World ranking', '')
            if (rating_text.count('#') == 1):
                return int(rating_text.replace('#', ''))
            else:
                return 'unknown'
        else:
            print('This team has not rating block. Skipping...')
            return None

    def __soup_get_stats_urls(self):
        """Parcing URL team stats by maps."""
        """Парсинг URL статистик команды по картам."""
        block_maps = self.__soup_2.find_all(class_='tabs standard-box')
        if (len(block_maps) == 2):
            block_maps = block_maps[1]
            maps_urls = block_maps.find_all('a')
            soup_maps_titles = block_maps.find_all('a')
            if (maps_urls):
                for i in range(len(maps_urls)):
                    maps_urls[i] = self.source_urls[0] + maps_urls[i]['href']
                    soup_maps_titles[i] = soup_maps_titles[i].text
                full_maps_urls = [None, None, None, None, None, None, None, None, None, None, None]
                for i in range(len(self.__active_maps)):
                    if (soup_maps_titles.count(self.__maps_titles[i]) == 1) and (self.__active_maps[i]):
                        url_index = soup_maps_titles.index(self.__maps_titles[i])
                        full_maps_urls[i] = maps_urls[url_index]
                return tuple(full_maps_urls)
            else:
                print('In this team, the maps statistics have not URLs. Skipping...')
                return None
        else:
            print('In this team, the maps statistics are still unknown. Skipping...')
            return None

class Map_stats(Program):
    """Team statistics object on the certain map."""
    """Объект статистики команды на определённой карте."""

    def __init__(self):
        self.__soup = None
        self.__times_played = None
        self.__wins = None
        self.__draws = None
        self.__losses = None
        self.__total_rounds_played = None
        self.__rounds_won = None
        self.__win_percent = None
        self.__pistol_rounds = None
        self.__pistol_rounds_won = None
        self.__pistol_round_win_percent = None
        self.status = None
        self.__table_rows_names = ('Times played', 'Wins / draws / losses', 'Total rounds played', 'Rounds won', 'Win percent', 'Pistol rounds', 'Pistol rounds won', 'Pistol round win percent', 'CT round win percent', 'T round win percent')

    def download_data(self, url, team_name, map_name):
        """Parsing map stat."""
        """Парсинг статистики карты."""
        if (url):
            print('Uploading team {} data: step 3: map {}...'.format(team_name, map_name))
            self.__soup = self.download_html(url) # https://www.hltv.org/stats/lineup/map/[ID map]?lineup=[ID player 1]&lineup=[ID player 2]&lineup=[ID player 3]&lineup=[ID player 4]&lineup=[ID player 5]&minLineupMatch=3&startDate=[Date 3 month ago]&endDate=[Date today]
            if (type(self.__soup) == int):
                self.status = self.__soup
                return self.status
            self.status = 5136
            data_team_map = self.__soup_get_data()
            if (data_team_map):
                self.__times_played = data_team_map[0]
                self.__wins = data_team_map[1]
                self.__draws = data_team_map[2]
                self.__losses = data_team_map[3]
                self.__total_rounds_played = data_team_map[4]
                self.__rounds_won = data_team_map[5]
                self.__win_percent = data_team_map[6]
                self.__pistol_rounds = data_team_map[7]
                self.__pistol_rounds_won = data_team_map[8]
                self.__pistol_round_win_percent = data_team_map[9]
                self.status = 200
                return 200
            else:
                return 5136
        else:
            self.__times_played = 0
            self.__wins = 0
            self.__draws = 0
            self.__losses = 0
            self.__total_rounds_played = 0
            self.__rounds_won = 0
            self.__win_percent = 0
            self.__pistol_rounds = 0
            self.__pistol_rounds_won = 0
            self.__pistol_round_win_percent = 0
            self.status = 200
            return 200

    def get_data(self):
        """Getting map stat data."""
        """Получение данных статистики карты."""
        if (self.status == 200):
            data = (self.__times_played, self.__wins, self.__draws, self.__losses, self.__total_rounds_played, self.__rounds_won, self.__win_percent, self.__pistol_rounds, self.__pistol_rounds_won, self.__pistol_round_win_percent)
            return data
        else:
            print('Data is corrupted.')
            return self.status

    def __soup_get_data(self):
        """Parsing map stat data."""
        """Парсинг данных статистики карты."""
        stats = self.__soup.find_all(class_='stats-row')
        if (len(stats) == 10):
            for i in range(len(stats)):
                stats[i] = stats[i].text.replace(self.__table_rows_names[i], '')
            stats[1] = stats[1].split(' / ')
            stats[4] = stats[4][0:len(stats[4])-1]
            stats[7] = stats[7][0:len(stats[7])-1]
            stats[8] = stats[8][0:len(stats[8])-1]
            stats[9] = stats[9][0:len(stats[9])-1]
            data_team_map = []
            for i in range(len(stats)):
                if (i != 1):
                    stats[i] = float(stats[i])
                    if (stats[i].is_integer() == True):
                        stats[i] = int(stats[i])
                    data_team_map.append(stats[i])
                else:
                    for j in range(len(stats[i])):
                        stats[i][j] = int(stats[i][j])
                        data_team_map.append(stats[i][j])
            return tuple(data_team_map)
        else:
            print('In this team, the map statistic have not some rows. Skipping...')
            return None

class Player(Program):
    """Object of individual player statistics."""
    """Объект индивидуальной статистики игрока."""

    def __init__(self):
        self.__soup_1 = None
        self.__soup_2 = None
        self.__ID = None
        self.__nickname = None
        self.__current_team = None
        self.__kills = None
        self.__deaths = None
        self.__kill_per_death = None
        self.__kill_per_round = None
        self.__rounds_with_kills = None
        self.__kill_death_difference = None
        self.__total_opening_kills = None
        self.__total_opening_deaths = None
        self.__opening_kill_ratio = None
        self.__opening_kill_rating = None
        self.__team_win_percent_after_first_kill = None
        self.__first_kill_in_won_rounds = None
        self.__0_kill_rounds = None
        self.__1_kill_rounds = None
        self.__2_kill_rounds = None
        self.__3_kill_rounds = None
        self.__4_kill_rounds = None
        self.__5_kill_rounds = None
        self.__rifle_kills = None
        self.__sniper_kills = None
        self.__smg_kills = None
        self.__pistol_kills = None
        self.__grenade = None
        self.__other = None
        self.__rating_2_0 = None
        self.__url = None
        self.status = None
        self.source_urls = ('https://www.hltv.org', '/matches', '/stats/players', '/team', '?startDate=', '&endDate=')
        self.__table_rows_names = ('Kills', 'Deaths', 'Kill / Death', 'Kill / Round', 'Rounds with kills', 'Kill - Death differenceK - D diff.', 'Total opening kills', 'Total opening deaths', 'Opening kill ratio', 'Opening kill rating', 'Team win percent after first kill', 'First kill in won rounds', '0 kill rounds', '1 kill rounds', '2 kill rounds', '3 kill rounds', '4 kill rounds', '5 kill rounds', 'Rifle kills', 'Sniper kills', 'SMG kills', 'Pistol kills', 'Grenade', 'Other')

    def download_data(self, url_1):
        """Parsing player data."""
        """Парсинг данных игрока."""
        print('Uploading player data: step 1...')
        self.__soup_1 = self.download_html(url_1) # https://www.hltv.org/stats/players/[ID]/[Nickname]?startDate=[Date 3 month ago]&endDate=[Date today]
        if (type(self.__soup_1) == int):
            self.status = self.__soup_1
            return self.status
        self.__ID = self.get_id_from_url(url_1)
        if (self.__ID == '0'):
            self.status = 1470
            return self.status
        self.status = 5136
        self.__nickname = self.__soup_1.find('h1', class_='summaryNickname text-ellipsis')
        if (self.__nickname):
            self.__nickname = self.__nickname.text
        else:
            print('This player has not some nickname. Skipping...')
            return 5136
        self.__current_team = self.__soup_get_current_team()
        if (not self.__current_team):
            return 5136
        self.__url = self.__soup_get_url(url_1)
        if (not self.__url):
            return 5136
        self.__rating_2_0 = self.__soup_get_player_rating()
        url_2 = self.__soup_1.find('a', class_='stats-top-menu-item stats-top-menu-item-link')
        if (not url_2):
            return 5136
        else:
            url_2 = self.source_urls[0] + url_2['href']
        print('Uploading player {} data: step 2...'.format(self.__nickname))
        self.__soup_2 = self.download_html(url_2) # https://www.hltv.org/stats/players/individual/[Number player]/[Nickname]?startDate=[Date 3 month ago]&endDate=[Date today]
        if (type(self.__soup_2) == int):
            self.status = self.__soup_2
            return self.status
        rows = self.__soup_get_rows_data()
        if (rows):
            self.__kills = rows[0]
            self.__deaths = rows[1]
            self.__kill_per_death = rows[2]
            self.__kill_per_round = rows[3]
            self.__rounds_with_kills = rows[4]
            self.__kill_death_difference = rows[5]
            self.__total_opening_kills = rows[6]
            self.__total_opening_deaths = rows[7]
            self.__opening_kill_ratio = rows[8]
            self.__opening_kill_rating = rows[9]
            self.__team_win_percent_after_first_kill = rows[10]
            self.__first_kill_in_won_rounds = rows[11]
            self.__0_kill_rounds = rows[12]
            self.__1_kill_rounds = rows[13]
            self.__2_kill_rounds = rows[14]
            self.__3_kill_rounds = rows[15]
            self.__4_kill_rounds = rows[16]
            self.__5_kill_rounds = rows[17]
            self.__rifle_kills = rows[18]
            self.__sniper_kills = rows[19]
            self.__smg_kills = rows[20]
            self.__pistol_kills = rows[21]
            self.__grenade = rows[22]
            self.__other = rows[23]
            self.status = 200
            return 200
        else:
            return 5136

    def get_data(self):
        """Getting player data."""
        """Получение данных игрока."""
        if (self.status == 200):
            data = (self.__ID, self.__nickname, self.__current_team, self.__kills, self.__deaths, self.__kill_per_death, self.__kill_per_round, self.__rounds_with_kills, self.__kill_death_difference, self.__total_opening_kills, self.__total_opening_deaths, self.__opening_kill_ratio, self.__opening_kill_rating, self.__team_win_percent_after_first_kill, self.__first_kill_in_won_rounds, self.__0_kill_rounds, self.__1_kill_rounds, self.__2_kill_rounds, self.__3_kill_rounds, self.__4_kill_rounds, self.__5_kill_rounds, self.__rifle_kills, self.__sniper_kills, self.__smg_kills, self.__pistol_kills, self.__grenade, self.__other, self.__rating_2_0, self.__url)
            return data
        else:
            print('Data is corrupted.')

    def download_current_team(self, url, nickname):
        print('Uploading current team of player {}...'.format(nickname))
        self.__soup_1 = self.download_html(url) # https://www.hltv.org/stats/players/[ID]/[Nickname]
        if (type(self.__soup_1) == int):
            self.status = self.__soup_1
            return self.status
        self.__current_team = self.__soup_get_current_team()
        return self.__current_team

    def __soup_get_current_team(self):
        """Parsing current team of player."""
        """Парсинг текущей команды игрока."""
        team_current = self.__soup_1.find('a', class_='a-reset text-ellipsis')
        if (team_current):
            return team_current.text
        else:
            team_current = self.__soup_1.find(class_='SummaryTeamname text-ellipsis')
            if (team_current):
                return team_current.text
            else:
                print('Error: cannot get current team. Skipping...')
                return None

    def __soup_get_url(self, dirt_url):
        """Parsing URL of player."""
        """Парсинг URL игрока."""
        if (dirt_url.count('?') == 0):
            print('Error: the URL does not contain the period of statistics collection. Skipping...')
            return None
        elif (dirt_url.count('?') == 1):
            return dirt_url[0:dirt_url.find('?')]
        else:
            print('Warning: probably URL is corrupted.')
            return dirt_url[0:dirt_url.find('?')]

    def __soup_get_player_rating(self):
        """Parsing rating 2.0 of player."""
        """Парсинг рейтинга 2.0 игрока."""
        rating = self.__soup_1.find(class_='summaryStatBreakdownDataValue')
        if (rating):
            rating = rating.text
            if (rating.count('.') == 1):
                return float(rating)
            elif (rating.count('.') == 0):
                return int(rating)
            else:
                print('Error: the rating 2.0 is not a number. Skipping...')
                return None

    def __soup_get_rows_data(self):
        """Parsing stat of player data."""
        """Парсинг данных статистики игрока."""
        rows = self.__soup_2.find_all(class_='stats-row')
        if (rows):
            for i in range(len(rows)):
                rows[i] = rows[i].text
                rows[i] = rows[i].replace(self.__table_rows_names[i], '')
                if((i == 10) or (i == 11)):
                    rows[i] = rows[i][0:len(rows[i])-1]
                if (rows[i] == ''):
                    rows[i] = 0
                rows[i] = float(rows[i])
                if(rows[i].is_integer()):
                    rows[i] = int(rows[i])
            return rows
        else:
            print('Error: the stats table not exist. Skipping...')
            return None

"""Main executable code"""
"""Основной исполняемый код"""
program = Program()
deny_start = False
print('This is a parcer for collecting statistics about teams and players on upcoming matches in CS:GO from hltv.org. Current version: 0.4.5 alpha.')
import_cfg = program.import_settings()
if (import_cfg):
    print('Config imported successfully.')
else:
    print('Parser terminated with error.')
DB_ready = program.DB.check()
if (not DB_ready):
    print("Got error while checking or updating database.")
    repair_DB = program.question(program.questions[4], True)
    if (repair_DB):
        program.recreate_DB()
    else:
        deny_start = True
backup_db = program.backup_DB()
if (backup_db):
    if (deny_start):
        start = False
    else:
        start = program.question(program.questions[0], True)
else:
    start = False
if (start):
    auto_mode = program.question(program.questions[1], False)
    success_updating = program.parcing_update()
    if (success_updating):
        if (auto_mode):
            success_ending = program.parcing_auto()
        else:
            success_ending = program.parcing_manually()
        if (success_ending):
            success_ending = program.update_current_team_of_players()
    else:
        success_ending = False
else:
    success_ending = True
if (success_ending):
    print('Bye.')
else:
    print('Parser terminated with error.')
