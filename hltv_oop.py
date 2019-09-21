from bs4 import BeautifulSoup
import requests
import time
import sqlite3
import datetime

"""Глобальные переменные и функции"""

source_urls = ['https://www.hltv.org', '/matches', '/stats/players/', '?startDate=', '&endDate=']
end_prog = ''
start_bool = True
skip_confirm = False
decision_made = False
words = {False: 'continue', True: 'start'}

def upload_html(url):
    """Функция загрузки страницы"""
    try:
        req = requests.get(url)
        if (req.status_code == 200):
            soup = BeautifulSoup(req.text, 'html.parser')
            return soup
        else:
            print('Error: ' + str(req_func.status_code) + '. Stopping parcer...')
            return req_func.status_code
    except requests.Timeout as e:
        print('Error: timed out. Stopping parcer...')
        print(str(e))
        return 408

def check_float(str):
    """Функция проверки строки числом"""
    try:
        float(str)
        return True
    except ValueError:
        return False

def get_match_status(link):
    soup = upload_html(link) # https://www.hltv.org/matches/[number]/[matchName]
    if (type(soup) == int):
        print('Error ' + soup + ' while uploading ' + link + '(HTML-error).')
        return soup
    else:
        """Обработка данных с загруженной страницы"""
        match_status = soup.find('div', class_='countdown').text
        return match_status

"""Классы объектов"""

class Database():
    """Объект БД"""
#    __buffer = ''

    def __init__(self):
        """БД по умолчанию"""
        self.__conn = sqlite3.connect("hltv_compact.db")
        self.__cursor = self.__conn.cursor()
        self.__tables_tuple = ('matches_upcoming', 'matches_completed', 'players', 'teams')
        self.__tables_db = {6: 'matches_upcoming', 8: 'matches_completed', 28: 'players', 73: 'teams'}
        self.__key_words = {6: 'match', 8: 'match', 28: 'player', 73: 'team'}

    def connect_another_name(self, db):
        """БД с другим именем"""
        if (db.count('.db') == 0):
            db = db + '.db'
        self.__conn.close()
        self.__conn = sqlite3.connect(db)
        self.__cursor = self.__conn.cursor()

    def __del__(self):
        """Закрытие БД"""
        self.__conn.close()

    def create(self):
        """Создание новой БД"""
        self.__cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        list_tables = self.__cursor.fetchall()
        if (list_tables != []):
            for i in range(len(list_tables)):
                list_tables[i] = list_tables[i][0]
        list_tables = tuple(list_tables)
        """Проверка текущей БД"""
        check_tables = [False, False, False, False]
        for i in range(len(check_tables)):
            if (list_tables.count(self.__tables_tuple[i]) == 1):
                check_tables[i] = True
        """Если БД не имеет всех таблиц, то они будут созданы заново"""
        if (check_tables != [True, True, True, True]):
            print('Creating database...')
            """Если БД имеет некоторые таблицы, то они удаляются"""
            if (check_tables.count(True) != 0):
                for i in range(len(check_tables)):
                    if (check_tables[i] == True):
                        self.__cursor.execute("DROP TABLE " + self.__tables_tuple[i] + ";")
            """Создание таблиц"""
            self.__cursor.execute("""CREATE TABLE players
                              (ID int, Player text, Current_Team text,
                              Kills int, Deaths int, Kill_per_Death int, Kill__per_Round int, Rounds_with_kills int, Kill_Death_difference int,
                              Total_opening_kills int, Total_opening_deaths int, Opening_kill_ratio int, Opening_kill_rating int, Team_win_percent_after_first_kill int, First_kill_in_won_rounds int,
                              Zero_kill_rounds int, One_kill_rounds int, Double_kill_rounds int, Triple_kill_rounds int, Quadro_kill_rounds int, Penta_kill_rounds int,
                              Rifle_kills int, Sniper_kills int, SMG_kills int, Pistol_kills int, Grenade int, Other int,
                              Rating_2_0 int, Link text)
                           """)
            self.__cursor.execute("""CREATE TABLE teams
                            (ID int, Team text, Rating int,
                            Dust_2_Times_played int, Dust_2_Wins int, Dust_2_Draws int, Dust_2_Losses int, Dust_2_Total_rounds_played int, Dust_2_Rounds_won int, Dust_2_Win_percent int, Dust_2_Pistol_rounds int, Dust_2_Pistol_rounds_won int, Dust_2_Pistol_round_win_percent int,
                            Inferno_Times_played int, Inferno_Wins int, Inferno_Draws int, Inferno_Losses int, Inferno_Total_rounds_played int, Inferno_Rounds_won int, Inferno_Win_percent int, Inferno_Pistol_rounds int, Inferno_Pistol_rounds_won int, Inferno_Pistol_round_win_percent int,
                            Mirage_Times_played int, Mirage_Wins int, Mirage_Draws int, Mirage_Losses int, Mirage_Total_rounds_played int, Mirage_Rounds_won int, Mirage_Win_percent int, Mirage_Pistol_rounds int, Mirage_Pistol_rounds_won int, Mirage_Pistol_round_win_percent int,
                            Nuke_Times_played int, Nuke_Wins int, Nuke_Draws int, Nuke_Losses int, Nuke_Total_rounds_played int, Nuke_Rounds_won int, Nuke_Win_percent int, Nuke_Pistol_rounds int, Nuke_Pistol_rounds_won int, Nuke_Pistol_round_win_percent int,
                            Overpass_Times_played int, Overpass_Wins int, Overpass_Draws int, Overpass_Losses int, Overpass_Total_rounds_played int, Overpass_Rounds_won int, Overpass_Win_percent int, Overpass_Pistol_rounds int, Overpass_Pistol_rounds_won int, Overpass_Pistol_round_win_percent int,
                            Train_Times_played int, Train_Wins int, Train_Draws int, Train_Losses int, Train_Total_rounds_played int, Train_Rounds_won int, Train_Win_percent int, Train_Pistol_rounds int, Train_Pistol_rounds_won int, Train_Pistol_round_win_percent int,
                            Vertigo_Times_played int, Vertigo_Wins int, Vertigo_Draws int, Vertigo_Losses int, Vertigo_Total_rounds_played int, Vertigo_Rounds_won int, Vertigo_Win_percent int, Vertigo_Pistol_rounds int, Vertigo_Pistol_rounds_won int, Vertigo_Pistol_round_win_percent int,
                            Link text)
                        """)
            self.__cursor.execute("""CREATE TABLE matches_upcoming(ID int, Team_1 text, Team_2 text, Date_match text, Format_match int, Maps text, Link text)""")
            self.__cursor.execute("""CREATE TABLE matches_completed(ID int, Team_1 text, Team_2 text, Date_match text, Format_match int, Maps text, Result_full text, Result_maps text, Link text)""")
            self.__conn.commit()
        else:
            print('All tables already created.')

    def write_data(self, data):
        """Запись данных в БД: размер массива data может быть только = 6, 8, 28 или 73
        Если данные уже присутствуют в таблице, они будут автоматически обновлены."""
        if ((len(data) == 6) or (len(data) == 8) or (len(data) == 28) or (len(data) == 73)):
            """Проверка наличия получемых данных."""
            self.__cursor.execute("SELECT Link FROM " + self.__tables_db[len(data)] + ";")
            Links = self.__cursor.fetchall()
            Links_list = [Links[i][0] for i in range(len(Links))]
            Data_exist = Links_list.count(data[len(data)-1])
            if(Data_exist != 0):
                print('This ' + self.__key_words[len(data)] + ' already exist. Data will be updated...')
                self.update_data(data)
            else:
                """Вычисление ID"""
                self.__cursor.execute("SELECT ID FROM " + self.__tables_db[len(data)] + " ORDER BY ID DESC;")
                last = self.__cursor.fetchall()
                if (last == []):
                    last = 0
                else:
                    last = int(last[0][0]) + 1
                if (len(data) == 6):
                    self.__cursor.execute("SELECT ID FROM matches_completed ORDER BY ID DESC;")
                    last_2 = self.__cursor.fetchall()
                    if (last_2 == []):
                        last_2 = 0
                    else:
                        last_2 = int(last_2[0][0]) + 1
                    if (last_2 > last):
                        last = last_2
                last = str(last)
                """Подготовка данных для записи"""
                here_data = [last]
                here_data.extend(data)
                if (len(data) == 6):
                    """Запись предстоящего матча."""
                    self.__cursor.execute("INSERT INTO matches_upcoming VALUES(?, ?, ?, ?, ?, ?, ?);", here_data)
                elif (len(data) == 8):
                    """Запись оконченного матча."""
                    self.__cursor.execute("SELECT ID FROM matches_upcoming WHERE Link = '" + here_data[8] + "';")
                    last = self.__cursor.fetchall()
                    last = str(int(last[0][0]))
                    here_data = [last]
                    here_data.extend(data)
                    self.__cursor.execute("INSERT INTO matches_completed VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?);", here_data)
                elif (len(data) == 28):
                    """Запись статистики игрока."""
                    self.__cursor.execute("INSERT INTO players VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", here_data)
                elif (len(data) == 73):
                    """Запись статистики команды."""
                    self.__cursor.execute("INSERT INTO teams VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", here_data)
                self.__conn.commit()
        else:
            print('Error 5173.a: Size of "data" not a 6, 8, 28 or 73; data is not added into database.')

    def update_data(self, data):
        """Обновление данных в БД: размер массива data может быть только = 6, 8, 28 или 73.
        Определение записи, данные которой будут обновляться, осуществляется проверкой совпадения ссылок.
        Обновление осуществляется путём удаления старой записи и добавлением новой с сохранением id."""
        if ((len(data) == 6) or (len(data) == 8) or (len(data) == 28) or (len(data) == 73)):
            """Поиск обновляемых данных."""
            self.__cursor.execute("SELECT ID FROM " + self.__tables_db[len(data)] + " WHERE Link = '" + data[len(data)-1] + "';")
            id = self.__cursor.fetchall()
            if (id != []):
                """Подготовка данных для обновления"""
                new_data = [id[0][0]]
                new_data.extend(data)
                """Удаление старой записи"""
                err = self.delete_data(self.__tables_db[len(data)], id[0][0])
                if (err == 200):
                    if (len(data) == 6):
                        """Обновление данных о предстоящем матче."""
                        self.__cursor.execute("INSERT INTO matches_upcoming VALUES(?, ?, ?, ?, ?, ?, ?);", new_data)
                    elif (len(data) == 8):
                        """Обновление данных об оконченном матче."""
                        self.__cursor.execute("INSERT INTO matches_completed VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?);", new_data)
                    elif (len(data) == 28):
                        """Обновление статистики игрока."""
                        self.__cursor.execute("INSERT INTO players VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", new_data)
                    elif (len(data) == 73):
                        """Обновление статистики команды."""
                        self.__cursor.execute("INSERT INTO teams VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", new_data)
                    self.__conn.commit()
                else:
                    print('While deleting old data getting error. Changes cancelled.')
            else:
                print('Error 1192: link from "data" not founded; data is not updated.')
        else:
            print('Error 5173.b: Size of "data" not a 6, 8, 28 or 73; data is not updated.')

    def delete_data(self, table, id):
        """Удаление данных из БД по id."""
        """Проверка правильности ввода параметров."""
        if (self.__tables_tuple.count(table) == 1):
            if (str(id).isdigit()):
                """Поиск удаляемых данных."""
                self.__cursor.execute("SELECT * FROM " + table + " WHERE ID = '" + str(id) + "';")
                data_existing = self.__cursor.fetchall()
                if (data_existing != []):
                    self.__cursor.execute("DELETE FROM " + table + " WHERE ID = '" + str(id) + "';")
                    self.__conn.commit()
                    return 200
                else:
                    print('Error 1414: "id" not founded; data is not deleted.')
                    return 1414
            else:
                print('Error 1415: "id" is not a number; data is not deleted.')
                return 1415
        else:
            print('Error 6461: "table" not founded; data is not deleted.')
            return 6461

    def delete_table_data(self, table):
        """Удаление данных из БД. Данный метод очищает всю таблицу."""
        """Проверка правильности ввода параметров."""
        if (self.__tables_tuple.count(table) == 1):
            """Очистка таблицы"""
            self.__cursor.execute("DELETE FROM " + table + "';")
            self.__conn.commit()
            print('Data in table ' + table + ' fully deleted.')
            return 200
        else:
            print('Error 6461: "table" not founded; data is not deleted.')
            return 6461

    def get_urls_upcomig_matches(self):
        self.__cursor.execute("SELECT Link FROM matches_upcoming;")
        data = self.__cursor.fetchall()
        if (data != []):
            for i in range(len(data)):
                data[i] = data[i][0]
            data = tuple(data)
            return data
        else:
            return data

    def get_id_upcoming_match(self, link):
        self.__cursor.execute("SELECT ID FROM matches_upcoming WHERE Link = '" + link + "';")
        data = self.__cursor.fetchall()
        if (data != []):
            for i in range(len(data)):
                data[i] = data[i][0]
            data = tuple(data)
            return data
        else:
            return data

    def get_link_upcoming_match_by_team(self, team_name):
        self.__cursor.execute('SELECT Link FROM matches_upcoming WHERE Team_1 = "' + team_name + '";')
        data = self.__cursor.fetchall()
        self.__cursor.execute('SELECT Link FROM matches_upcoming WHERE Team_2 = "' + team_name + '";')
        data_2 = self.__cursor.fetchall()
        data.extend(data_2)
        if (data != []):
            for i in range(len(data)):
                data[i] = data[i][0]
            data = tuple(data)
            return data
        else:
            return data

class Map_stats():
    """Объект статистики команды на карте"""

    def __init__(self):
        """Простая инициализация"""
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
        self.__status = 0

    def upload_data(self, link):
        """Инициализация с конкретной ссылки"""
        time.sleep(1)
        soup = upload_html(link) # https://www.hltv.org/stats/teams/map/[mapNumber]/[number]/[teamName]
        if (type(soup) == int):
            print('Error ' + soup + ' while uploading ' + link + '(HTML-error).')
            self.__status = soup
        else:
            """Обработка данных с загруженной страницы"""
            table_rows_names = ('Times played', 'Wins / draws / losses', 'Total rounds played', 'Rounds won', 'Win percent', 'Pistol rounds', 'Pistol rounds won', 'Pistol round win percent')
            table = soup.find(class_='stats-rows standard-box')
            rows = table.find_all(class_='stats-row')
            stats = []
            for i in range(len(rows)):
                stats.append(rows[i].text)
                stats[i] = stats[i].replace(table_rows_names[i], '')
            stats[1] = stats[1].split(' / ')
            stats[4] = stats[4][0:len(stats[4])-1]
            stats[7] = stats[7][0:len(stats[7])-1]
            data_team_map = []
            for i in range(len(stats)):
                if (i != 1):
                    """if(stats[i] == '0.0%'): # Баг фикс. Возможно, он уже не требуется
                        stats[i] = 0
                    else:"""
                    stats[i] = float(stats[i])
                    if(stats[i].is_integer() == True):
                        stats[i] = int(stats[i])
                    data_team_map.append(stats[i])
                else:
                    for j in range(len(stats[i])):
                        stats[i][j] = int(stats[i][j])
                        data_team_map.append(stats[i][j])
            """Присвоение полученных данных свойствам объекта"""
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
            self.__status = 200

    def get_data(self):
        """Вывод свойств объекта"""
        if (self.__status == 200) or (self.__status == 0):
            data = (self.__times_played, self.__wins, self.__draws, self.__losses, self.__total_rounds_played, self.__rounds_won, self.__win_percent, self.__pistol_rounds, self.__pistol_rounds_won, self.__pistol_round_win_percent)
            return data
        else:
            print('Data is corrupted.')

class Match():

    def __init__(self):
        self.__team_1 = 'None'
        self.__team_2 = 'None'
        self.__date = 0
        self.__format = 0
        self.__maps = 'None'
        self.__result_full = 'None'
        self.__result_maps = 'None'
        self.__link = 'None'
        self.__status = 0
        self.__link_team_1 = 'None'
        self.__link_team_2 = 'None'
        self.__link_team_1_stats = 'None'
        self.__link_team_2_stats = 'None'
        self.__links_team_1_players = 'None'
        self.__links_team_2_players = 'None'

    def upload_data(self, link):
        """Инициализация с конкретной ссылки"""
        print('Uploading match data...')
        time.sleep(1)
        soup = upload_html(link) # https://www.hltv.org/matches/[number]/[matchName]
        if (type(soup) == int):
            print('Error ' + soup + ' while uploading ' + link + '(HTML-error).')
            self.__status = soup
        else:
            """Обработка данных с загруженной страницы"""
            match_status = soup.find('div', class_='countdown').text
            time_and_date_unix = soup.find('div', class_='time')['data-unix'] # Исходное время GTK +3
            time_and_date_unix = float(time_and_date_unix[0:len(time_and_date_unix)-3] + '.000')
            self.__date = datetime.datetime.fromtimestamp(time_and_date_unix)
            self.__date = self.__date.isoformat(' ') + '.000'
            print('Date: ' + self.__date)
            team_1 = soup.find('div', class_='team1-gradient')
            team_2 = soup.find('div', class_='team2-gradient')
            if (team_1 == None) or (team_2 == None):
                print('In this match, the teams are still unknown. Skipping...')
                self.__status = 5136
            else:
                self.__team_1 = team_1.find(class_='teamName').text
                self.__team_2 = team_2.find(class_='teamName').text
                print('Match: ' + self.__team_1 + ' vs ' + self.__team_2)
                team_link_1 = team_1.find('a')
                team_link_2 = team_2.find('a')
                if (team_link_1 == None) or (team_link_2 == None):
                    print('In this match, the teams are still unknown. Skipping...')
                    self.__status = 5136
                else:
                    self.__link_team_1 = source_urls[0] + team_link_1['href']
                    self.__link_team_2 = source_urls[0] + team_link_2['href']
                    format_pre = soup.find('div', class_='padding preformatted-text')
                    if (format_pre == None):
                        print('This match has not maps block. Skipping...')
                        self.__status = 5407
                        return 5407
                    else:
                        format_pre = format_pre.text
                        if (format_pre.count('Best of') == 1):
                            self.__format = format_pre
                        else:
                            print('This match has unstandart or corrupt maps block. Skipping...')
                            self.__status = 5407
                            return 5407
                    self.__format = int(self.__format[8:9])
                    print('Format: Best of ' + str(self.__format))
                    maps_list = soup.find_all(class_='mapname')
                    maps_now = [maps_list[i].text for i in range(self.__format)]
                    self.__maps = ''
                    for i in range(len(maps_now)):
                        self.__maps = self.__maps + maps_now[i] + ', '
                    self.__maps = self.__maps[0:len(self.__maps)-2]
                    print('Maps: ' + self.__maps)
                    if (match_status == 'Match over'):
                        team_1_result = team_1.find('div', class_='won')
                        team_2_result = team_2.find('div', class_='tie')
                        if(team_1_result == None) and (team_2_result == None):
                            team_1_result = team_1.find('div', class_='lost').text
                            team_2_result = team_2.find('div', class_='won').text
                        elif(team_2_result != None):
                            team_1_result = team_1.find('div', class_='tie').text
                            team_2_result = team_2.find('div', class_='tie').text
                        else:
                            team_1_result = team_1.find('div', class_='won').text
                            team_2_result = team_2.find('div', class_='lost').text
                        self.__result_maps = team_1_result + ':' + team_2_result
                        full_result = soup.find('div', class_='flexbox-column')
                        full_results = full_result.find_all(class_='results')
                        self.__result_full = ''
                        for i in range(len(full_results)):
                            full_results[i] = full_results[i].text
                            space = full_results[i].find(' ')
                            full_results[i] = full_results[i][0:space]
                            self.__result_full = self.__result_full + full_results[i] + ', '
                        self.__result_full = self.__result_full[0:len(self.__result_full)-2]
                        self.__link_team_1_stats = 'None'
                        self.__link_team_2_stats = 'None'
                        self.__links_team_1_players = 'None'
                        self.__links_team_2_players = 'None'
                    elif (match_status == 'Match deleted'):
                        print('This match cancelled. Deleting...')
                        self.__status = 4313
                        return 4313
                    elif (match_status == 'Match postponed'):
                        print('This match postponed. Skipping...')
                        self.__status = 5407
                        return 5407
                    else:
                        self.__result_maps = 'None'
                        self.__result_full = 'None'
                        teams_stats = soup.find(class_='map-stats-infobox-header')
                        links_teams_stats = teams_stats.find_all(class_='team')
                        self.__link_team_1_stats = source_urls[0] + links_teams_stats[0].find('a')['href']
                        self.__link_team_2_stats = source_urls[0] + links_teams_stats[1].find('a')['href']
                        lineups = soup.find('div', class_='lineups')
                        players = lineups.find_all('td', class_='player')
                        date_today = datetime.date.isoformat(datetime.date.today())
                        delta_3_month_ago = datetime.timedelta(days=90)
                        date_3_month_ago = datetime.date.isoformat(datetime.date.today() - delta_3_month_ago)
                        self.__links_team_1_players = []
                        self.__links_team_2_players = []
                        for i in range(5, 10):
                            nickname = players[i].find(class_='text-ellipsis').text
                            if (nickname == 'TBA'):
                                print('In team_1 some players still unknown. Skipping...')
                                self.__status = 1541
                                return 1541
                            id_player = players[i].find(class_='player-compare')
                            if (id_player == None):
                                print('In team_1 some players have not statistic page. Skipping...')
                                self.__status = 1542
                                return 1542
                            id_player = id_player['data-player-id']
                            self.__links_team_1_players.append(source_urls[0] + source_urls[2] + id_player + '/' + nickname + source_urls[3] + date_3_month_ago + source_urls[4] + date_today)
                        for i in range(15, 20):
                            nickname = players[i].find(class_='text-ellipsis').text
                            if (nickname == 'TBA'):
                                print('In team_2 some players still unknown. Skipping...')
                                self.__status = 1542
                                return 1542
                            id_player = players[i].find(class_='player-compare')
                            if (id_player == None):
                                print('In team_2 some players have not statistic page. Skipping...')
                                self.__status = 1542
                                return 1542
                            id_player = id_player['data-player-id']
                            self.__links_team_2_players.append(source_urls[0] + source_urls[2] + id_player + '/' + nickname + source_urls[3] + date_3_month_ago + source_urls[4] + date_today)
                        self.__links_team_1_players = tuple(self.__links_team_1_players)
                        self.__links_team_2_players = tuple(self.__links_team_2_players)
                    self.__link = link
                    self.__status = 200

    def get_data(self):
        """Вывод свойств объекта"""
        if (self.__status == 200) or (self.__status == 0):
            if ((self.__result_full == 'None') or (self.__result_maps == 'None')):
                data = (self.__team_1, self.__team_2, self.__date, self.__format, self.__maps, self.__link)
            else:
                data = (self.__team_1, self.__team_2, self.__date, self.__format, self.__maps, self.__result_full, self.__result_maps, self.__link)
            return data
        elif (self.__status == 1541) or (self.__status == 1542) or (self.__status == 4313):
            return self.__status
        else:
            print('Data is corrupted.')
            return self.__status

    def get_links_teams(self):
        """Вывод ссылок на команды"""
        if (self.__status == 200) or (self.__status == 0):
            data = (self.__link_team_1, self.__link_team_2)
            return data
        else:
            print('Data is corrupted.')

    def get_links_stats_teams(self):
        """Вывод ссылок на статистики команд"""
        if (self.__status == 200) or (self.__status == 0):
            data = (self.__link_team_1_stats, self.__link_team_2_stats)
            return data
        else:
            print('Data is corrupted.')

    def get_links_stats_team_1_players(self):
        """Вывод ссылок на статистики игроков команды 1"""
        if (self.__status == 200) or (self.__status == 0):
            data = self.__links_team_1_players
            return data
        else:
            print('Data is corrupted.')

    def get_links_stats_team_2_players(self):
        """Вывод ссылок на статистики игроков команды 2"""
        if (self.__status == 200) or (self.__status == 0):
            data = self.__links_team_2_players
            return data
        else:
            print('Data is corrupted.')

    def get_status(self):
        return self.__status

class Team():
    """Объект полной статистики команды"""

    def __init__(self):
        """Простая инициализация"""
        self.__team = 'None'
        self.__rating = 'unknown'
        self.__link = 'None'
        self.__Dust_2 = Map_stats()
        self.__Inferno = Map_stats()
        self.__Mirage = Map_stats()
        self.__Nuke = Map_stats()
        self.__Overpass = Map_stats()
        self.__Train = Map_stats()
        self.__Vertigo = Map_stats()
        self.__status = 0

    def upload_data(self, link_1, link_2):
        """Инициализация с конкретных ссылок"""
        print('Uploading team data: step 1...')
        time.sleep(1)
        soup_1 = upload_html(link_1) # https://www.hltv.org/team/[Number team]/[Team name]
        if (type(soup_1) == int):
            print('Error ' + soup_1 + ' while uploading ' + link + '(HTML-error).')
            self.__status = soup_1
        else:
            """Обработка данных с загруженной страницы"""
            self.__team = soup_1.find(class_='profile-team-name text-ellipsis').text
            rating = soup_1.find(class_='profile-team-stat')
            rating_text = rating.find('span').text
            if (rating_text[0] == '#'):
                rating_text = rating_text[1:]
                rating_text = int(rating_text)
            else:
                rating_text = 'unknown'
            self.__rating = rating_text
            self.__link = link_1
            print('Uploading team ' + self.__team + ' data: step 2...')
            time.sleep(1)
            soup_2 = upload_html(link_2) # https://www.hltv.org/stats/lineup/maps?lineup=[Number player 1]&lineup=[Number player 2]&lineup=[Number player 3]&lineup=[Number player 4]&lineup=[Number player 5]&minLineupMatch=3&startDate=[Date 3 month ago]&endDate=[Date today]
            if (type(soup_2) == int):
                print('Error ' + soup_2 + ' while uploading ' + link + '(HTML-error).')
                self.__status = soup_2
            else:
                """Обработка данных с загруженной страницы"""
                list_maps = soup_2.find_all(class_='tabs standard-box')
                if (len(list_maps) < 2):
                    print('In this team, the maps statistics are still unknown. Skipping...')
                    self.__status = 5136
                else:
                    list_maps = list_maps[1]
                    list_maps_urls = list_maps.find_all('a')
                    must_maps = ('Dust2', 'Inferno', 'Mirage', 'Nuke', 'Overpass', 'Train', 'Vertigo')
                    for i in range(len(list_maps_urls)-1, -1, -1):
                        if (must_maps.count(list_maps_urls[i].text) == 0):
                            list_maps_urls.pop(i)
                    maps_names = [list_maps_urls[i].text for i in range(len(list_maps_urls))]
                    full_maps_urls = []
                    for i in range(7):
                        if(maps_names.count(must_maps[i]) != 0):
                            full_maps_urls.append(list_maps_urls[maps_names.index(must_maps[i])]['href'])
                        else:
                            full_maps_urls.append('0')
                    """Инициализация статистики карт"""
                    print('Uploading team ' + self.__team + ' data: step 3: map Dust 2...')
                    self.__Dust_2 = Map_stats()
                    if (full_maps_urls[0] != '0'):
                        self.__Dust_2.upload_data(source_urls[0] + full_maps_urls[0])
                    print('Uploading team ' + self.__team + ' data: step 3: map Inferno...')
                    self.__Inferno = Map_stats()
                    if (full_maps_urls[1] != '0'):
                        self.__Inferno.upload_data(source_urls[0] + full_maps_urls[1])
                    print('Uploading team ' + self.__team + ' data: step 3: map Mirage...')
                    self.__Mirage = Map_stats()
                    if (full_maps_urls[2] != '0'):
                        self.__Mirage.upload_data(source_urls[0] + full_maps_urls[2])
                    print('Uploading team ' + self.__team + ' data: step 3: map Nuke...')
                    self.__Nuke = Map_stats()
                    if (full_maps_urls[3] != '0'):
                        self.__Nuke.upload_data(source_urls[0] + full_maps_urls[3])
                    print('Uploading team ' + self.__team + ' data: step 3: map Overpass...')
                    self.__Overpass = Map_stats()
                    if (full_maps_urls[4] != '0'):
                        self.__Overpass.upload_data(source_urls[0] + full_maps_urls[4])
                    print('Uploading team ' + self.__team + ' data: step 3: map Train...')
                    self.__Train = Map_stats()
                    if (full_maps_urls[5] != '0'):
                        self.__Train.upload_data(source_urls[0] + full_maps_urls[5])
                    print('Uploading team ' + self.__team + ' data: step 3: map Vertigo...')
                    self.__Vertigo = Map_stats()
                    if (full_maps_urls[6] != '0'):
                        self.__Vertigo.upload_data(source_urls[0] + full_maps_urls[6])
                    print('Completed.')
                    self.__status = 200

    def get_data(self):
        """Вывод свойств объекта"""
        if (self.__status == 200) or (self.__status == 0):
            Dust_2_data = self.__Dust_2.get_data()
            Inferno_data = self.__Inferno.get_data()
            Mirage_data = self.__Mirage.get_data()
            Nuke_data = self.__Nuke.get_data()
            Overpass_data = self.__Overpass.get_data()
            Train_data = self.__Train.get_data()
            Vertigo_data = self.__Vertigo.get_data()
            data = [self.__team, self.__rating]
            data.extend(Dust_2_data)
            data.extend(Inferno_data)
            data.extend(Mirage_data)
            data.extend(Nuke_data)
            data.extend(Overpass_data)
            data.extend(Train_data)
            data.extend(Vertigo_data)
            data.append(self.__link)
            data = tuple(data)
            return data
        elif (self.__status == 5136):
            return self.__status
        else:
            print('Data is corrupted.')
            return self.__status

class Player():
    """Объект индивидуальной статистики игрока"""

    def __init__(self):
        """Простая инициализация"""
        self.__nickname = 'None'
        self.__current_team = 'None'
        self.__kills = 0
        self.__deaths = 0
        self.__kill_per_death = 0
        self.__kill_per_round = 0
        self.__rounds_with_kills = 0
        self.__kill_death_difference = 0
        self.__total_opening_kills = 0
        self.__total_opening_deaths = 0
        self.__opening_kill_ratio = 0
        self.__opening_kill_rating = 0
        self.__team_win_percent_after_first_kill = 0
        self.__first_kill_in_won_rounds = 0
        self.__0_kill_rounds = 0
        self.__1_kill_rounds = 0
        self.__2_kill_rounds = 0
        self.__3_kill_rounds = 0
        self.__4_kill_rounds = 0
        self.__5_kill_rounds = 0
        self.__rifle_kills = 0
        self.__sniper_kills = 0
        self.__smg_kills = 0
        self.__pistol_kills = 0
        self.__grenade = 0
        self.__other = 0
        self.__rating_2_0 = 0
        self.__link = 'None'
        self.__status = 0

    def upload_data(self, link_1):
        """Инициализация с конкретной ссылоки"""
        print('Uploading player data: step 1...')
        time.sleep(1)
        soup_1 = upload_html(link_1) # https://www.hltv.org/stats/players/[Number player]/[Nickname]?startDate=[Date 3 month ago]&endDate=[Date today]
        if (type(soup_1) == int):
            print('Error ' + soup_1 + ' while uploading ' + link_1 + '(HTML-error).')
            self.__status = soup_1
        else:
            """Обработка данных с загруженной страницы"""
            self.__nickname = soup_1.find('h1', class_='summaryNickname text-ellipsis').text
            team_current = soup_1.find('a', class_='a-reset text-ellipsis')
            if (team_current == None):
                team_current = soup_1.find(class_='SummaryTeamname text-ellipsis')
            self.__current_team = team_current.text
            question = link_1.count('?')
            if (question == 0):
                print('Warning: the link does not contain the period of statistics collection. This means that player statistics will be taken for all time.')
            elif (question == 1):
                question_index = link_1.find('?')
                link_1 = link_1[0:question_index]
            else:
                print('Warning: probably link is corrupted.')
                question_index = link_1.find('?')
                link_1 = link_1[0:question_index]
            self.__link = link_1
            table = soup_1.find_all(class_='col stats-rows standard-box')
            table = table[1]
            self.__rating_2_0 = table.find('span', class_='strong').text
            if (check_float(self.__rating_2_0)):
                self.__rating_2_0 = float(self.__rating_2_0)
                if (self.__rating_2_0.is_integer()):
                    self.__rating_2_0 = int(self.__rating_2_0)
                tabs = soup_1.find_all('a', class_='stats-top-menu-item stats-top-menu-item-link')
                link_2 = source_urls[0] + tabs[0]['href']
                print('Uploading player ' + self.__nickname + ' data: step 2...')
                time.sleep(1)
                soup_2 = upload_html(link_2) # https://www.hltv.org/stats/players/individual/[Number player]/[Nickname]?startDate=[Date 3 month ago]&endDate=[Date today]
                if (type(soup_2) == int):
                    print('Error ' + soup_2 + ' while uploading ' + link_2 + '(HTML-error).')
                    self.__status = soup_2
                else:
                    """Обработка данных с загруженной страницы"""
                    table_rows_names = ('Kills', 'Deaths', 'Kill / Death', 'Kill / Round', 'Rounds with kills', 'Kill - Death differenceK - D diff.', 'Total opening kills', 'Total opening deaths', 'Opening kill ratio', 'Opening kill rating', 'Team win percent after first kill', 'First kill in won rounds', '0 kill rounds', '1 kill rounds', '2 kill rounds', '3 kill rounds', '4 kill rounds', '5 kill rounds', 'Rifle kills', 'Sniper kills', 'SMG kills', 'Pistol kills', 'Grenade', 'Other')
                    rows = soup_2.find_all(class_='stats-row')
                    for i in range(len(rows)):
                        rows[i] = rows[i].text
                        rows[i] = rows[i].replace(table_rows_names[i], '')
                        if((i == 10) or (i == 11)):
                            rows[i] = rows[i][0:len(rows[i])-1]
                        if (rows[i] == ''):
                            rows[i] = 0
                        rows[i] = float(rows[i])
                        if(rows[i].is_integer()):
                            rows[i] = int(rows[i])
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
                    self.__status = 200
            else:
                print('Error 4313: "__rating_2_0" is not digit; object "Player" corrupted.')
                self.__status = 4313

    def get_data(self):
        """Вывод свойств объекта"""
        if (self.__status == 200) or (self.__status == 0):
            data = (self.__nickname, self.__current_team, self.__kills, self.__deaths, self.__kill_per_death, self.__kill_per_round, self.__rounds_with_kills, self.__kill_death_difference, self.__total_opening_kills, self.__total_opening_deaths, self.__opening_kill_ratio, self.__opening_kill_rating, self.__team_win_percent_after_first_kill, self.__first_kill_in_won_rounds, self.__0_kill_rounds, self.__1_kill_rounds, self.__2_kill_rounds, self.__3_kill_rounds, self.__4_kill_rounds, self.__5_kill_rounds, self.__rifle_kills, self.__sniper_kills, self.__smg_kills, self.__pistol_kills, self.__grenade, self.__other, self.__rating_2_0, self.__link)
            return data
        else:
            print('Data is corrupted.')

"""Основной исполняемый код"""
print('This is a parcer for collecting statistics about teams and players on upcoming matches in CS:GO from hltv.org. Current version: v. 0.2.6 alpha.')
debug_mode = str(input('Enable debug mode? (Node: in debug mode you must confirm downloading data about match every time when it starting.) (Y/n): '))
while (decision_made != True):
    if ((debug_mode == 'Y') or (debug_mode == 'y') or (debug_mode == '')):
        skip_confirm = False
        decision_made = True
    elif ((debug_mode == 'N') or (debug_mode == 'n')):
        skip_confirm = True
        decision_made = True
    else:
        print('Try again.')
        decision_made = False
decision_made = False
print('Preparing list of matches...')
soup_glob = upload_html('https://www.hltv.org/matches') # Эта часть кода будет реализована в будущем для загрузки всех предстоящих матчей
if (type(soup_glob) == int):
    print('Error ' + soup_glob + ' while uploading ' + link + '(HTML-error).')
    self.__status = soup_glob
else:
    DB = Database()
    all_upcomig_matches = soup_glob.find(class_='upcoming-matches')
    list_upcoming_matches = all_upcomig_matches.find_all('a')
    urls_upcoming_matches = [source_urls[0] + list_upcoming_matches[i]['href'] for i in range(len(list_upcoming_matches))]
    exist_upcoming_matches = DB.get_urls_upcomig_matches()
    for i in range(len(exist_upcoming_matches)):
        if (urls_upcoming_matches.count(exist_upcoming_matches[i]) == 1):
            urls_upcoming_matches.remove(exist_upcoming_matches[i])
        elif (urls_upcoming_matches.count(exist_upcoming_matches[i]) > 1):
            print('Warning: probably, link corrupted (list_upcoming_matches contains the same matches)')
            for j in range(urls_upcoming_matches.count(exist_upcoming_matches[i])):
                urls_upcoming_matches.remove(exist_upcoming_matches[i])
    print('Updating info about exist matches...')
    """Обновление существующих матчей"""
    for i in range(len(exist_upcoming_matches)):
        match = Match()
        match.upload_data(exist_upcoming_matches[i])
        match_data = match.get_data()
        if (type(match_data) == tuple):
            if (len(match_data) == 6):
                DB.update_data(match_data)
            elif (len(match_data) == 8):
                id_match = DB.get_id_upcoming_match(exist_upcoming_matches[i])
                DB.write_data(match_data)
                DB.delete_data('matches_upcoming', id_match[0])
                another_match_1 = DB.get_link_upcoming_match_by_team(match_data[0])
                another_match_2 = DB.get_link_upcoming_match_by_team(match_data[1])
                another_matches = []
                if (len(another_match_1) != 0):
                    for j in range(len(another_match_1)):
                        match_status_got = get_match_status(another_match_1[j])
                        if (type(match_status_got) != int):
                            if (match_status_got != 'Match over') and (match_status_got != 'Match deleted') and (match_status_got != 'Match postponed'):
                                another_matches.append(another_match_1[j])
                                break
                if (len(another_match_2) != 0):
                    for j in range(len(another_match_2)):
                        match_status_got = get_match_status(another_match_2[j])
                        if (type(match_status_got) != int):
                            if (match_status_got != 'Match over') and (match_status_got != 'Match deleted') and (match_status_got != 'Match postponed'):
                                another_matches.append(another_match_2[j])
                                break
                if (len(another_matches) != 0):
                    for j in range(len(another_matches)):
                        urls_upcoming_matches.append(another_matches[j])
        elif (type(match_data) == int):
            if (match_data == 4313):
                id_match = DB.get_id_upcoming_match(exist_upcoming_matches[i])
                DB.delete_data('matches_upcoming', id_match[0])
            elif (match_data == 1541):
                print('This match not updated. Probably, it should delete.')
    """Добавление новых матчей"""
    print('Parcer ready to collecting new matches.')
    for i in range(len(urls_upcoming_matches)):
        decision_made = False
        while (decision_made != True):
            if (skip_confirm == False):
                start = str(input('Do you wanna ' + words[start_bool] + '? (Y/n):'))
            else:
                start = 'Y'
            if ((start == 'Y') or (start == 'y') or (start == '')):
                start_bool = False
                decision_made = True
                """Создание объекта матча и получение с него данных"""
                match = Match()
                match.upload_data(urls_upcoming_matches[i]) # Сюда нужно ввести ссылку на матч
                status_match = match.get_status()
                if(status_match == 200):
                    match_data = match.get_data()
                    links_teams = match.get_links_teams()
                    links_stats_teams = match.get_links_stats_teams()
                    links_stats_team_1_players = match.get_links_stats_team_1_players()
                    links_stats_team_2_players = match.get_links_stats_team_2_players()
                    print(match_data)
                    """Создание объектов команд и получение с них данных"""
                    team_1 = Team()
                    team_1.upload_data(links_teams[0], links_stats_teams[0])
                    team_1_data = team_1.get_data()
                    if (type(team_1_data) != int):
                        print(team_1_data)
                        print(len(team_1_data))
                        team_2 = Team()
                        team_2.upload_data(links_teams[1], links_stats_teams[1])
                        team_2_data = team_2.get_data()
                        if (type(team_2_data) != int):
                            print(team_2_data)
                            print(len(team_2_data))
                            """Создание объектов игроков и получение с них данных"""
                            team_1_player_1 = Player()
                            team_1_player_2 = Player()
                            team_1_player_3 = Player()
                            team_1_player_4 = Player()
                            team_1_player_5 = Player()
                            team_2_player_1 = Player()
                            team_2_player_2 = Player()
                            team_2_player_3 = Player()
                            team_2_player_4 = Player()
                            team_2_player_5 = Player()
                            team_1_player_1.upload_data(links_stats_team_1_players[0])
                            team_1_player_1_data = team_1_player_1.get_data()
                            print(team_1_player_1_data)
                            team_1_player_2.upload_data(links_stats_team_1_players[1])
                            team_1_player_2_data = team_1_player_2.get_data()
                            print(team_1_player_2_data)
                            team_1_player_3.upload_data(links_stats_team_1_players[2])
                            team_1_player_3_data = team_1_player_3.get_data()
                            print(team_1_player_3_data)
                            team_1_player_4.upload_data(links_stats_team_1_players[3])
                            team_1_player_4_data = team_1_player_4.get_data()
                            print(team_1_player_4_data)
                            team_1_player_5.upload_data(links_stats_team_1_players[4])
                            team_1_player_5_data = team_1_player_5.get_data()
                            print(team_1_player_5_data)
                            team_2_player_1.upload_data(links_stats_team_2_players[0])
                            team_2_player_1_data = team_2_player_1.get_data()
                            print(team_2_player_1_data)
                            team_2_player_2.upload_data(links_stats_team_2_players[1])
                            team_2_player_2_data = team_2_player_2.get_data()
                            print(team_2_player_2_data)
                            team_2_player_3.upload_data(links_stats_team_2_players[2])
                            team_2_player_3_data = team_2_player_3.get_data()
                            print(team_2_player_3_data)
                            team_2_player_4.upload_data(links_stats_team_2_players[3])
                            team_2_player_4_data = team_2_player_4.get_data()
                            print(team_2_player_4_data)
                            team_2_player_5.upload_data(links_stats_team_2_players[4])
                            team_2_player_5_data = team_2_player_5.get_data()
                            print(team_2_player_5_data)
                            DB.write_data(match_data)
                            DB.write_data(team_1_data)
                            DB.write_data(team_2_data)
                            DB.write_data(team_1_player_1_data)
                            DB.write_data(team_1_player_2_data)
                            DB.write_data(team_1_player_3_data)
                            DB.write_data(team_1_player_4_data)
                            DB.write_data(team_1_player_5_data)
                            DB.write_data(team_2_player_1_data)
                            DB.write_data(team_2_player_2_data)
                            DB.write_data(team_2_player_3_data)
                            DB.write_data(team_2_player_4_data)
                            DB.write_data(team_2_player_5_data)
            elif ((start == 'N') or (start == 'n')):
                print('Bye.')
                decision_made = True
            else:
                print('Try again.')
                decision_made = False
        if ((start == 'N') or (start == 'n')):
            break
