from bs4 import BeautifulSoup
import requests
from fake_useragent import UserAgent
import time
from datetime import datetime
import os
import shutil
import sqlite3
from datetime import date
from datetime import timedelta
import random
import socket
import ssl

class Program():
    """Main class"""
    """Основной класс"""
    user_agent = UserAgent().chrome
    count_retries = 3
    source_urls = ('https://www.hltv.org', '/matches', '/stats/players', '/team', '?startDate=', '&endDate=')
    questions = ('Start parcer? (Y/n): ',
    'Want to start? (Y/n): ',
    'Want to continue? (Y/n): ',
    'Want to recreate the database (if yes, the old database will saved as hltv_compact_old.db)? (Y/n): ',
    'Got error while downloading match. Do you want continue? (Y/n): ')

    def __init__(self):
        self.DB = None
        self.DB_filename = None
        self.auto_mode = None
        self.repeat_mode = None
        self.log_add_mode = None
        self.competitive_maps = [True, True, True, True, True, True, True, True, True, True, True] # Cache, Cobblestone, Dust2, Inferno, Mirage, Nuke, Overpass, Season, Train, Tuscan, Vertigo
        self.__settings_titles = ('cache=', 'cobblestone=', 'dust2=', 'inferno=', 'mirage=', 'nuke=', 'overpass=', 'season=', 'train=', 'tuscan=', 'vertigo=', 'filename=', 'auto_mode=', 'repeat_mode=', 'log_add_mode=', 'download_count_retries=')
        self.__soup = None # relocate to new class
        self.__urls_matches_soup = [] # relocate to new class
        self.__titles_matches_soup = [] # relocate to new class
        self.__match_tournaments_soup = [] # relocate to new class
        self.__match_dates_soup = [] # relocate to new class
        self.__team_titles_for_update = [] # relocate to new class
        self.__urls_teams = [] # relocate to new class
        self.__urls_teams_stat = [] # relocate to new class
        self.__urls_players_stats = [] # relocate to new class
        self.__nicknames = [] # relocate to new class

    def download_html(self, url):
        for i in range(Program.count_retries):
            status = 0
            try:
                time.sleep(random.uniform(1, 2))
                req = requests.get(url, headers={'User-Agent': Program.user_agent}, timeout=5)
                if (req.status_code == 200):
                    return BeautifulSoup(req.text, 'html.parser')
                else:
                    self.log_and_print('Error {} while uploading {} (HTML-error).'.format(str(req.status_code), url))
                    if req.status_code == 503:
                        Program.user_agent = UserAgent().chrome
                    status = req.status_code
            except requests.Timeout as e:
                self.log_and_print('Error: timed out. Stopping parcing this page...')
                self.log_and_print(str(e))
                status = 408
            except socket.timeout as e:
                self.log_and_print('Error: timed out. Stopping parcing this page...')
                self.log_and_print(str(e))
                status = 408
            except Exception as e:
                self.log_and_print("Unknown error while downloading HTML: {}.".format(str(e)))
                status = e
            if (i != Program.count_retries - 1):
                self.log_and_print("Attempt to re-download HTML (retries {} remain).".format(Program.count_retries - i - 1))
        return status

    def get_id_from_url(self, url):
        """Getting an ID from a URL."""
        """Получение ID из URL."""
        if Program.source_urls[0] in url:
            parts = url.replace(Program.source_urls[0] + '/', '').split('/')
        elif url[0] == '/':
            parts = url[1:].split('/')
        else:
            parts = url.split('/')
        for i in parts:
            if i.isdigit():
                return int(i)
        self.log_and_print('Error: ID not founded in URL {}.'.format(url))
        return None

    def question(self, question_message, default_answer=True):
        """Method for asking questions to the user."""
        """Метод для задавания вопросов пользователю."""
        while(True):
            answer = input(question_message).lower()
            if answer == 'y':
                return True
            elif answer == 'n':
                return False
            elif answer == '':
                return default_answer
            else:
                self.log_and_print('Wrong answer. Try again.')

    def parcing_auto(self): # relocate to new class
        """Method for automatic parsing mode"""
        """Метод для автоматического режима парсинга"""
        for i in range(len(self.__urls_matches_soup)):
            match = Match()
            match_code_downloaded = match.download_data(self.__urls_matches_soup[i], self.__titles_matches_soup[i], self.__match_dates_soup[i], self.__match_tournaments_soup[i])
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
                match_titles = match.get_teams_titles()
                if (not match_titles):
                    return False
                match_nicknames = match.get_nicknames()
                if (not match_nicknames):
                    return False
                update_stat = self.__download_stats_all(urls_teams, urls_teams_stats, players_urls, match_data, match_titles, match_nicknames)
                if (not update_stat):
                    return False
                elif (update_stat == 5136):
                    self.log_and_print('Skipping...')
                    continue
            elif (match_code_downloaded == 5136):
                self.log_and_print('Skipping...')
                continue
            else:
                ignore_error = self.question(Program.questions[4], True)
                if (ignore_error):
                    continue
                else:
                    self.log_and_print('Stopping parcer...')
                    return False
        return True

    def parcing_manually(self): # merge with parcing_auto
        """Method for manual parsing mode"""
        """Метод для ручного режима парсинга"""
        stop = self.question(Program.questions[1], True)
        i = 0
        while (stop):
            match = Match()
            match_code_downloaded = match.download_data(self.__urls_matches_soup[i], self.__titles_matches_soup[i], self.__match_dates_soup[i], self.__match_tournaments_soup[i])
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
                match_titles = match.get_teams_titles()
                if (not match_titles):
                    return False
                match_nicknames = match.get_nicknames()
                if (not match_nicknames):
                    return False
                update_stat = self.__download_stats_all(urls_teams, urls_teams_stats, players_urls, match_data, match_titles, match_nicknames)
                if (not update_stat):
                    return False
                elif (update_stat == 5136):
                    i += 1
                    if (i < len(self.__urls_matches_soup)):
                        stop = self.question(Program.questions[2], True)
                    else:
                        stop = False
                    continue
            elif (match_code_downloaded == 5136):
                self.log_and_print('Skipping...')
                i += 1
                if (i < len(self.__urls_matches_soup)):
                    stop = self.question(Program.questions[2], True)
                else:
                    stop = False
                continue
            else:
                ignore_error = self.question(Program.questions[4], True)
                if (ignore_error):
                    continue
                else:
                    self.log_and_print('Stopping parcer...')
                    return False
            i += 1
            if (i < len(self.__urls_matches_soup)):
                stop = self.question(Program.questions[2], True)
            else:
                stop = False
        return True


    def parcing_update(self): # relocate to new class (and rework 'cause it's too big)
        """Method to update data on added upcoming matches"""
        """Метод для обновления данных о добавленных предстоящих матчах"""
        self.log_and_print('Preparing list of matches...')
        self.__soup = self.download_html('https://www.hltv.org/matches')
        if (type(self.__soup) == int):
            return False
        info_matches_downloaded = self.__soup_get_info_matches()
        if (not info_matches_downloaded):
            return False
        urls_matches_DB = self.DB.get_urls_upcomig_matches()
        if (not urls_matches_DB):
            self.log_and_print('Warning: list of URLs matches in DB is empty.')
            return True
        else:
            urls_prepared = self.__soup_prepare_urls(urls_matches_DB)
            if (not urls_prepared):
                return False
            urls_matches_DB = self.DB.get_urls_upcomig_matches()
            teams_titles = self.DB.get_titles_upcomig_matches()
            matches_titles = tuple([teams_titles[i][0] + ' vs ' + teams_titles[i][1] for i in range(len(teams_titles))])
            date_matches = self.DB.get_dates_upcomig_matches()
            tournaments_matches = self.DB.get_tournaments_upcoming_matches()
            self.log_and_print('Updating info about exist matches...')
            for i in range(len(urls_matches_DB)):
                match = Match()
                match_code_downloaded = match.download_data(urls_matches_DB[i], matches_titles[i], date_matches[i], tournaments_matches[i])
                if (match_code_downloaded == 200):
                    match_data = match.get_data()
                elif (match_code_downloaded == 5136):
                    self.log_and_print('Skipping...')
                    continue
                elif (match_code_downloaded == 4313):
                    match_data = match.get_data()
                    id_match = match_data[4313]
                    self.log_and_print('Deleting...')
                    self.DB.delete_data('matches_upcoming', id_match)
                else:
                    ignore_error = self.question(Program.questions[4], True)
                    if (ignore_error):
                        continue
                    else:
                        self.log_and_print('Stopping parcer...')
                        return False
                if (type(match_data) == tuple):
                    if (len(match_data) == 8):
                        update = self.DB.update_data(match_data)
                        if (not update):
                            return False
                    elif (len(match_data) == 10):
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
                        teams_titles_for_update = match.get_teams_titles()
                        if (teams_titles_for_update):
                            self.__team_titles_for_update.append(teams_titles_for_update)
                        else:
                            return False
                        players_nicknames = match.get_nicknames()
                        if (players_nicknames):
                            self.__nicknames.append(players_nicknames)
                        else:
                            return False
                    else:
                        self.log_and_print('Error while getting match data: wrong data len. Parcer will stopped...')
                        return False
                elif (type(match_data) == int):
                    self.log_and_print('This match not updated. Probably, it should delete.')
            self.__urls_teams = tuple(self.__urls_teams)
            self.__urls_teams_stat = tuple(self.__urls_teams_stat)
            self.__urls_players_stats = tuple(self.__urls_players_stats)
            self.__team_titles_for_update = tuple(self.__team_titles_for_update)
            if (self.__urls_teams) and (self.__urls_teams_stat) and (self.__urls_players_stats):
                self.log_and_print('Parcer updating teams and players stats from completed matches...')
                for i in range(len(self.__urls_teams)):
                    update_stat = self.__download_stats_all(self.__urls_teams[i], self.__urls_teams_stat[i], self.__urls_players_stats[i], None, self.__team_titles_for_update[i], self.__nicknames[i])
                    if (not update_stat):
                        return False
                    elif (update_stat == 5136):
                        continue
            self.log_and_print('Parcer ready to collecting new matches.')
            return True

    def recreate_DB(self): # relocate to Database class
        """If DB is damaged, you must call this method to create a new one and save the old one."""
        """В случае если БД повреждена, необходимо вызвать этот метод для создания новой и сохранения старой."""
        self.log_and_print('Disconnecting database...')
        self.DB.disconnect()
        self.log_and_print('Renaming...')
        os.rename(self.DB_filename, 'old_' + self.DB_filename)
        self.DB.connect()
        DB_ready = DB.check()
        if (DB_ready):
            self.log_and_print('Database recreated.')
            return True
        else:
            self.log_and_print('Database recreate failed (unknown error).')
            return False

    def import_settings(self): # must not be inherited to other classes
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
            end_point = file_data.find("\n", start_point)
            if (end_point == -1):
                print("Error while reading settings.cfg: end of line not found while reading '{}'.".format(self.__settings_titles[i]))
                return False
            field_value = file_data[start_point:end_point]
            if (field_value):
                if (i == 11):
                    self.DB_filename = field_value
                    self.DB = Database(field_value)
                elif (i == 12):
                    self.auto_mode = self.str_to_bool(field_value)
                    if (self.auto_mode == None):
                        print('Error while reading settings.cfg: auto_mode value cannot be readen.')
                        return False
                elif (i == 13):
                    if (field_value.isdigit()):
                        self.repeat_mode = int(field_value)
                    else:
                        print('Error while reading settings.cfg: repeat_mode value not a integer.')
                        return False
                elif (i == 14):
                    self.log_add_mode = self.str_to_bool(field_value)
                    if (self.log_add_mode == None):
                        print('Error while reading settings.cfg: log_add_mode value cannot be readen.')
                        return False
                    self.__use_log()
                elif (i == 15):
                    if (field_value.isdigit()):
                        if (int(field_value) <= 20):
                            Program.count_retries = int(field_value)
                        else:
                            Program.count_retries = 20
                            print('Not critical error while reading settings.cfg: download_count_retries more than 20. Count set to 20.')
                    else:
                        print('Error while reading settings.cfg: download_count_retries value not a integer.')
                        return False
                else:
                    self.competitive_maps[i] = self.str_to_bool(field_value)
                    if (self.competitive_maps[i] == None):
                        print('Error while reading settings.cfg: {} value cannot be readen.'.format(self.__settings_titles[i]))
                        return False
            else:
                print('Error while reading settings.cfg: {} value cannot be readen.'.format(self.__settings_titles[i]))
                return False
        return True

    def __soup_get_info_matches(self): # relocate to new class
        """Parsing URLs to upcoming matches."""
        """Парсинг URL на предстоящие матчи."""
        block_upcomig_matches = self.__soup.find(class_='upcomingMatchesWrapper')
        if (not block_upcomig_matches):
            self.log_and_print('Error while searching block "upcomingMatchesWrapper". Parcer will stopped...')
            return False
        all_upcoming_matches = block_upcomig_matches.find_all('a', class_='match a-reset')
        if (not all_upcoming_matches):
            self.log_and_print('Error while searching URLs on upcoming matches (there are not upcoming matches?). Parcer will stopped...')
            return False
        all_dates = block_upcomig_matches.find_all('div', class_='matchTime')
        for i in range(len(all_upcoming_matches)):
            teams = all_upcoming_matches[i].find('div', class_='matchTeams text-ellipsis')
            if (teams):
                if (len(teams.find_all('div', class_='matchTeamLogoContainer')) == 2):
                    self.__urls_matches_soup.append(Program.source_urls[0] + all_upcoming_matches[i]['href'])
                    teams_titles = teams.find_all('div', class_='matchTeamName text-ellipsis')
                    self.__titles_matches_soup.append(teams_titles[0].text + ' vs ' + teams_titles[1].text)
                    self.__match_tournaments_soup.append(all_upcoming_matches[i].find('div', class_='matchEventName').text)
                    self.__match_dates_soup.append(datetime.fromtimestamp(float(all_dates[i]['data-unix'])/1000).isoformat(' ') + '.000')
                else:
                    continue
            else:
                continue
        return True

    def __soup_prepare_urls(self, urls_matches_DB): # relocate to new class (and rename to __soup_clear_urls_exist_matches or something like that)
        """Changing the URLs in DB (with the same ID) and return the URLs of upcoming matches that are not in the DB."""
        """Изменение URL в БД (с одинаковыми ID) и вывод URL предстоящих матчей, которых нет в БД."""
        IDs_matches_soup = [int(self.get_id_from_url(self.__urls_matches_soup[i])) for i in range(len(self.__urls_matches_soup))]
        if (IDs_matches_soup.count(0) != 0):
            self.log_and_print('Error while getting IDs matches from URLs on upcoming matches (getted ID = 0). Parcer will stopped...')
            return False
        IDs_matches_DB = self.DB.get_ids_upcoming_matches()
        if (not IDs_matches_DB):
            self.log_and_print('Error while getting IDs matches from DB. Parcer will stopped...')
            return False
        for i in range(len(IDs_matches_DB)):
            if (IDs_matches_soup.count(IDs_matches_DB[i]) >= 1):
                if (IDs_matches_soup.count(IDs_matches_DB[i]) > 1):
                    self.log_and_print('Warning: probably, URL corrupted (all_upcoming_matches contains the same matches)')
                for j in range(IDs_matches_soup.count(IDs_matches_DB[i])):
                    index_ID_match_DB = IDs_matches_soup.index(IDs_matches_DB[i])
                    if (self.__urls_matches_soup[index_ID_match_DB] != urls_matches_DB[i]):
                        self.log_and_print('Changing URL "{}" to "{}"'.format(urls_matches_DB[i], self.__urls_matches_soup[index_ID_match_DB]))
                        updated_url = self.DB.change_upcoming_match_url(IDs_matches_soup[index_ID_match_DB], self.__urls_matches_soup[index_ID_match_DB])
                        if (not updated_url):
                            return False
                    IDs_matches_soup.pop(index_ID_match_DB)
                    self.__urls_matches_soup.pop(index_ID_match_DB)
                    self.__titles_matches_soup.pop(index_ID_match_DB)
                    self.__match_tournaments_soup.pop(index_ID_match_DB)
                    self.__match_dates_soup.pop(index_ID_match_DB)
        self.__urls_matches_soup = tuple(self.__urls_matches_soup)
        self.__titles_matches_soup = tuple(self.__titles_matches_soup)
        self.__match_tournaments_soup = tuple(self.__match_tournaments_soup)
        self.__match_dates_soup = tuple(self.__match_dates_soup)
        return True

    def __download_player_current_team(self, url): # relocate to new class
        """Method for the stage of checking whether players belong to the team (after downloading all matches)."""
        """Метод для этапа проверки принадлежности игроков к команде (после загрузки всех матчей)."""
        self.log_and_print('Uploading player data: step 1...')
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
                self.log_and_print('Error: cannot get current team. Skipping...')
                return None

    def __download_stats_all(self, urls_teams, urls_teams_stats, urls_players, match_data, team_titles, nicknames): # relocate to new class (and remove part with writing data into database)
        """Getting statistics of teams and players and write into DB."""
        """Получение статистики команд и игроков и запись их в БД."""
        teams = (Team(self.competitive_maps), Team(self.competitive_maps))
        teams_data = [[], []]
        players_data = [[], []]
        for i in range(len(teams)):
            success_download = teams[i].download_data(urls_teams[i], urls_teams_stats[i], team_titles[i])
            if (success_download == 200):
                teams_data[i] = teams[i].get_data()
                if (teams_data[i]):
                    self.log_and_print(str(teams_data[i])) # For debug
                    self.log_and_print(str(len(teams_data[i]))) # For debug
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
                success_download = players[i][j].download_data(urls_players[i][j], nicknames[i][j])
                if (success_download == 200):
                    players_data[i].append(players[i][j].get_data())
                    if (players_data[i][j]):
                        self.log_and_print(str(players_data[i][j])) # For debug
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

    def __write_data_in_DB(self, match, teams, players): # relocate to new class (or just remove that)
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

    def backup_DB(self): # relocate to Database class
        if (os.path.exists('backup_db')):
            if (os.path.isfile(self.DB_filename)):
                shutil.copy(self.DB_filename, 'backup_db')
            else:
                self.log_and_print("Error while backuping DB: file DB not found.")
                return False
        else:
            os.mkdir('backup_db')
            if (os.path.isfile(self.DB_filename)):
                shutil.copy(self.DB_filename, 'backup_db')
            else:
                self.log_and_print("Error while backuping DB: file DB not found.")
                return False
        self.log_and_print('Database backuped successfully.')
        return True

    def update_current_team_of_players(self): # relocate to new class
        """Update information about the player's current team."""
        """Обновление информации о текущей команде игрока."""
        self.log_and_print('Parcer updating current teams for players...')
        teams = self.DB.get_teams_titles()
        for i in range(len(teams)):
            players = self.DB.get_players_of_current_team(teams[i])
            if (len(players) > 5):
                for j in range(len(players)):
                    player = Player()
                    current_team = player.download_current_team(players[j][2], players[j][1])
                    if (current_team):
                        if (current_team != teams[i]):
                            self.log_and_print('Current team is "{}". Team in database is "{}". Changing...'.format(current_team, teams[i]))
                            success_update = self.DB.update_current_team(players[j][0], current_team)
                            if (not success_update):
                                return False
                    else:
                        return False
        return True

    def log_and_print(self, input_string):
        """Print text and write in log file."""
        """Вывод текста и запись его в лог файл."""
        if (type(input_string) == str):
            print(input_string)
            log_file = open('parcer.log', 'a', encoding='utf-8')
            log_file.write('{}\t\t{}\n'.format(datetime.now().isoformat(' '), input_string))
            log_file.close()
        else:
            print('Log and print error: input value must be str, getted {}.'.format(type(input_string)))

    def str_to_bool(self, value):
        if (type(value) == str):
            if (value == 'True'):
                return True
            elif (value == 'False'):
                return False
            else:
                self.log_and_print('Error while convert string to bool: value not a True or False (getted {}).'.format(value))
                return None
        else:
            self.log_and_print('Error while convert string to bool: value not a string (getted {}).'.format(type(value)))
            return None

    def __use_log(self): # need try except
        types_open_log = {True: 'a', False: 'w'}
        log_file = open('parcer.log', types_open_log[os.path.isfile('parcer.log') and self.log_add_mode], encoding='utf-8')
        log_file.write('-------------------------------------------------------------------------------------------------------------------------------\n')
        log_file.write('Start datetime: {}\n'.format(datetime.now().isoformat(' ')))
        log_file.close()

    def clear_temp_data(self): # relocate to new class
        self.__soup = None
        self.__urls_matches_soup = None
        self.__titles_matches_soup = None
        self.__match_tournaments_soup = None
        self.__match_dates_soup = None
        self.__team_titles_for_update = []
        self.__urls_teams = []
        self.__urls_teams_stat = []
        self.__urls_players_stats = []

class Database(Program):

    def __init__(self, db_name):
        self.__conn = sqlite3.connect(db_name)
        self.__cursor = self.__conn.cursor()
        self.__tables_tuple = ('matches_upcoming', 'matches_completed', 'players', 'teams', 'DB_version')
        self.__columns_tables = (
        ('ID', 'Team_1', 'Team_2', 'Date_match', 'Tournament', 'Format_match', 'Maps', 'URL'),
        ('ID', 'Team_1', 'Team_2', 'Date_match', 'Tournament', 'Format_match', 'Maps', 'Result_full', 'Result_maps', 'URL'),
        ('ID', 'Player', 'Current_Team', 'Kills', 'Deaths', 'Kill_per_Death', 'Kill__per_Round', 'Rounds_with_kills', 'Kill_Death_difference', 'Total_opening_kills', 'Total_opening_deaths', 'Opening_kill_ratio', 'Opening_kill_rating', 'Team_win_percent_after_first_kill', 'First_kill_in_won_rounds', 'Zero_kill_rounds', 'One_kill_rounds', 'Double_kill_rounds', 'Triple_kill_rounds', 'Quadro_kill_rounds', 'Penta_kill_rounds', 'Rifle_kills', 'Sniper_kills', 'SMG_kills', 'Pistol_kills', 'Grenade', 'Other', 'Rating_2_0', 'URL'),
        ('ID', 'Team', 'Rating', 'Cache_Times_played', 'Cache_Wins', 'Cache_Draws', 'Cache_Losses', 'Cache_Total_rounds_played', 'Cache_Rounds_won', 'Cache_Win_percent', 'Cache_Pistol_rounds', 'Cache_Pistol_rounds_won', 'Cache_Pistol_round_win_percent', 'Cache_CT_round_win_percent', 'Cache_T_round_win_percent', 'Cobblestone_Times_played', 'Cobblestone_Wins', 'Cobblestone_Draws', 'Cobblestone_Losses', 'Cobblestone_Total_rounds_played', 'Cobblestone_Rounds_won', 'Cobblestone_Win_percent', 'Cobblestone_Pistol_rounds', 'Cobblestone_Pistol_rounds_won', 'Cobblestone_Pistol_round_win_percent', 'Cobblestone_CT_round_win_percent', 'Cobblestone_T_round_win_percent', 'Dust_2_Times_played', 'Dust_2_Wins', 'Dust_2_Draws', 'Dust_2_Losses', 'Dust_2_Total_rounds_played', 'Dust_2_Rounds_won', 'Dust_2_Win_percent', 'Dust_2_Pistol_rounds', 'Dust_2_Pistol_rounds_won', 'Dust_2_Pistol_round_win_percent', 'Dust_2_CT_round_win_percent', 'Dust_2_T_round_win_percent', 'Inferno_Times_played', 'Inferno_Wins', 'Inferno_Draws', 'Inferno_Losses', 'Inferno_Total_rounds_played', 'Inferno_Rounds_won', 'Inferno_Win_percent', 'Inferno_Pistol_rounds', 'Inferno_Pistol_rounds_won', 'Inferno_Pistol_round_win_percent', 'Inferno_CT_round_win_percent', 'Inferno_T_round_win_percent', 'Mirage_Times_played', 'Mirage_Wins', 'Mirage_Draws', 'Mirage_Losses', 'Mirage_Total_rounds_played', 'Mirage_Rounds_won', 'Mirage_Win_percent', 'Mirage_Pistol_rounds', 'Mirage_Pistol_rounds_won', 'Mirage_Pistol_round_win_percent', 'Mirage_CT_round_win_percent', 'Mirage_T_round_win_percent', 'Nuke_Times_played', 'Nuke_Wins', 'Nuke_Draws', 'Nuke_Losses', 'Nuke_Total_rounds_played', 'Nuke_Rounds_won', 'Nuke_Win_percent', 'Nuke_Pistol_rounds', 'Nuke_Pistol_rounds_won', 'Nuke_Pistol_round_win_percent', 'Nuke_CT_round_win_percent', 'Nuke_T_round_win_percent', 'Overpass_Times_played', 'Overpass_Wins', 'Overpass_Draws', 'Overpass_Losses', 'Overpass_Total_rounds_played', 'Overpass_Rounds_won', 'Overpass_Win_percent', 'Overpass_Pistol_rounds', 'Overpass_Pistol_rounds_won', 'Overpass_Pistol_round_win_percent', 'Overpass_CT_round_win_percent', 'Overpass_T_round_win_percent', 'Season_Times_played', 'Season_Wins', 'Season_Draws', 'Season_Losses', 'Season_Total_rounds_played', 'Season_Rounds_won', 'Season_Win_percent', 'Season_Pistol_rounds', 'Season_Pistol_rounds_won', 'Season_Pistol_round_win_percent', 'Season_CT_round_win_percent', 'Season_T_round_win_percent', 'Train_Times_played', 'Train_Wins', 'Train_Draws', 'Train_Losses', 'Train_Total_rounds_played', 'Train_Rounds_won', 'Train_Win_percent', 'Train_Pistol_rounds', 'Train_Pistol_rounds_won', 'Train_Pistol_round_win_percent', 'Train_CT_round_win_percent', 'Train_T_round_win_percent', 'Tuscan_Times_played', 'Tuscan_Wins', 'Tuscan_Draws', 'Tuscan_Losses', 'Tuscan_Total_rounds_played', 'Tuscan_Rounds_won', 'Tuscan_Win_percent', 'Tuscan_Pistol_rounds', 'Tuscan_Pistol_rounds_won', 'Tuscan_Pistol_round_win_percent', 'Tuscan_CT_round_win_percent', 'Tuscan_T_round_win_percent', 'Vertigo_Times_played', 'Vertigo_Wins', 'Vertigo_Draws', 'Vertigo_Losses', 'Vertigo_Total_rounds_played', 'Vertigo_Rounds_won', 'Vertigo_Win_percent', 'Vertigo_Pistol_rounds', 'Vertigo_Pistol_rounds_won', 'Vertigo_Pistol_round_win_percent', 'Vertigo_CT_round_win_percent', 'Vertigo_T_round_win_percent', 'URL'),
        ('Build',))
        self.__new_columns_tables = ('Tournament', 'URL', 'Cache_Times_played', 'Cache_Wins', 'Cache_Draws', 'Cache_Losses', 'Cache_Total_rounds_played', 'Cache_Rounds_won', 'Cache_Win_percent', 'Cache_Pistol_rounds', 'Cache_Pistol_rounds_won', 'Cache_Pistol_round_win_percent', 'Cache_CT_round_win_percent', 'Cache_T_round_win_percent', 'Cobblestone_Times_played', 'Cobblestone_Wins', 'Cobblestone_Draws', 'Cobblestone_Losses', 'Cobblestone_Total_rounds_played', 'Cobblestone_Rounds_won', 'Cobblestone_Win_percent', 'Cobblestone_Pistol_rounds', 'Cobblestone_Pistol_rounds_won', 'Cobblestone_Pistol_round_win_percent', 'Cobblestone_CT_round_win_percent', 'Cobblestone_T_round_win_percent', 'Dust_2_CT_round_win_percent', 'Dust_2_T_round_win_percent', 'Inferno_CT_round_win_percent', 'Inferno_T_round_win_percent', 'Mirage_CT_round_win_percent', 'Mirage_T_round_win_percent', 'Nuke_CT_round_win_percent', 'Nuke_T_round_win_percent', 'Overpass_CT_round_win_percent', 'Overpass_T_round_win_percent', 'Season_Times_played', 'Season_Wins', 'Season_Draws', 'Season_Losses', 'Season_Total_rounds_played', 'Season_Rounds_won', 'Season_Win_percent', 'Season_Pistol_rounds', 'Season_Pistol_rounds_won', 'Season_Pistol_round_win_percent', 'Season_CT_round_win_percent', 'Season_T_round_win_percent', 'Train_CT_round_win_percent', 'Train_T_round_win_percent', 'Tuscan_Times_played', 'Tuscan_Wins', 'Tuscan_Draws', 'Tuscan_Losses', 'Tuscan_Total_rounds_played', 'Tuscan_Rounds_won', 'Tuscan_Win_percent', 'Tuscan_Pistol_rounds', 'Tuscan_Pistol_rounds_won', 'Tuscan_Pistol_round_win_percent', 'Tuscan_CT_round_win_percent', 'Tuscan_T_round_win_percent', 'Vertigo_CT_round_win_percent', 'Vertigo_T_round_win_percent')
        self.__tables_db = {8: 'matches_upcoming', 10: 'matches_completed', 29: 'players', 136: 'teams'}
        self.__key_words = {8: 'match', 10: 'match', 29: 'player', 136: 'team'}
        self.__create_tables_commands = (
        """CREATE TABLE matches_upcoming({} int, {} text, {} text, {} text, {} text, {} int, {} text, {} text)""".format(*self.__columns_tables[0]),
        """CREATE TABLE matches_completed({} int, {} text, {} text, {} text, {} text, {} int, {} text, {} text, {} text, {} text)""".format(*self.__columns_tables[1]),
        """CREATE TABLE players({} int, {} text, {} text, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} text)""".format(*self.__columns_tables[2]),
        """CREATE TABLE teams({} int, {} text, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} int, {} text)""".format(*self.__columns_tables[3]),
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
            columns_exist = self.__check_columns_tables(5)
            if (columns_exist):
                DB_version = self.get_DB_build()
                if (DB_version == 4):
                    self.log_and_print('Database build 4.')
                    self.log_and_print('Database is ready.')
                    return True
                elif (DB_version == 3):
                    self.log_and_print('Database is outdated (build 3)! Updating...')
                    success_update = self.__update_DB_from_3_build()
                    if (success_update == False):
                        return False
                    elif (success_update == 'Cancelled'): # it looks very stupid
                        return 'Update cancelled.'
                    else:
                        self.log_and_print('Success updated.')
                        return True
                elif (DB_version == 2):
                    self.log_and_print('Database is outdated (build 2)! Updating...')
                    success_update = self.__update_DB_from_2_build()
                    if (success_update == False):
                        return False
                    else:
                        success_update = self.__update_DB_from_3_build()
                        if (success_update == False):
                            return False
                        elif (success_update == 'Cancelled'): # it looks very stupid
                            return 'Update cancelled.'
                        else:
                            self.log_and_print('Success updated.')
                            return True
                elif (DB_version == 1):
                    self.log_and_print('Wrong value of version database detected (when database was build 1 it has not table DB_version)! Parcer cannot use this database.')
                    return False
                elif (DB_version > 3):
                    self.log_and_print('This program using the database build 3, but build {} detected! Parcer cannot use this database.'.format(str(DB_version)))
                    return False
                else:
                    self.log_and_print('Wrong value of version database detected! Parcer cannot use this database.')
                    return False
            else:
                self.log_and_print('DB Error: some columns not exist.')
                return False
        elif (check_tables == [True, True, True, True, False]):
            """If the database does not have a table with the version of the database, it will be created, and the database is updated to build 2. But before that the columns in the tables will be checked"""
            """Если БД не имеет таблицы с версией БД, то она будет создана, а БД обновлена до билда 2. Но перед этим будут проверены колонки в таблицах"""
            self.log_and_print('Database is outdated (legacy)! Updating...')
            columns_exist = self.__check_columns_tables(4)
            if (columns_exist):
                success_update = self.__update_DB_from_legacy()
                if (success_update):
                    self.log_and_print('Success updated to build 2.')
                    success_update = self.__update_DB_from_2_build()
                    if (success_update):
                        success_update = self.__update_DB_from_3_build()
                        if (success_update):
                            self.log_and_print('Success updated.')
                            return True
                        elif (success_update == 'Cancelled'): # it looks very stupid
                            return 'Update cancelled.'
                        else:
                            return False
                    else:
                        return False
                    return True
                else:
                    return False
            else:
                self.log_and_print('DB Error: some columns not exist.')
                return False
        elif (check_tables == [False, False, False, False, False]):
            """If the database does not have all the tables, they will be created"""
            """Если БД не имеет всех таблиц, то они будут созданы"""
            self.log_and_print('Creating database...')
            success_creating = self.__create()
            return success_creating
        else:
            self.log_and_print('Database is corrupted!')
            return False

    def write_data(self, data):
        """Writing data to the database: the size of the data tuple can only be 8, 10, 29, or 136.
        The sizes of input tuples can be changed in future versions of the parser.
        If the data is already exist in the table, it will be automatically updated."""
        """Запись данных в БД: размер кортежа data может быть только = 8, 10, 29 или 136.
        Размеры принимаемых кортежей могут быть изменены в будущих версиях парсера.
        Если данные уже существуют в таблице, они будут автоматически обновлены."""
        if ((len(data) == 8) or (len(data) == 10) or (len(data) == 29) or (len(data) == 136)):
            self.__cursor.execute("SELECT ID FROM {};".format(self.__tables_db[len(data)]))
            IDs = self.__cursor.fetchall()
            IDs_list = [IDs[i][0] for i in range(len(IDs))]
            Data_exist = IDs_list.count(int(data[0]))
            if (len(data) == 8) or (len(data) == 10):
                title = '{} vs {}'.format(data[1], data[2])
            elif (len(data) == 29) or (len(data) == 136):
                title = data[1]
            if (Data_exist):
                self.log_and_print('{} data of {} already exist. Data will be updated...'.format(self.__key_words[len(data)], title))
                self.update_data(data)
            else:
                if (len(data) == 8): # Upcoming match
                    self.__cursor.execute("INSERT INTO matches_upcoming VALUES(?, ?, ?, ?, ?, ?, ?, ?);", data)
                elif (len(data) == 10): # Completed match
                    self.__cursor.execute("INSERT INTO matches_completed VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", data)
                elif (len(data) == 29): # Player data
                    self.__cursor.execute("INSERT INTO players VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", data)
                elif (len(data) == 136): # Team data

                    self.__cursor.execute("INSERT INTO teams VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", data)
                self.__conn.commit()
                self.log_and_print('{} data of {} added into database.'.format(self.__key_words[len(data)].title(), title))
            return True
        else:
            self.log_and_print('Error: Size of "data" not a 8, 10, 29, or 136; data is not added into database.')
            return False

    def update_data(self, data): # Merge with write_data
        """Updating data in the database: the size of the data tuple can only be = 8, 10, 29, or 136.
        The sizes of accepted tuples will be changed in future versions of the parser.
        Determining the row whose data will be updated is performed by checking the ID match.
        Updating is carried out by deleting the old row and adding a new one."""
        """Обновление данных в БД: размер кортежа data может быть только = 8, 10, 29, или 136.
        Размеры принимаемых кортежей будут изменены в будущих версиях парсера.
        Определение строки, данные которой будут обновляться, осуществляется проверкой совпадения ID.
        Обновление осуществляется путём удаления старой строки и добавлением новой."""
        if ((len(data) == 8) or (len(data) == 10) or (len(data) == 29) or (len(data) == 136)):
            self.__cursor.execute("SELECT ID FROM {} WHERE ID = {};".format(self.__tables_db[len(data)], data[0]))
            founded_ID = self.__cursor.fetchall()
            if (founded_ID):
                err = self.delete_data(self.__tables_db[len(data)], founded_ID[0][0])
                if (len(data) == 8) or (len(data) == 10):
                    title = '{} vs {}'.format(data[1], data[2])
                elif (len(data) == 29) or (len(data) == 136):
                    title = data[1]
                if (err == 200):
                    if (len(data) == 8): # Upcoming match
                        self.__cursor.execute("INSERT INTO matches_upcoming VALUES(?, ?, ?, ?, ?, ?, ?, ?);", data)
                    elif (len(data) == 10): # Completed match
                        self.__cursor.execute("INSERT INTO matches_completed VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", data)
                    elif (len(data) == 29): # Player data
                        self.__cursor.execute("INSERT INTO players VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", data)
                    elif (len(data) == 136): # Team data

                        self.__cursor.execute("INSERT INTO teams VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", data)
                    self.__conn.commit()
                    self.log_and_print('{} data of {} updated.'.format(self.__key_words[len(data)].title(), title))
                    return True
                else:
                    self.log_and_print('While deleting old data getting error. Changes cancelled.')
                    return False
            else:
                self.log_and_print('Error: URL from "data" not founded; data is not updated.')
                return False
        else:
            self.log_and_print('Error: Size of "data" not a 8, 10, 29, or 136; data is not updated.')
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
                    self.log_and_print('Error: "ID" not founded; data is not deleted.')
                    return 1414
            else:
                self.log_and_print('Error: "ID" is not a number; data is not deleted.')
                return 1415
        else:
            self.log_and_print('Error: "table" not founded; data is not deleted.')
            return 6461

    def delete_all_data_from_table(self, table):
        """Deleting all rows from table."""
        """Удаление строки из таблицы."""
        if (self.__tables_tuple.count(table) == 1):
            self.__cursor.execute("DELETE FROM {};".format(table))
            self.__conn.commit()
            self.log_and_print('Data in table {} fully deleted.'.format(table))
            return 200
        else:
            self.log_and_print('Error: "table" not founded; data is not deleted.')
            return 6461

    def get_urls_upcomig_matches(self):
        """Getting the URLs of upcoming matches."""
        """Получение URL предстоящих матчей."""
        self.__cursor.execute("SELECT URL FROM matches_upcoming ORDER BY Date_match;")
        data = self.__cursor.fetchall()
        return tuple([data[i][0] for i in range(len(data))])

    def __update_DB_from_legacy(self):
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

    def __update_DB_from_2_build(self):
        """Updating DB from build 2. Support for previous versions will soon be discontinued."""
        """Обновление БД с билда 2. Поддержка предыдущих версий вскоре будет прекращена."""
        self.__cursor.execute('SELECT Build FROM DB_version;')
        DB_version = self.__cursor.fetchall()
        if (DB_version[0][0] == 3):
            self.log_and_print('Database build is 3.')
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
            self.log_and_print('Error while updating database: value of version database is corrupted (got version = "{}").'.format(DB_version))
            return False

    def __update_DB_from_3_build(self):
        """Updating DB from build 3. Support for previous versions will soon be discontinued."""
        """Обновление БД с билда 3. Поддержка предыдущих версий вскоре будет прекращена."""
        tables_names = ('teams', 'matches_upcoming', 'matches_completed')
        self.__cursor.execute('SELECT Build FROM DB_version;')
        DB_version = self.__cursor.fetchall()
        if (DB_version[0][0] == 4):
            self.log_and_print('Database build is 4.')
        elif (DB_version[0][0] == 3):
            long_update = self.question('WARNING! Upgrading to build 4 takes a very long time ({}) and requires a stable Internet connection. Continue? (Y/n): '.format(self.__calc_download_tournaments()), True)
            if (long_update):
                for i in range(len(tables_names)):
                    self.__cursor.execute('ALTER TABLE {} RENAME TO {}_old;'.format(tables_names[i], tables_names[i]))
                    if (i == 0):
                        self.__cursor.execute(self.__create_tables_commands[3])
                        self.__cursor.execute('SELECT * FROM teams_old;')
                        old_data = self.__cursor.fetchall()
                        new_data = [list(old_data[j][:13]) for j in range(len(old_data))]
                        for j in range(len(new_data)):
                            new_data[j].extend([0]*2)
                            for k in range(10):
                                new_data[j].extend(old_data[j][13+10*k:23+10*k])
                                new_data[j].extend([0]*2)
                            new_data[j].append(old_data[j][113])
                            self.__cursor.execute('INSERT INTO teams VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);', new_data[j])
                    else:
                        self.__cursor.execute(self.__create_tables_commands[i - 1])
                        self.__cursor.execute('SELECT * FROM {}_old;'.format(tables_names[i]))
                        old_data = self.__cursor.fetchall()
                        new_data = [list(old_data[j][:4]) for j in range(len(old_data))]
                        for j in range(len(new_data)):
                            new_data[j].append('NULL')
                            new_data[j].extend(old_data[j][4:])
                            if (i == 1):
                                self.__cursor.execute('INSERT INTO {} VALUES(?, ?, ?, ?, ?, ?, ?, ?);'.format(tables_names[i]), new_data[j])
                            elif (i == 2):
                                self.__cursor.execute('INSERT INTO {} VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?);'.format(tables_names[i]), new_data[j])
                    self.__cursor.execute('DROP TABLE {}_old;'.format(tables_names[i]))
                self.__cursor.execute('UPDATE DB_version SET Build = 4 WHERE Build = 3;')
                for i in range(2):
                    self.__cursor.execute('SELECT * FROM {};'.format(tables_names[i + 1]))
                    matches_info = self.__cursor.fetchall()
                    matches_IDs = tuple([matches_info[j][0] for j in range(len(matches_info))])
                    matches_urls = tuple([matches_info[j][7 + i * 2] for j in range(len(matches_info))])
                    matches_titles = tuple(['{} vs {}'.format(matches_info[j][1], matches_info[j][2]) for j in range(len(matches_info))])
                    matches_dates = tuple([matches_info[j][3] for j in range(len(matches_info))])
                    tournaments_download = self.__download_tournaments(matches_urls, matches_titles, matches_dates)
                    if (tournaments_download):
                        for j in range(len(tournaments_download)):
                            self.__cursor.execute('UPDATE {} SET Tournament = "{}" WHERE ID = {};'.format(tables_names[i + 1], tournaments_download[j], matches_IDs[j]))
                            self.__conn.commit()
                    else:
                        return False
                return True
            else:
                return 'Cancelled' # it looks very stupid
        else:
            self.log_and_print('Error while updating database: value of version database is corrupted (got version = "{}").'.format(DB_version))
            return False

    def __calc_download_tournaments(self):
        self.__cursor.execute('SELECT * FROM matches_upcoming;')
        count_upcoming_matches = len(self.__cursor.fetchall())
        self.__cursor.execute('SELECT * FROM matches_completed;')
        count_completed_matches = len(self.__cursor.fetchall())
        count_matches = (count_upcoming_matches + count_completed_matches) * 2
        if (count_matches > 60):
            minutes = count_matches // 60
            seconds = count_matches - minutes * 60
            if (minutes > 60):
                hours = minutes // 60
                minutes -= hours * 60
                time_str = '{} hours {} minutes {} seconds'.format(str(hours), str(minutes), str(seconds))
            else:
                time_str = '{} minutes {} seconds'.format(str(minutes), str(seconds))
        else:
            time_str = '{} seconds'.format(str(count_matches))
        return time_str

    def __download_tournaments(self, urls, titles, dates):
        if (type(urls) == tuple) or (type(urls) == list):
            tournaments = []
            for i in range(len(urls)):
                match = Match()
                success_download = match.download_data(urls[i], titles[i], dates[i], None)
                if (success_download == 200) or (success_download == 5136) or (success_download == 4313):
                    tournaments.append(match.get_tournament())
                else:
                    return None
            return tuple(tournaments)
        else:
            self.log_and_print('Error while downloading tournaments: wrong input array of URLs.')
            return None

    def __check_columns_tables(self, count_tables):
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
                        elif (self.__new_columns_tables.count(self.__columns_tables[i][j]) == 1) and ((DB_version == 3) or (DB_version == 2) or (DB_version == 1)):
                            back += 1
                            continue
                        self.log_and_print('Column {} from table {} not exist!'.format(self.__columns_tables[i][j], self.__tables_tuple[i]))
                        success = False
                        break
                back = 0
                if (not success):
                    break
            return success
        else:
            return False

    def __create(self):
        """Creating an empty database."""
        """Создание пустой БД."""
        try:
            for i in range(len(self.__create_tables_commands)):
                self.__cursor.execute(self.__create_tables_commands[i])
            self.__cursor.execute("INSERT INTO DB_version VALUES(4);")
            self.__conn.commit()
            return True
        except sqlite3.Error as e:
            self.log_and_print("Error while creating database: {}".format(str(e)))
            return False
        except Exception as e:
            self.log_and_print("Unknown error while creating database: {}".format(str(e)))
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
            self.log_and_print('Changed.')
            return True
        else:
            self.log_and_print('Error while updating URL in matches_upcoming: wrong input data into function(getted ID_match = "{}" and new_url = "{}")'.format(ID_match, new_url))
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
            self.log_and_print("Error while getting build version database: {}".format(str(e)))
            return False
        except Exception as e:
            self.log_and_print("Unknown error while getting build version database: {}".format(str(e)))
            return False

    def get_teams_titles(self):
        self.__cursor.execute('SELECT Team FROM teams ORDER BY Team;')
        teams = self.__cursor.fetchall()
        return tuple([teams[i][0] for i in range(len(teams))])

    def get_players_of_current_team(self, team):
        self.__cursor.execute('SELECT ID, Player, URL FROM players WHERE Current_Team = "{}" ORDER BY Current_Team;'.format(team))
        return tuple(self.__cursor.fetchall())

    def get_titles_upcomig_matches(self):
        self.__cursor.execute('SELECT Team_1, Team_2 FROM matches_upcoming ORDER BY Date_match;')
        return tuple(self.__cursor.fetchall())

    def get_dates_upcomig_matches(self):
        self.__cursor.execute('SELECT Date_match FROM matches_upcoming ORDER BY Date_match;')
        dates = self.__cursor.fetchall()
        return tuple([dates[i][0] for i in range(len(dates))])

    def get_tournaments_upcoming_matches(self):
        self.__cursor.execute('SELECT Tournament FROM matches_upcoming ORDER BY Date_match;')
        tournaments = self.__cursor.fetchall()
        return tuple([tournaments[i][0] for i in range(len(tournaments))])

    def update_current_team(self, ID, current_team):
        try:
            self.__cursor.execute('UPDATE players SET Current_Team = "{}" WHERE ID = {};'.format(current_team, str(ID)))
            self.__conn.commit()
            self.log_and_print('Changed successfully.')
            return True
        except sqlite3.Error as e:
            self.log_and_print("Error while updating current team of player: {}".format(str(e)))
            return False
        except Exception as e:
            self.log_and_print("Unknown error while updating current team of player: {}".format(str(e)))
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
        self.__tournament = None
        self.__format = None
        self.__maps = None
        self.__result_full = None
        self.__result_maps = None
        self.status = None
        self.__urls_teams = []
        self.__urls_teams_stats = []
        self.__urls_players = [[], []]
        self.__nicknames = [[], []]
        self.__IDs_players = [[], []]
        self.__score_types = ('won', 'tie', 'lost')
        self.lineup_url = ('/stats/lineup/maps?', 'minLineupMatch=3', '&startDate=')

    def download_data(self, url, match_title, match_date, match_tournament):
        """Parsing match data."""
        """Парсинг данных матча."""
        self.log_and_print('Uploading match data...')
        if (match_tournament):
            self.log_and_print('Tournament: {}'.format(match_tournament))
        self.log_and_print('Date: {}'.format(match_date))
        self.log_and_print('Match: {}'.format(match_title))
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
        event = self.__soup.find('div', class_='event text-ellipsis')
        if (event):
            self.__tournament = event.find('a').text
        else:
            self.log_and_print('Tournament of this match are still unknown.')
            return 5136
        if (not match_tournament):
            self.log_and_print('Tournament: {}'.format(self.__tournament))
        if (self.__soup.find('div', class_='time')):
            self.__date = datetime.fromtimestamp(float(self.__soup.find('div', class_='time')['data-unix'])/1000).isoformat(' ') + '.000' # Местное время
            if (self.__date != match_date):
                self.log_and_print('Date changed to {}'.format(self.__date))
        else:
            self.log_and_print('Time of this match are still unknown.')
            return 5136
        self.__teams_titles = (self.__soup_get_team_info(True, False), self.__soup_get_team_info(False, False))
        if (not (self.__teams_titles[0] and self.__teams_titles[1])):
            return 5136
        if (self.__teams_titles[0] + ' vs ' + self.__teams_titles[1] != match_title):
            teams_old = match_title.split(' vs ')
            for i in range(2):
                if (teams_old[i] != self.__teams_titles[i]):
                    self.log_and_print('Team {} changed to {}'.format(str(i + 1), self.__teams_titles[i]))
        self.__urls_teams = (self.__soup_get_team_info(True, True), self.__soup_get_team_info(False, True))
        if (not (self.__urls_teams[0] and self.__urls_teams[1])):
            return 5136
        self.__format = self.__soup_get_match_format()
        if (self.__format):
            self.log_and_print('Format: Best of ' + str(self.__format))
        else:
            return 5136
        self.__maps = self.__soup_get_maps()
        if (self.__maps):
            self.log_and_print('Maps: ' + self.__maps)
        else:
            return 5136
        IDs_and_nicknames = (self.__soup_get_nicknames_and_IDs(True), self.__soup_get_nicknames_and_IDs(False))
        if (IDs_and_nicknames[0]) and (IDs_and_nicknames[1]):
            self.__IDs_players[0] = IDs_and_nicknames[0][0]
            self.__IDs_players[1] = IDs_and_nicknames[1][0]
            self.__nicknames[0] = IDs_and_nicknames[0][1]
            self.__nicknames[1] = IDs_and_nicknames[1][1]
        else:
            return 5136
        match_status = self.__soup_get_match_status()
        if (match_status == 10001) or (match_status == 10002):
            if (match_status == 10001):
                self.__result_maps = self.__soup_get_result_maps()
                if (not self.__result_maps):
                    return 5136
                self.__result_full = self.__soup_get_result_full()
                if (not self.__result_full):
                    return 5136
            self.__urls_teams_stats = (self.__soup_get_url_team_stat(True, match_status), self.__soup_get_url_team_stat(False, match_status))
            if (not self.__urls_teams_stats[0]) or (not self.__urls_teams_stats[1]):
                return 5136
            self.__urls_players = (self.__soup_get_urls_team_stats_players(True, match_status), self.__soup_get_urls_team_stats_players(False, match_status))
            if (not self.__urls_players[0]) or (not self.__urls_players[1]):
                return 5136
        elif (match_status == 4313):
            self.status = 4313
            return 4313
        elif (match_status == 5136):
            return 5136
        self.status = 200
        return 200

    def get_data(self):
        """Getting match data."""
        """Получение данных матча."""
        if (self.status == 200):
            if ((self.__result_full == None) or (self.__result_maps == None)):
                data = (self.__ID, *self.__teams_titles, self.__date, self.__tournament, self.__format, self.__maps, self.__url)
            else:
                data = (self.__ID, *self.__teams_titles, self.__date, self.__tournament, self.__format, self.__maps, self.__result_full, self.__result_maps, self.__url)
            return data
        elif (self.status == 4313):
            return {self.status: self.__ID}
        else:
            self.log_and_print('Data is corrupted.')
            return self.status

    def get_urls_teams(self):
        """Getting URLs teams."""
        """Получение URL команд."""
        if (self.status == 200):
            data = tuple([*self.__urls_teams])
            return data
        else:
            self.log_and_print('Data is corrupted.')
            return None

    def get_urls_stats_teams(self):
        """Getting URLs teams stats."""
        """Получение URL статистик команд."""
        if (self.status == 200):
            data = tuple([*self.__urls_teams_stats])
            return data
        else:
            self.log_and_print('Data is corrupted.')

    def get_urls_stats_players(self, team_bool):
        """Getting URLs players stats."""
        """Получение URL статистик игроков."""
        team = {True: 0, False: 1}
        if (self.status == 200) or (self.status == 0):
            if (type(team_bool) == bool):
                data = self.__urls_players[team[team_bool]]
                return data
            else:
                self.log_and_print('Error: got variable not "bool".')
                return None
        else:
            self.log_and_print('Data is corrupted.')
            return None

    def get_teams_titles(self):
        if (self.status == 200) or (self.status == 0):
            return self.__teams_titles
        else:
            self.log_and_print('Data is corrupted.')
            return None

    def get_nicknames(self):
        if (self.status == 200) or (self.status == 0):
            return self.__nicknames
        else:
            self.log_and_print('Data is corrupted.')
            return None

    def get_tournament(self):
        if (self.status == 200) or (self.status == 0) or (self.status == 5136) or (self.status == 4313):
            return self.__tournament
        else:
            self.log_and_print('Data is corrupted.')
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
                    return Program.source_urls[0] + team.find('a')['href']
                else:
                    self.log_and_print('In this match, team {} URL are still unknown.'.format(teams_dict[team_1]))
                    return None
            else:
                return team.find(class_='teamName').text
        else:
            self.log_and_print('In this match, team {} are still unknown.'.format(teams_dict[team_1]))
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
                self.log_and_print('This match has unstandart or corrupt maps block.')
                return None
        else:
            self.log_and_print('This match has not maps block.')
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
            self.log_and_print('This match has unstandart or corrupt maps block.')
            return None

    def __soup_get_match_status(self):
        """Parsing the status of the match (not started (10002), over (10001), postponed (5136), deleted (4313))."""
        """Парсинг статуса матча (не начался (10002), завершился (10001), отложен (5136), удалён (4313))."""
        match_status = self.__soup.find('div', class_='countdown')
        if (match_status):
            if (match_status.text == 'Match over'):
                return 10001
            elif (match_status.text == 'Match deleted'):
                self.log_and_print('This match cancelled.')
                return 4313
            elif (match_status.text == 'Match postponed'):
                self.log_and_print('This match postponed.')
                return 5136
            else:
                return 10002
        else:
            self.log_and_print('This match has not div.countdown block.')
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
                self.log_and_print("This match has not results maps or there's unstandart or broken block.")
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
                    self.log_and_print("This match has not result on map %d or there's unstandart or broken block." % i)
                    return None
            return full_result_str[0:len(full_result_str)-2]
        else:
            maps = self.__soup.find_all('div', class_='mapname')
            if (maps):
                for i in range(len(maps)):
                    maps[i] = maps[i].text
            else:
                self.log_and_print("This match has not maps or broken block.")
                return None
            if (maps.count('Default') > 0):
                return 'Forfeit'
            else:
                self.log_and_print("This match has not results per map or there's unstandart or broken block.")
                return None

    def __soup_get_url_team_stat(self, team_1, match_status):
        """Parsing URL for team statistics (if team_1 = True - team 1, False - team 2). If the match is over, the URL is generated by the parser, since it is not on the page."""
        """Парсинг URL на статистику команды (если team_1 = True - команда 1, False - команда 2). Если матч окончен, URL генерируется парсером, так как на странице она отсутствует."""
        teams_dict = {True: 0, False: 1}
        if (match_status == 10002):
            teams_stats = self.__soup.find(class_='map-stats-infobox-header')
            if (teams_stats):
                urls_teams_stats = teams_stats.find_all(class_='team')
                if (urls_teams_stats):
                    return Program.source_urls[0] + urls_teams_stats[teams_dict[team_1]].find('a')['href']
                else:
                    self.log_and_print('This match has not URL for team %d stat.' % (teams_dict[team_1] + 1))
                    return None
            else:
                self.log_and_print('This match has not URLs for teams stats.')
                return None
        elif (match_status == 10001):
            url = '{}{}lineup={}&lineup={}&lineup={}&lineup={}&lineup={}&{}{}{}{}{}'.format(Program.source_urls[0], self.lineup_url[0], *self.__IDs_players[teams_dict[team_1]], self.lineup_url[1], self.lineup_url[2], date.isoformat(date.today() - timedelta(days=90)), Program.source_urls[5], date.isoformat(date.today()))
            return url
        else:
            self.log_and_print("Error while getting team stat URL: status match is incorrect.")
            return None

    def __soup_get_urls_team_stats_players(self, team_1, match_status):
        """Parsing URL for players statistics (if team_1 = True - from team 1, False - from team 2)."""
        """Парсинг URL на статистику игроков (если team_1 = True - из команды 1, False - из команды 2)."""
        teams_dict = {True: 0, False: 1}
        lineups = self.__soup.find_all('div', class_='lineup standard-box')
        if (not lineups):
            self.log_and_print("This match has not lineups.")
            return None
        players_nicknames = lineups[teams_dict[team_1]].find_all('div', class_='text-ellipsis')
        if (len(players_nicknames) < 5):
            self.log_and_print('In team %d some players still unknown.' % (teams_dict[team_1] + 1))
            return None
        if (match_status == 10002):
            players_compare = lineups[teams_dict[team_1]].find_all('div', class_='player-compare')
            if (len(players_compare) < 10):
                self.log_and_print('In team %d some players have not statistic page.' % (teams_dict[team_1] + 1))
                return None
            for i in range(int(len(players_compare)/2-1), -1, -1):
                players_compare.pop(i)
        elif (match_status == 10001):
            tr = lineups[teams_dict[team_1]].find_all('tr')
            if (tr):
                players = tr[1].find_all('div', class_='flagAlign')
                if (not players):
                    self.log_and_print("This match has not players blocks.")
                    return None
            else:
                self.log_and_print("This match has not tr blocks.")
                return None
        else:
            self.log_and_print("Error while getting players stats URLs: status match is incorrect.")
            return None
        date_today = date.isoformat(date.today())
        date_3_month_ago = date.isoformat(date.today() - timedelta(days=90))
        urls_players = []
        for i in range(5):
            nickname = players_nicknames[i].text
            if (nickname == 'TBA') or (nickname == 'TBD'):
                self.log_and_print('In team %d some players still unknown.' % (teams_dict[team_1] + 1))
                return None
            if (match_status == 10002):
                id_player = players_compare[i]['data-player-id']
            elif (match_status == 10001):
                id_player = players[i]['data-player-id']
            else:
                self.log_and_print("Error while getting players stats URLs: status match is incorrect.")
                return None
            if (id_player == '0'):
                self.log_and_print('In team %d some players has not ID.' % (teams_dict[team_1] + 1))
                return None
            urls_players.append('{}{}/{}/{}{}{}{}{}'.format(Program.source_urls[0], Program.source_urls[2], id_player, nickname, Program.source_urls[4], date_3_month_ago, Program.source_urls[5], date_today))
        return tuple(urls_players)

    def __soup_get_nicknames_and_IDs(self, team_1):
        """Parsing of nicknames."""
        """Парсинг никнеймов игроков."""
        teams_dict = {True: 0, False: 1}
        lineups = self.__soup.find_all('div', class_='lineup standard-box')
        if (lineups):
            tr = lineups[teams_dict[team_1]].find_all('tr')
            if (tr):
                players = tr[1].find_all('div', class_='flagAlign', attrs={'data-player-id': True})
                if (players):
                    if (len(players) == 5):
                        IDs_and_nicknames = [[], []]
                        for i in range(5):
                            if (players[i].text == '\nTBA\n') or (players[i].text == '\nTBD\n'):
                                self.log_and_print('This match has not player {} in team {}.'.format(str(i + 1), str(teams_dict[team_1] + 1)))
                                return None
                            else:
                                IDs_and_nicknames[0].append(players[i]['data-player-id'])
                                IDs_and_nicknames[1].append(players[i].find('div', class_='text-ellipsis').text)
                        IDs_and_nicknames[0] = tuple(IDs_and_nicknames[0])
                        IDs_and_nicknames[1] = tuple(IDs_and_nicknames[1])
                        return tuple(IDs_and_nicknames)
                    else:
                        self.log_and_print('In this match team {} have less than 5 players.'.format(str(teams_dict[team_1] + 1)))
                        return None
                else:
                    self.log_and_print('This match has not players blocks.')
                    return None
            else:
                self.log_and_print("This match has not tr blocks.")
                return None
        else:
            self.log_and_print("This match has not lineups blocks.")
            return None

class Team(Program):
    """Object team statistics."""
    """Объект статистики команды."""

    def __init__(self, competitive_maps):
        self.__soup_1 = None
        self.__soup_2 = None
        self.__url = None
        self.__ID = 0
        self.__team = None
        self.__rating = None
        self.__maps_data = (Map_stats(), Map_stats(), Map_stats(), Map_stats(), Map_stats(), Map_stats(), Map_stats(), Map_stats(), Map_stats(), Map_stats(), Map_stats())
        #                     Cache     Cobblestone     Dust 2      Inferno       Mirage        Nuke       Overpass      Season       Train        Tuscan      Vertigo
        self.status = None
        self.__active_maps = competitive_maps
        self.__maps_titles = ('Cache', 'Cobblestone', 'Dust2', 'Inferno', 'Mirage', 'Nuke', 'Overpass', 'Season', 'Train', 'Tuscan', 'Vertigo')

    def download_data(self, url_1, url_2, team_title):
        """Parsing team data."""
        """Парсинг данных команды."""
        self.log_and_print('Uploading team {} data: step 1...'.format(team_title))
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
            self.log_and_print('This team has not name block.')
            return 5136
        self.__rating = self.__soup_get_team_rating()
        if (not self.__rating):
            return 5136
        self.log_and_print('Uploading team {} data: step 2...'.format(self.__team))
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
            self.log_and_print('Team statistics download complete.')
            self.status = 200
            return 200
        elif (stats_urls == [None, None, None, None, None, None, None, None, None, None, None]):
            self.log_and_print('Not critical error while getting team stats URLs: tuple have not any URL (team not played any competitive map?).')
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
            self.log_and_print('Data is corrupted.')
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
            self.log_and_print('This team has not rating block.')
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
                    maps_urls[i] = Program.source_urls[0] + maps_urls[i]['href']
                    soup_maps_titles[i] = soup_maps_titles[i].text
                full_maps_urls = [None, None, None, None, None, None, None, None, None, None, None]
                for i in range(len(self.__active_maps)):
                    if (soup_maps_titles.count(self.__maps_titles[i]) == 1) and (self.__active_maps[i]):
                        url_index = soup_maps_titles.index(self.__maps_titles[i])
                        full_maps_urls[i] = maps_urls[url_index]
                return tuple(full_maps_urls)
            else:
                self.log_and_print('In this team, the maps statistics have not URLs.')
                return None
        else:
            self.log_and_print('In this team, the maps statistics are still unknown.')
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
        self.__CT_round_win_percent = None
        self.__T_round_win_percent = None
        self.status = None
        self.__table_rows_names = ('Times played', 'Wins / draws / losses', 'Total rounds played', 'Rounds won', 'Win percent', 'Pistol rounds', 'Pistol rounds won', 'Pistol round win percent', 'CT round win percent', 'T round win percent')

    def download_data(self, url, team_name, map_name):
        """Parsing map stat."""
        """Парсинг статистики карты."""
        if (url):
            self.log_and_print('Uploading team {} data: step 3: map {}...'.format(team_name, map_name))
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
                self.__CT_round_win_percent = data_team_map[10]
                self.__T_round_win_percent = data_team_map[11]
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
            self.__CT_round_win_percent = 0
            self.__T_round_win_percent = 0
            self.status = 200
            return 200

    def get_data(self):
        """Getting map stat data."""
        """Получение данных статистики карты."""
        if (self.status == 200):
            data = (self.__times_played, self.__wins, self.__draws, self.__losses, self.__total_rounds_played, self.__rounds_won, self.__win_percent, self.__pistol_rounds, self.__pistol_rounds_won, self.__pistol_round_win_percent, self.__CT_round_win_percent, self.__T_round_win_percent)
            return data
        else:
            self.log_and_print('Data is corrupted.')
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
            self.log_and_print('In this team, the map statistic have not some rows.')
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
        self.__table_rows_names = ('Kills', 'Deaths', 'Kill / Death', 'Kill / Round', 'Rounds with kills', 'Kill - Death differenceK - D diff.', 'Total opening kills', 'Total opening deaths', 'Opening kill ratio', 'Opening kill rating', 'Team win percent after first kill', 'First kill in won rounds', '0 kill rounds', '1 kill rounds', '2 kill rounds', '3 kill rounds', '4 kill rounds', '5 kill rounds', 'Rifle kills', 'Sniper kills', 'SMG kills', 'Pistol kills', 'Grenade', 'Other')

    def download_data(self, url_1, nickname):
        """Parsing player data."""
        """Парсинг данных игрока."""
        self.log_and_print('Uploading player {} data: step 1...'.format(nickname))
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
            self.log_and_print('This player has not some nickname.')
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
            url_2 = Program.source_urls[0] + url_2['href']
        self.log_and_print('Uploading player {} data: step 2...'.format(self.__nickname))
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
            self.log_and_print('Data is corrupted.')

    def download_current_team(self, url, nickname):
        self.log_and_print('Uploading current team of player {}...'.format(nickname))
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
                self.log_and_print('Error: cannot get current team.')
                return None

    def __soup_get_url(self, dirt_url):
        """Parsing URL of player."""
        """Парсинг URL игрока."""
        if (dirt_url.count('?') == 0):
            self.log_and_print('Error: the URL does not contain the period of statistics collection.')
            return None
        elif (dirt_url.count('?') == 1):
            return dirt_url[0:dirt_url.find('?')]
        else:
            self.log_and_print('Warning: probably URL is corrupted.')
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
                self.log_and_print('Error: the rating 2.0 is not a number.')
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
                if (rows[i].isdigit()):
                    rows[i] = int(rows[i])
                elif '.' in rows[i]:
                    rows[i] = float(rows[i])
                    if (rows[i].is_integer()):
                        rows[i] = int(rows[i])
                else:
                    rows[i] = 0
            return rows
        else:
            self.log_and_print('Error: the stats table not exist.')
            return None

"""Main executable code"""
"""Основной исполняемый код"""
# This code will relocate to new class
runned = False
program = Program()
deny_start = False
import_cfg = program.import_settings()
if (import_cfg):
    program.log_and_print('Config imported successfully.')
else:
    program.log_and_print('Parser terminated with error.')
program.log_and_print('This is a parcer for collecting statistics about teams and players on upcoming matches in CS:GO from hltv.org. Current version: 0.5.6 alpha.')
while (program.repeat_mode + 1 > 0):
    DB_ready = program.DB.check()
    if (not DB_ready):
        program.log_and_print("Got error while checking or updating database.")
        repair_DB = program.question(Program.questions[3], True)
        if (repair_DB):
            program.recreate_DB()
        else:
            deny_start = True
    elif (DB_ready == 'Update cancelled.'):
        print(DB_ready)
        break
    backup_db = program.backup_DB()
    if (backup_db):
        if (deny_start):
            start = False
        else:
            if (not runned):
                start = program.question(Program.questions[0], True)
            else:
                start = True
    else:
        start = False
    if (start):
        runned = True
        auto_mode = program.auto_mode
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
        program.log_and_print('Bye.')
    else:
        program.log_and_print('Parser terminated with error.')
    program.clear_temp_data()
    if (program.repeat_mode != 0):
        program.log_and_print('Parser has switched to sleep mode. Awakening in {}'.format(datetime.now().isoformat(' ')))
        time.sleep(86400 * program.repeat_mode)
        Program.user_agent = UserAgent().chrome
        program.log_and_print('-------------------------------------------------------------------------------------------------------------------------------\n')
        program.log_and_print('Start datetime: {}\n'.format(datetime.now().isoformat(' ')))
    else:
        program.repeat_mode -= 1
