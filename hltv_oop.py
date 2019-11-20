from bs4 import BeautifulSoup
import requests
import time
import sqlite3
import datetime
import os

"""Global variables and functions"""
"""Глобальные переменные и функции"""

source_urls = ['https://www.hltv.org', '/matches', '/stats/players', '/team', '?startDate=', '&endDate=']
end_prog = ''
start_bool = True
skip_confirm = False
decision_made = False
program_started = False
DB_checking = True
words = {False: 'continue', True: 'start'}

def download_html(url):
    """Page download function"""
    """Функция загрузки страницы"""
    try:
        time.sleep(1) # If not do that, hltv.org get temporarily ban an IP address that is running the parser. (https://www.hltv.org/robots.txt)
        # Если этого не сделать, hltv.org временно забанит IP адрес, где запущен этот парсер. (https://www.hltv.org/robots.txt)
        req = requests.get(url)
        if (req.status_code == 200):
            soup = BeautifulSoup(req.text, 'html.parser')
            return soup
        else:
            print('Error: ' + str(req.status_code) + '. Stopping parcer...')
            return req.status_code
    except requests.Timeout as e:
        print('Error: timed out. Stopping parcing this page...')
        print(str(e))
        return 408

def check_float(str):
    """Function to check whether a string is a floating point number"""
    """Функция проверки является ли строка числом с плавающей точкой"""
    try:
        float(str)
        return True
    except ValueError:
        return False

def get_match_status(link):
    """Function getting information about the current status of the match (start time, live, over, postponed, deleted)"""
    """Функция получения информации о текущем статусе матча (время начала, начат, окончен, перенесён, удалён)"""
    soup = download_html(link) # https://www.hltv.org/matches/[number]/[matchName]
    if (type(soup) == int):
        print('Error ' + soup + ' while downloading ' + link + '(HTML-error).')
        return soup
    else:
        match_status = soup.find('div', class_='countdown').text
        return match_status

def get_id_from_link(link):
    ID = 'None'
    for i in range(1, 4):
        if (link.count(source_urls[0] + source_urls[i])):
            ID = link.replace(source_urls[0] + source_urls[i] + '/', '')
            last_slash = ID.find('/')
            if (last_slash != -1):
                ID = ID[0:ID.find('/')]
            else:
                ID = '/'
            break
    if (ID.isdigit() == True):
        return ID
    else:
        print('Error 1470: ID not founded in link ' + link + '.')
        return '0'

"""Classes of objects"""
"""Классы объектов"""

class Database():
    """Database object"""
    """Объект БД"""

    def __init__(self):
        """Default database"""
        """БД по умолчанию"""
        self.__conn = sqlite3.connect("hltv_compact.db")
        self.__cursor = self.__conn.cursor()
        self.__tables_tuple = ('matches_upcoming', 'matches_completed', 'players', 'teams', 'DB_version')
        self.__columns_tables = (('ID', 'Team_1', 'Team_2', 'Date_match', 'Format_match', 'Maps', 'Link'), ('ID', 'Team_1', 'Team_2', 'Date_match', 'Format_match', 'Maps', 'Result_full', 'Result_maps', 'Link'), ('ID', 'Player', 'Current_Team', 'Kills', 'Deaths', 'Kill_per_Death', 'Kill__per_Round', 'Rounds_with_kills', 'Kill_Death_difference', 'Total_opening_kills', 'Total_opening_deaths', 'Opening_kill_ratio', 'Opening_kill_rating', 'Team_win_percent_after_first_kill', 'First_kill_in_won_rounds', 'Zero_kill_rounds', 'One_kill_rounds', 'Double_kill_rounds', 'Triple_kill_rounds', 'Quadro_kill_rounds', 'Penta_kill_rounds', 'Rifle_kills', 'Sniper_kills', 'SMG_kills', 'Pistol_kills', 'Grenade', 'Other', 'Rating_2_0', 'Link'), ('ID', 'Team', 'Rating', 'Dust_2_Times_played', 'Dust_2_Wins', 'Dust_2_Draws', 'Dust_2_Losses', 'Dust_2_Total_rounds_played', 'Dust_2_Rounds_won', 'Dust_2_Win_percent', 'Dust_2_Pistol_rounds', 'Dust_2_Pistol_rounds_won', 'Dust_2_Pistol_round_win_percent', 'Inferno_Times_played', 'Inferno_Wins', 'Inferno_Draws', 'Inferno_Losses', 'Inferno_Total_rounds_played', 'Inferno_Rounds_won', 'Inferno_Win_percent', 'Inferno_Pistol_rounds', 'Inferno_Pistol_rounds_won', 'Inferno_Pistol_round_win_percent', 'Mirage_Times_played', 'Mirage_Wins', 'Mirage_Draws', 'Mirage_Losses', 'Mirage_Total_rounds_played', 'Mirage_Rounds_won', 'Mirage_Win_percent', 'Mirage_Pistol_rounds', 'Mirage_Pistol_rounds_won', 'Mirage_Pistol_round_win_percent', 'Nuke_Times_played', 'Nuke_Wins', 'Nuke_Draws', 'Nuke_Losses', 'Nuke_Total_rounds_played', 'Nuke_Rounds_won', 'Nuke_Win_percent', 'Nuke_Pistol_rounds', 'Nuke_Pistol_rounds_won', 'Nuke_Pistol_round_win_percent', 'Overpass_Times_played', 'Overpass_Wins', 'Overpass_Draws', 'Overpass_Losses', 'Overpass_Total_rounds_played', 'Overpass_Rounds_won', 'Overpass_Win_percent', 'Overpass_Pistol_rounds', 'Overpass_Pistol_rounds_won', 'Overpass_Pistol_round_win_percent', 'Train_Times_played', 'Train_Wins', 'Train_Draws', 'Train_Losses', 'Train_Total_rounds_played', 'Train_Rounds_won', 'Train_Win_percent', 'Train_Pistol_rounds', 'Train_Pistol_rounds_won', 'Train_Pistol_round_win_percent', 'Vertigo_Times_played', 'Vertigo_Wins', 'Vertigo_Draws', 'Vertigo_Losses', 'Vertigo_Total_rounds_played', 'Vertigo_Rounds_won', 'Vertigo_Win_percent', 'Vertigo_Pistol_rounds', 'Vertigo_Pistol_rounds_won', 'Vertigo_Pistol_round_win_percent', 'Link'), ('Build',))
        self.__tables_db = {7: 'matches_upcoming', 9: 'matches_completed', 29: 'players', 74: 'teams'}
        self.__key_words = {7: 'match', 9: 'match', 29: 'player', 74: 'team'}

    def connect_another_name(self, db):
        """Database with another name"""
        """БД с другим именем"""
        if (db.count('.db') == 0):
            db = db + '.db'
        self.__conn.close()
        self.__conn = sqlite3.connect(db)
        self.__cursor = self.__conn.cursor()

    def __del__(self):
        """Closing database"""
        """Закрытие БД"""
        self.__conn.close()

    def check(self):
        """Checking current database"""
        """Проверка текущей БД"""
        self.__cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        list_tables = self.__cursor.fetchall()
        if (list_tables != []):
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
                if (DB_version == 2):
                    print('Database build 2.')
                    print('Database is ready.')
                    return True
                elif (DB_version == 1):
                    print('Database is outdated! Updating...')
                    success_update = self.update_DB_from_1_build()
                    if (success_update == False):
                        print('Errors occurred while updating the database.')
                        return False
                    else:
                        print('Success updated.')
                        return True
                elif (DB_version > 2):
                    print('This program using the database build 2, but build ' + str(DB_version) + ' detected! Parcer cannot use this database.')
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
            print('Database is outdated! Updating...')
            columns_exist = self.check_columns_tables(4)
            if (columns_exist):
                success_update = self.update_DB_from_1_build()
                if (success_update == False):
                    print('Errors occurred while updating the database.')
                    return False
                else:
                    print('Success updated.')
                    return True
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
            """If the DB does not have some tables, the function will return False"""
            """Если БД не имеет некоторых таблиц, функция возвратит False"""
            print('Database is corrupted!')
            return False

    def write_data(self, data):
        """Writing data to the database: the size of the data tuple can only be 7, 9, 29, or 74.
        The sizes of input tuples can be changed in future versions of the parser.
        If the data is already exist in the table, it will be automatically updated."""
        """Запись данных в БД: размер кортежа data может быть только = 7, 9, 29 или 74.
        Размеры принимаемых кортежей могут быть изменены в будущих версиях парсера.
        Если данные уже существуют в таблице, они будут автоматически обновлены."""
        if ((len(data) == 7) or (len(data) == 9) or (len(data) == 29) or (len(data) == 74)):
            """Checking the availability of the data received."""
            """Проверка наличия получемых данных."""
            self.__cursor.execute("SELECT ID FROM " + self.__tables_db[len(data)] + ";")
            IDs = self.__cursor.fetchall()
            IDs_list = [IDs[i][0] for i in range(len(IDs))]
            Data_exist = IDs_list.count(int(data[0]))
            if (Data_exist != 0):
                print('This ' + self.__key_words[len(data)] + ' already exist. Data will be updated...')
                self.update_data(data)
            else:
                if (len(data) == 7):
                    """Writing of the upcoming match."""
                    """Запись предстоящего матча."""
                    self.__cursor.execute("INSERT INTO matches_upcoming VALUES(?, ?, ?, ?, ?, ?, ?);", data)
                elif (len(data) == 9):
                    """Writing of the finished match."""
                    """Запись оконченного матча."""
                    self.__cursor.execute("INSERT INTO matches_completed VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?);", data)
                elif (len(data) == 29):
                    """Writing player statistics."""
                    """Запись статистики игрока."""
                    self.__cursor.execute("INSERT INTO players VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", data)
                elif (len(data) == 74):
                    """Writing team statistics."""
                    """Запись статистики команды."""
                    self.__cursor.execute("INSERT INTO teams VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", data)
                self.__conn.commit()
        else:
            print('Error 5173.a: Size of "data" not a 7, 9, 29, or 74; data is not added into database.')

    def update_data(self, data):
        """Updating data in the database: the size of the data tuple can only be = 7, 9, 29, or 74.
        The sizes of accepted tuples will be changed in future versions of the parser.
        The definition of the record, the data of which will be updated, is carried out by checking the coincidence of references.
        Updating is carried out by deleting the old record and adding a new one with the preservation of the ID."""
        """Обновление данных в БД: размер кортежа data может быть только = 7, 9, 29, или 74.
        Размеры принимаемых кортежей будут изменены в будущих версиях парсера.
        Определение записи, данные которой будут обновляться, осуществляется проверкой совпадения ссылок.
        Обновление осуществляется путём удаления старой записи и добавлением новой с сохранением ID."""
        if ((len(data) == 7) or (len(data) == 9) or (len(data) == 29) or (len(data) == 74)):
            """Search for updated data."""
            """Поиск обновляемых данных."""
            self.__cursor.execute("SELECT ID FROM " + self.__tables_db[len(data)] + " WHERE ID = '" + data[0] + "';")
            id = self.__cursor.fetchall()
            if (id != []):
                """Delete old record"""
                """Удаление старой записи"""
                err = self.delete_data(self.__tables_db[len(data)], id[0][0])
                if (err == 200):
                    if (len(data) == 7):
                        """Update data about the upcoming match."""
                        """Обновление данных о предстоящем матче."""
                        self.__cursor.execute("INSERT INTO matches_upcoming VALUES(?, ?, ?, ?, ?, ?, ?);", data)
                    elif (len(data) == 9):
                        """Update data about the finished match."""
                        """Обновление данных об оконченном матче."""
                        self.__cursor.execute("INSERT INTO matches_completed VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?);", data)
                    elif (len(data) == 29):
                        """Update player statistics."""
                        """Обновление статистики игрока."""
                        self.__cursor.execute("INSERT INTO players VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", data)
                    elif (len(data) == 74):
                        """Update team statistics."""
                        """Обновление статистики команды."""
                        self.__cursor.execute("INSERT INTO teams VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", data)
                    self.__conn.commit()
                else:
                    print('While deleting old data getting error. Changes cancelled.')
            else:
                print('Error 1192: link from "data" not founded; data is not updated.')
        else:
            print('Error 5173.b: Size of "data" not a 7, 9, 29, or 74; data is not updated.')

    def delete_data(self, table, id):
        """Delete data from the database by ID."""
        """Удаление данных из БД по ID."""
        """Verify that entered the parameters correctly."""
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
        """Delete data from the database. This method clears the table fully."""
        """Удаление данных из БД. Данный метод очищает всю таблицу."""
        """Verify that you entered the parameters correctly."""
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
        """Getting all links of the upcoming matches from database."""
        """Получение всех ссылок предстоящих матчей из БД."""
        self.__cursor.execute("SELECT Link FROM matches_upcoming;")
        data = self.__cursor.fetchall()
        if (data != []):
            for i in range(len(data)):
                data[i] = data[i][0]
            data = tuple(data)
            return data
        else:
            return data

    def get_links_upcoming_matches_by_team(self, team_name):
        """Getting the IDs of upcoming matches a certain team."""
        """Получение ID предстоящих матчей определённой команды."""
        self.__cursor.execute('SELECT Link FROM matches_upcoming WHERE Team_1 = "' + team_name + '";')
        data = self.__cursor.fetchall()
        self.__cursor.execute('SELECT Link FROM matches_upcoming WHERE Team_2 = "' + team_name + '";')
        data_2 = self.__cursor.fetchall()
        data.extend(data_2)
        if (data != []):
            data_links = [data[i][0] for i in range(len(data))]
            data_links = tuple(data_links)
            return data_links
        else:
            return data

    def update_DB_from_1_build(self):
        for i in range(4):
            self.__cursor.execute('SELECT ID, Link FROM ' + self.__tables_tuple[i] + ';')
            IDs_and_Links = self.__cursor.fetchall()
            IDs_and_Links_changing = [list(IDs_and_Links[j]) for j in range(len(IDs_and_Links))]
            for j in range(len(IDs_and_Links_changing)):
                new_id = get_id_from_link(IDs_and_Links_changing[j][1])
                if (new_id.isdigit()) and (new_id != '0'):
                    IDs_and_Links_changing[j][0] = int(new_id)
                    self.__cursor.execute('UPDATE ' + self.__tables_tuple[i] + ' SET ID = ' + str(IDs_and_Links_changing[j][0]) + ' WHERE Link = "' + IDs_and_Links_changing[j][1] + '";')
                else:
                    return False
        self.__cursor.execute("""CREATE TABLE DB_version(Build int)""")
        self.__cursor.execute("INSERT INTO DB_version VALUES(2);")
        self.__conn.commit()
        return True

    def check_columns_tables(self, count_tables):
        if (type(count_tables) == int):
            success = True
            for i in range(count_tables):
                self.__cursor.execute("pragma table_info(" + self.__tables_tuple[i] + ");")
                info_columns = self.__cursor.fetchall()
                names_columns = [info_columns[i][1] for i in range(len(info_columns))]
                for j in range(len(names_columns)):
                    if (names_columns[j] != self.__columns_tables[i][j]):
                        print('Column "' + self.__columns_tables[i][j] + '" from table "' + self.__tables_tuple[i] + '" not exist!')
                        success = False
                        break
                if (success == False):
                    break
            return success
        else:
            return False

    def create(self):
        try:
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
            self.__cursor.execute("""CREATE TABLE DB_version(Build int)""")
            self.__cursor.execute("INSERT INTO DB_version VALUES(2);")
            self.__conn.commit()
            return True
        except sqlite3.Error as e:
            print("Error while creating database: " + str(e))
            return False
        except Exception as e:
            print("Unknown error while creating database: " + str(e))
            return False

    def get_ids_upcoming_matches(self):
        self.__cursor.execute('SELECT ID FROM matches_upcoming;')
        data = self.__cursor.fetchall()
        if (data != []):
            data_IDs = [data[i][0] for i in range(len(data))]
            data_IDs = tuple(data_IDs)
            return data_IDs
        else:
            return data

    def change_upcoming_match_link(self, ID_match, new_link):
        if (type(ID_match) == int) and (type(new_link) == str):
            self.__cursor.execute('UPDATE matches_upcoming SET Link = "' + new_link + '" WHERE ID = ' + str(ID_match) + ';')
            self.__conn.commit()
            return True
        else:
            return False

    def get_DB_build(self):
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
            print("Error while getting build version database: " + str(e))
            return False
        except Exception as e:
            print("Unknown error while getting build version database: " + str(e))
            return False

class Map_stats():
    """Team statistics object on the certain map"""
    """Объект статистики команды на определённой карте"""

    def __init__(self):
        """Default initialization"""
        """Инициализация по умолчанию"""
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

    def download_data(self, link):
        """Downloading data"""
        """Загрузка данных"""
        soup = download_html(link) # https://www.hltv.org/stats/teams/map/[mapNumber]/[number]/[teamName]
        if (type(soup) == int):
            print('Error ' + str(soup) + ' while uploading ' + link + '(HTML-error).')
            self.__status = soup
        else:
            """Processing data from a downloaded page"""
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
                    stats[i] = float(stats[i])
                    if(stats[i].is_integer() == True):
                        stats[i] = int(stats[i])
                    data_team_map.append(stats[i])
                else:
                    for j in range(len(stats[i])):
                        stats[i][j] = int(stats[i][j])
                        data_team_map.append(stats[i][j])
            """Assigning received data to object properties"""
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
        """Getting object properties"""
        """Получение свойств объекта"""
        if (self.__status == 200) or (self.__status == 0):
            data = (self.__times_played, self.__wins, self.__draws, self.__losses, self.__total_rounds_played, self.__rounds_won, self.__win_percent, self.__pistol_rounds, self.__pistol_rounds_won, self.__pistol_round_win_percent)
            return data
        else:
            print('Data is corrupted.')
            return self.__status

    def get_status(self):
        """Getting object status"""
        """Получение статуса объекта"""
        return self.__status

class Match():

    def __init__(self):
        """Default initialization"""
        """Инициализация по умолчанию"""
        self.__ID = 0
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

    def download_data(self, link):
        """Downloading data"""
        """Загрузка данных"""
        print('Uploading match data...')
        soup = download_html(link) # https://www.hltv.org/matches/[ID]/[matchName]
        if (type(soup) == int):
            print('Error ' + str(soup) + ' while uploading ' + link + '(HTML-error).')
            self.__status = soup
        else:
            self.__ID = get_id_from_link(link)
            if (self.__ID == '0'):
                self.__status = 1470
                return self.__status
            """Processing data from a downloaded page"""
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
                        lineups = soup.find_all('div', class_='lineup standard-box')
                        players_team_1_nicknames = lineups[0].find_all('div', class_='text-ellipsis')
                        players_team_2_nicknames = lineups[1].find_all('div', class_='text-ellipsis')
                        players_team_1_compare = lineups[0].find_all('div', class_='player-compare')
                        players_team_2_compare = lineups[1].find_all('div', class_='player-compare')
                        for i in range(int(len(players_team_1_compare)/2-1), -1, -1):
                            players_team_1_compare.pop(i)
                        for i in range(int(len(players_team_2_compare)/2-1), -1, -1):
                            players_team_2_compare.pop(i)
                        date_today = datetime.date.isoformat(datetime.date.today())
                        delta_3_month_ago = datetime.timedelta(days=90)
                        date_3_month_ago = datetime.date.isoformat(datetime.date.today() - delta_3_month_ago)
                        self.__links_team_1_players = []
                        self.__links_team_2_players = []
                        if (len(players_team_1_nicknames) < 5):
                            print('In team_1 some players still unknown. Skipping...')
                            self.__status = 1543
                            return 1543
                        if (len(players_team_2_nicknames) < 5):
                            print('In team_2 some players still unknown. Skipping...')
                            self.__status = 1543
                            return 1543
                        if (len(players_team_1_compare) < 5):
                            print('In team_1 some players have not statistic page. Skipping...')
                            self.__status = 1544
                            return 1544
                        if (len(players_team_2_compare) < 5):
                            print('In team_2 some players have not statistic page. Skipping...')
                            self.__status = 1544
                            return 1544
                        for i in range(5):
                            nickname = players_team_1_nicknames[i].text
                            if (nickname == 'TBA') or (nickname == 'TBD'):
                                print('In team_1 some players still unknown. Skipping...')
                                self.__status = 1541
                                return 1541
                            id_player = players_team_1_compare[i]['data-player-id']
                            if (id_player == '0'):
                                print('In team_1 some players still unknown. Skipping...')
                                self.__status = 1541
                                return 1541
                            self.__links_team_1_players.append(source_urls[0] + source_urls[2] + '/' + id_player + '/' + nickname + source_urls[4] + date_3_month_ago + source_urls[5] + date_today)
                        for i in range(5):
                            nickname = players_team_2_nicknames[i].text
                            if (nickname == 'TBA') or (nickname == 'TBD'):
                                print('In team_2 some players still unknown. Skipping...')
                                self.__status = 1541
                                return 1541
                            id_player = players_team_2_compare[i]['data-player-id']
                            if (id_player == '0'):
                                print('In team_2 some players still unknown. Skipping...')
                                self.__status = 1541
                                return 1541
                            self.__links_team_2_players.append(source_urls[0] + source_urls[2] + '/' + id_player + '/' + nickname + source_urls[4] + date_3_month_ago + source_urls[5] + date_today)
                        self.__links_team_1_players = tuple(self.__links_team_1_players)
                        self.__links_team_2_players = tuple(self.__links_team_2_players)
                    self.__link = link
                    self.__status = 200

    def get_data(self):
        """Getting object properties"""
        """Получение свойств объекта"""
        if (self.__status == 200) or (self.__status == 0):
            if ((self.__result_full == 'None') or (self.__result_maps == 'None')):
                data = (self.__ID, self.__team_1, self.__team_2, self.__date, self.__format, self.__maps, self.__link)
            else:
                data = (self.__ID, self.__team_1, self.__team_2, self.__date, self.__format, self.__maps, self.__result_full, self.__result_maps, self.__link)
            return data
        elif (self.__status == 1541) or (self.__status == 1543) or (self.__status == 1544):
            return self.__status
        elif (self.__status == 4313):
            return {self.__status: self.__ID}
        else:
            print('Data is corrupted.')
            return self.__status

    def get_links_teams(self):
        """Getting team links"""
        """Получение ссылок на команды"""
        if (self.__status == 200) or (self.__status == 0):
            data = (self.__link_team_1, self.__link_team_2)
            return data
        else:
            print('Data is corrupted.')

    def get_links_stats_teams(self):
        """Getting team statistics links"""
        """Получение ссылок на статистики команд"""
        if (self.__status == 200) or (self.__status == 0):
            data = (self.__link_team_1_stats, self.__link_team_2_stats)
            return data
        else:
            print('Data is corrupted.')

    def get_links_stats_players(self, team_bool):
        """Getting players statistics links"""
        """Получение ссылок на статистики игроков"""
        if (self.__status == 200) or (self.__status == 0):
            if (type(team_bool) == bool):
                if (team_bool == True):
                    data = self.__links_team_1_players
                else:
                    data = self.__links_team_2_players
                return data
            else:
                print('Error 6001: getted variable not "bool".')
                return 6001
        else:
            print('Data is corrupted.')

    def get_status(self):
        return self.__status

class Team():
    """Object team statistics"""
    """Объект полной статистики команды"""

    def __init__(self):
        """Default initialization"""
        """Инициализация по умолчанию"""
        self.__ID = 0
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

    def download_data(self, link_1, link_2):
        """Downloading data"""
        """Загрузка данных"""
        print('Uploading team data: step 1...')
        soup_1 = download_html(link_1) # https://www.hltv.org/team/[ID]/[Team name]
        if (type(soup_1) == int):
            print('Error ' + str(soup_1) + ' while uploading ' + link + '(HTML-error).')
            self.__status = soup_1
        else:
            self.__ID = get_id_from_link(link_1)
            if (self.__ID == '0'):
                self.__status = 1470
                return self.__status
            """Processing data from a downloaded page"""
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
            """Downloading data"""
            """Загрузка данных"""
            print('Uploading team ' + self.__team + ' data: step 2...')
            soup_2 = download_html(link_2) # https://www.hltv.org/stats/lineup/maps?lineup=[Number player 1]&lineup=[Number player 2]&lineup=[Number player 3]&lineup=[Number player 4]&lineup=[Number player 5]&minLineupMatch=3&startDate=[Date 3 month ago]&endDate=[Date today]
            if (type(soup_2) == int):
                print('Error ' + str(soup_2) + ' while uploading ' + link + '(HTML-error).')
                self.__status = soup_2
            else:
                """Processing data from a downloaded page"""
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
                    """Download statistics maps"""
                    """Загрузка статистики карт"""
                    passing = True
                    print('Uploading team ' + self.__team + ' data: step 3: map Dust 2...')
                    if (full_maps_urls[0] != '0'):
                        self.__Dust_2.download_data(source_urls[0] + full_maps_urls[0])
                        if (self.__Dust_2.get_status() != 200):
                            passing = False
                            self.__status = self.__Dust_2.get_status()
                    if (passing == True):
                        print('Uploading team ' + self.__team + ' data: step 3: map Inferno...')
                        if (full_maps_urls[1] != '0'):
                            self.__Inferno.download_data(source_urls[0] + full_maps_urls[1])
                            if (self.__Inferno.get_status() != 200):
                                passing = False
                                self.__status = self.__Inferno.get_status()
                    if (passing == True):
                        print('Uploading team ' + self.__team + ' data: step 3: map Mirage...')
                        if (full_maps_urls[2] != '0'):
                            self.__Mirage.download_data(source_urls[0] + full_maps_urls[2])
                            if (self.__Mirage.get_status() != 200):
                                passing = False
                                self.__status = self.__Mirage.get_status()
                    if (passing == True):
                        print('Uploading team ' + self.__team + ' data: step 3: map Nuke...')
                        if (full_maps_urls[3] != '0'):
                            self.__Nuke.download_data(source_urls[0] + full_maps_urls[3])
                            if (self.__Nuke.get_status() != 200):
                                passing = False
                                self.__status = self.__Nuke.get_status()
                    if (passing == True):
                        print('Uploading team ' + self.__team + ' data: step 3: map Overpass...')
                        if (full_maps_urls[4] != '0'):
                            self.__Overpass.download_data(source_urls[0] + full_maps_urls[4])
                            if (self.__Overpass.get_status() != 200):
                                passing = False
                                self.__status = self.__Overpass.get_status()
                    if (passing == True):
                        print('Uploading team ' + self.__team + ' data: step 3: map Train...')
                        if (full_maps_urls[5] != '0'):
                            self.__Train.download_data(source_urls[0] + full_maps_urls[5])
                            if (self.__Train.get_status() != 200):
                                passing = False
                                self.__status = self.__Train.get_status()
                    if (passing == True):
                        print('Uploading team ' + self.__team + ' data: step 3: map Vertigo...')
                        if (full_maps_urls[6] != '0'):
                            self.__Vertigo.download_data(source_urls[0] + full_maps_urls[6])
                            if (self.__Vertigo.get_status() != 200):
                                passing = False
                                self.__status = self.__Vertigo.get_status()
                    if (passing == True):
                        print('Team statistics download complete.')
                        self.__status = 200

    def get_data(self):
        """Getting object properties"""
        """Получение свойств объекта"""
        if (self.__status == 200) or (self.__status == 0):
            Dust_2_data = self.__Dust_2.get_data()
            Inferno_data = self.__Inferno.get_data()
            Mirage_data = self.__Mirage.get_data()
            Nuke_data = self.__Nuke.get_data()
            Overpass_data = self.__Overpass.get_data()
            Train_data = self.__Train.get_data()
            Vertigo_data = self.__Vertigo.get_data()
            data = [self.__ID, self.__team, self.__rating]
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
    """Object of individual player statistics"""
    """Объект индивидуальной статистики игрока"""

    def __init__(self):
        """Default initialization"""
        """Инициализация по умолчанию"""
        self.__ID = 0
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

    def download_data(self, link_1):
        """Downloading data"""
        """Загрузка данных"""
        print('Uploading player data: step 1...')
        soup_1 = download_html(link_1) # https://www.hltv.org/stats/players/[ID]/[Nickname]?startDate=[Date 3 month ago]&endDate=[Date today]
        if (type(soup_1) == int):
            print('Error ' + str(soup_1) + ' while uploading ' + link_1 + '(HTML-error).')
            self.__status = soup_1
        else:
            self.__ID = get_id_from_link(link_1)
            if (self.__ID == '0'):
                self.__status = 1470
                return self.__status
            """Processing data from a downloaded page"""
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
                """Downloading data"""
                """Загрузка данных"""
                print('Uploading player ' + self.__nickname + ' data: step 2...')
                soup_2 = download_html(link_2) # https://www.hltv.org/stats/players/individual/[Number player]/[Nickname]?startDate=[Date 3 month ago]&endDate=[Date today]
                if (type(soup_2) == int):
                    print('Error ' + str(soup_2) + ' while uploading ' + link_2 + '(HTML-error).')
                    self.__status = soup_2
                else:
                    """Processing data from a downloaded page"""
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
                    """Assigning received data to object properties"""
                    """Присвоение полученных данных свойствам объекта"""
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
                print('Error 4314: "__rating_2_0" is not digit; object "Player" corrupted.')
                self.__status = 4314

    def get_data(self):
        """Getting object properties"""
        """Получение свойств объекта"""
        if (self.__status == 200) or (self.__status == 0):
            data = (self.__ID, self.__nickname, self.__current_team, self.__kills, self.__deaths, self.__kill_per_death, self.__kill_per_round, self.__rounds_with_kills, self.__kill_death_difference, self.__total_opening_kills, self.__total_opening_deaths, self.__opening_kill_ratio, self.__opening_kill_rating, self.__team_win_percent_after_first_kill, self.__first_kill_in_won_rounds, self.__0_kill_rounds, self.__1_kill_rounds, self.__2_kill_rounds, self.__3_kill_rounds, self.__4_kill_rounds, self.__5_kill_rounds, self.__rifle_kills, self.__sniper_kills, self.__smg_kills, self.__pistol_kills, self.__grenade, self.__other, self.__rating_2_0, self.__link)
            return data
        else:
            print('Data is corrupted.')

"""Main executable code"""
"""Основной исполняемый код"""
print('This is a parcer for collecting statistics about teams and players on upcoming matches in CS:GO from hltv.org. Current version: 0.3.2 alpha.')
DB = Database()
DB_ready = DB.check()
while (DB_checking):
    if (DB_ready):
        DB_checking = False
        while (program_started == False):
            start_program = str(input('Start parcer? (Y/n): '))
            if ((start_program == 'Y') or (start_program == 'y') or (start_program == '')):
                program_started = True
                while (decision_made != True):
                    debug_mode = str(input('Enable debug mode? (Note: in debug mode you must confirm downloading data about match every time when it starting.) (Y/n): '))
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
                soup_glob = download_html('https://www.hltv.org/matches') # Эта часть кода будет реализована в будущем для загрузки всех предстоящих матчей
                if (type(soup_glob) == int):
                    print('Error ' + soup_glob + ' while uploading ' + link + '(HTML-error).')
                    self.__status = soup_glob
                else:
                    all_upcomig_matches = soup_glob.find(class_='upcoming-matches')
                    list_upcoming_matches = all_upcomig_matches.find_all('a', class_='a-reset')
                    urls_upcoming_matches = [source_urls[0] + list_upcoming_matches[i]['href'] for i in range(len(list_upcoming_matches))]
                    IDs_upcoming_matches = [int(get_id_from_link(urls_upcoming_matches[i])) for i in range(len(urls_upcoming_matches))]
                    if (IDs_upcoming_matches.count(0) != 0):
                        print('Parcer stopping...')
                    else:
                        IDs_exist_upcoming_matches = DB.get_ids_upcoming_matches()
                        links_exist_upcoming_matches = DB.get_urls_upcomig_matches()
                        for i in range(len(IDs_exist_upcoming_matches)):
                            if (IDs_upcoming_matches.count(IDs_exist_upcoming_matches[i]) == 1):
                                index_ID = IDs_upcoming_matches.index(IDs_exist_upcoming_matches[i])
                                if (urls_upcoming_matches[index_ID] != links_exist_upcoming_matches[i]):
                                    print ('Changing link ' + links_exist_upcoming_matches[i] + ' to ' + urls_upcoming_matches[index_ID])
                                    updated_link = DB.change_upcoming_match_link(IDs_upcoming_matches[index_ID], urls_upcoming_matches[index_ID])
                                IDs_upcoming_matches.pop(index_ID)
                                urls_upcoming_matches.pop(index_ID)
                            elif (IDs_upcoming_matches.count(IDs_exist_upcoming_matches[i]) > 1):
                                print('Warning: probably, link corrupted (list_upcoming_matches contains the same matches)')
                                for j in range(IDs_upcoming_matches.count(IDs_exist_upcoming_matches[i])):
                                    index_ID = IDs_upcoming_matches.index(IDs_exist_upcoming_matches[i])
                                    if (urls_upcoming_matches[index_ID] != links_exist_upcoming_matches[i]):
                                        print ('Changing link ' + links_exist_upcoming_matches[i] + ' to ' + urls_upcoming_matches[index_ID])
                                        updated_link = DB.change_upcoming_match_link(IDs_upcoming_matches[index_ID], urls_upcoming_matches[index_ID])
                                    IDs_upcoming_matches.pop(index_ID)
                                    urls_upcoming_matches.pop(index_ID)
                        print('Updating info about exist matches...')
                        """Update existing matches"""
                        """Обновление существующих матчей"""
                        for i in range(len(links_exist_upcoming_matches)):
                            match = Match()
                            match.download_data(links_exist_upcoming_matches[i])
                            match_data = match.get_data()
                            if (type(match_data) == tuple):
                                if (len(match_data) == 7):
                                    DB.update_data(match_data)
                                elif (len(match_data) == 9):
                                    DB.write_data(match_data)
                                    DB.delete_data('matches_upcoming', match_data[0])
                                    another_match_1 = DB.get_links_upcoming_matches_by_team(match_data[1])
                                    another_match_2 = DB.get_links_upcoming_matches_by_team(match_data[2])
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
                            elif (type(match_data) == dict):
                                id_match = match_data[4313]
                                DB.delete_data('matches_upcoming', id_match)
                            elif (type(match_data) == int):
                                if (match_data == 1541) or (match_data == 1543) or (match_data == 1544):
                                    print('This match not updated. Probably, it should delete.')
                        """Adding new matches"""
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
                                    """Creating a match object and retrieving data from it"""
                                    """Создание объекта матча и получение с него данных"""
                                    match = Match()
                                    match.download_data(urls_upcoming_matches[i]) # Сюда нужно ввести ссылку на матч
                                    status_match = match.get_status()
                                    if(status_match == 200):
                                        match_data = match.get_data()
                                        links_teams = match.get_links_teams()
                                        links_stats_teams = match.get_links_stats_teams()
                                        links_stats_team_1_players = match.get_links_stats_players(True)
                                        links_stats_team_2_players = match.get_links_stats_players(False)
                                        print(match_data)
                                        """Creating command objects and retrieving data from them"""
                                        """Создание объектов команд и получение с них данных"""
                                        team_1 = Team()
                                        team_1.download_data(links_teams[0], links_stats_teams[0])
                                        team_1_data = team_1.get_data()
                                        if (type(team_1_data) != int):
                                            print(team_1_data)
                                            print(len(team_1_data))
                                            team_2 = Team()
                                            team_2.download_data(links_teams[1], links_stats_teams[1])
                                            team_2_data = team_2.get_data()
                                            if (type(team_2_data) != int):
                                                print(team_2_data)
                                                print(len(team_2_data))
                                                """Creating player objects and retrieving data from them"""
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
                                                team_1_player_1.download_data(links_stats_team_1_players[0])
                                                team_1_player_1_data = team_1_player_1.get_data()
                                                print(team_1_player_1_data)
                                                team_1_player_2.download_data(links_stats_team_1_players[1])
                                                team_1_player_2_data = team_1_player_2.get_data()
                                                print(team_1_player_2_data)
                                                team_1_player_3.download_data(links_stats_team_1_players[2])
                                                team_1_player_3_data = team_1_player_3.get_data()
                                                print(team_1_player_3_data)
                                                team_1_player_4.download_data(links_stats_team_1_players[3])
                                                team_1_player_4_data = team_1_player_4.get_data()
                                                print(team_1_player_4_data)
                                                team_1_player_5.download_data(links_stats_team_1_players[4])
                                                team_1_player_5_data = team_1_player_5.get_data()
                                                print(team_1_player_5_data)
                                                team_2_player_1.download_data(links_stats_team_2_players[0])
                                                team_2_player_1_data = team_2_player_1.get_data()
                                                print(team_2_player_1_data)
                                                team_2_player_2.download_data(links_stats_team_2_players[1])
                                                team_2_player_2_data = team_2_player_2.get_data()
                                                print(team_2_player_2_data)
                                                team_2_player_3.download_data(links_stats_team_2_players[2])
                                                team_2_player_3_data = team_2_player_3.get_data()
                                                print(team_2_player_3_data)
                                                team_2_player_4.download_data(links_stats_team_2_players[3])
                                                team_2_player_4_data = team_2_player_4.get_data()
                                                print(team_2_player_4_data)
                                                team_2_player_5.download_data(links_stats_team_2_players[4])
                                                team_2_player_5_data = team_2_player_5.get_data()
                                                print(team_2_player_5_data)
                                                print('Players statistics download complete.')
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
            elif ((start_program == 'N') or (start_program == 'n')):
                print('Bye.')
                program_started = True
            else:
                print('Try again.')
                program_started = False
    else:
        print("Got error while checking or updating database.")
        user_want_recreate = str(input('Want to recreate the database (if yes, the old database will saved as hltv_compact_old.db)? (Y/n):'))
        if ((user_want_recreate == 'Y') or (user_want_recreate == 'y') or (user_want_recreate == '')):
            print('Disconnecting database...')
            del DB
            print('Renaming...')
            os.rename('hltv_compact.db', 'hltv_compact_old.db')
            DB = Database()
            DB_ready = DB.check()
            DB_checking = True
        elif ((user_want_recreate == 'N') or (user_want_recreate == 'n')):
            print('Bye.')
            DB_checking = False
        else:
            print('Try again.')
            DB_checking = True
