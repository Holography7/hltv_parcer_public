import sqlite3
import shutil
from class_Program import *
from class_Match import *
from DB_structure import *

class DatabaseException(Exception):
    pass

class Database(Program):
    """Database object"""
    """Объект БД"""

    def __init__(self, db_name):
        """Connecting, checking, and updating database"""
        """Подключение, проверка и обновление БД"""

        def check_database(old_database=False):
            """Cheking tables and columns. Use this function only when __CONN and __CURSOR initialized! This function is only available in __init__!"""
            """Проверка таблиц и столбцов. Использовать эту функцию только когда __CONN и __CURSOR инициализированы! Эта функция доступна только в __init__!"""
            if old_database: # initializing database structure
                db_struct = OLD_TABLES # dict of database structure, imported from DB_structure
            else:
                db_struct = TABLES # dict of database structure, imported from DB_structure
            self.__CURSOR.execute("SELECT name FROM sqlite_master WHERE type='table';") # getting list of table titles
            list_tables = self.__CURSOR.fetchall()
            set_tables = set(table[0] for table in list_tables)
            true_set_tables = set(db_struct.keys())
            if set_tables != true_set_tables: # cheking tables
                self.__CONN.close()
                raise DatabaseException('Database error while checking database: database corrupt (table not exist or unknown).')
            for table in db_struct.keys(): # cheking columns
                self.__CURSOR.execute("pragma table_info({});".format(table)) # getting columns from table
                info_columns = self.__CURSOR.fetchall()
                columns_titles = tuple([col_title[1] for col_title in info_columns])
                true_columns_titles = tuple(db_struct[table].keys())
                if columns_titles != true_columns_titles:
                    self.__CONN.close()
                    raise DatabaseException('Database error while checking database: database corrupt (some columns not exist or unknown in table "{}").'.format(table))

        def update_DB_from_4_build():
            """Use this function only when __CONN and __CURSOR initialized! This function is only available in __init__!"""
            """Использовать эту функцию только когда __CONN и __CURSOR инициализированы! Эта функция доступна только в __init__!"""
            check_database(old_database=True)
            try:
                create_tables_commands = tuple(['CREATE TABLE {}({});'.format(table, ', '.join([' '.join((col_title, col_type)) for col_title, col_type in self.__TABLES[table].items()])) for table in self.__TABLES.keys()]) # commands for creating new tables
                self.__CURSOR.execute('SELECT * FROM matches_upcoming ORDER BY ID;') # getting data from table "matches_upcoming"
                data_matches_upcoming = self.__CURSOR.fetchall()
                self.__CURSOR.execute('SELECT * FROM matches_completed ORDER BY ID;') # getting data from table "matches_completed"
                data_matches_completed = self.__CURSOR.fetchall()
                # now begining bugfix to deleting duplicate completed matches
                IDs_matches_completed = [match[0] for match in data_matches_completed]
                for match in data_matches_completed:
                    if IDs_matches_completed.count(match[0]) > 1:
                        IDs_matches_completed.remove(match[0])
                        data_matches_completed.remove(match)
                # bugfix ended
                data_matches = data_matches_upcoming + data_matches_completed
                # begin the part that takes many time because it's updating from HLTV
                self.init_progress_bar('Updating database', len(data_matches)) # initialization loading progress bar
                downloaded_data_matches = []
                for old_match in data_matches:
                    new_match = Match(old_match[1] + ' vs ' + old_match[2], old_match[3], old_match[4], old_match[5], old_match[-1])
                    downloaded_data_matches.append(new_match.data)
                    Program.loading_progress['loading_points'] += 1
                    self.log_and_print(new_match)
                self.close_progress_bar()
                # end downloading part
                downloaded_data_matches = tuple(downloaded_data_matches)
                self.__CURSOR.execute('SELECT * FROM players ORDER BY ID;') # getting data from table "players"
                data_players = self.__CURSOR.fetchall()
                # now begining same bugfix for players
                IDs_players = [player[0] for player in data_players]
                for player in data_players:
                    if IDs_players.count(player[0]) > 1:
                        IDs_players.remove(player[0])
                        data_players.remove(player)
                # bugfix ended
                data_players = [list(player) for player in data_players]
                # adding last date of update... maybe
                for player in data_players:
                    self.__CURSOR.execute('SELECT Date_match FROM matches_completed WHERE Team_1 = "{0}" OR Team_2 = "{0}" ORDER BY Date_match DESC;'.format(player[2]))
                    dates = self.__CURSOR.fetchall()
                    if dates:
                        player.append(dates[0][0])
                    else:
                        player.append(datetime.isoformat(datetime.fromtimestamp(0), sep=' ')) # HAHAHAHAHAHAH
                    player = tuple(player)
                data_players = tuple(data_players)
                self.__CURSOR.execute('SELECT * FROM teams ORDER BY ID;') # getting data from table "teams"
                data_teams = self.__CURSOR.fetchall()
                data_teams = [list(team) for team in data_teams]
                for team in data_teams:
                    # changing values of rating "unknown" to -1:
                    if team[2] == 'unknown':
                        team[2] = -1
                    # adding last date of update... maybe
                    self.__CURSOR.execute('SELECT Date_match FROM matches_completed WHERE Team_1 = "{0}" OR Team_2 = "{0}" ORDER BY Date_match DESC;'.format(team[1]))
                    dates = self.__CURSOR.fetchall()
                    if dates:
                        team.append(dates[0][0])
                    else:
                        team.append(datetime.isoformat(datetime.fromtimestamp(0), sep=' ')) # HAHAHAHAHAHAH
                    team = tuple(team)
                new_data = {'matches': downloaded_data_matches, 'players': data_players, 'teams': data_teams, 'dump': [], 'db_version': ((5, ), )}
                for table in OLD_TABLES.keys(): # deleting old tables
                    self.__CURSOR.execute('DROP TABLE {};'.format(table))
                for command in create_tables_commands: # creating new tables
                    self.__CURSOR.execute(command)
                for table in TABLES.keys(): # writing new data into database
                    for element in new_data[table]:
                        self.__CURSOR.execute('INSERT INTO {} VALUES({});'.format(table, ', '.join(['?'] * len(element))), element)
                self.__CONN.commit()
            except sqlite3.OperationalError as e:
                self.__CONN.close()
                raise DatabaseException("Database error while cheking database: {}.".format(str(e)))

        # begin __init__
        create_db = False
        if not os.path.isfile(db_name): # cheking that file database is exist
            self.log_and_print('Warning: database not found. Creating new database...')
            create_db = True
        try:
            self.__CONN = sqlite3.connect(db_name) # connect database (or create if not exist)
            self.__CURSOR = self.__CONN.cursor()
        except Exception as e:
            self.__CONN.close()
            raise DatabaseException("Database error while connecting database: {}".format(str(e)))
        self.__TABLES = TABLES # dict of database structure, imported from DB_structure
        if create_db: # Create tables if DB not exist before
            create_tables_commands = tuple(['CREATE TABLE {}({});'.format(table, ', '.join([' '.join((col_title, col_type)) for col_title, col_type in self.__TABLES[table].items()])) for table in self.__TABLES.keys()])
            try:
                for command in create_tables_commands: # creating tables
                    self.__CURSOR.execute(command)
                self.__CURSOR.execute('INSERT INTO DB_version VALUES(5);') # Insert build version
                self.__CONN.commit()
            except Exception as e:
                self.__CONN.close()
                raise DatabaseException("Database error while creating database: {}".format(str(e)))
        try: # cheking for database version
            self.__CURSOR.execute('SELECT build FROM db_version;')
        except sqlite3.OperationalError:
            self.__CONN.close()
            raise DatabaseException('Database error while cheking database: table "db_version" not found.')
        except Exception as e:
            self.__CONN.close()
            raise DatabaseException("Database error while cheking database: {}.".format(str(e)))
        else:
            DB_version = self.__CURSOR.fetchall()
            if DB_version[0][0] == 4: # updating database from build 4
                self.__CURSOR.execute('SELECT * FROM matches_completed;')
                completed_matches = self.__CURSOR.fetchall()
                if Program.settings['proxy_mode']:
                    calc_time = time.gmtime(len(completed_matches) * round((Program.proxies[Program.faster_proxy] / 1000) + 1))
                else:
                    calc_time = time.gmtime(len(completed_matches))
                time_to_update_str = '{}{}{}'.format('{} hour{} '.format(str(calc_time.tm_hour), 's' * int((calc_time.tm_hour - 1) // (calc_time.tm_hour - 1.1)) ** 2) * int(calc_time.tm_hour // (calc_time.tm_hour - 0.1)), '{} minute{} '.format(str(calc_time.tm_min), 's' * int((calc_time.tm_min - 1) // (calc_time.tm_min - 1.1)) ** 2) * int(calc_time.tm_min // (calc_time.tm_min - 0.1)), '{} second{}'.format(str(calc_time.tm_sec), 's' * int((calc_time.tm_sec - 1) // (calc_time.tm_sec - 1.1)) ** 2) * int(calc_time.tm_sec // (calc_time.tm_sec - 0.1)))
                update_DB = self.question('Database is outdated (build 4). Update takes a very long time ({}) and requires a stable Internet connection. Do you want to update? (Y/n): '.format(time_to_update_str))
                if update_DB:
                    update_DB_from_4_build()
                    self.log_and_print('Database "{}" updated.'.format(db_name))
                else:
                    self.__CONN.close()
                    raise DatabaseException('Database update cancelled by user.')
            elif DB_version[0][0] == 5:
                self.log_and_print('Build of database "{}" is 5.'.format(db_name))
            else:
                self.__CONN.close()
                raise DatabaseException('Database error while cheking database: database is too outdated (build {}). Use previous version to update database to build 4.'.format(str(DB_version[0][0])))
            check_database() # checking database if build 5
            if not os.path.exists('backup_db'): # cheking backup directory
                os.mkdir('backup_db')
            shutil.copy(db_name, 'backup_db') # backuping database
            if '.' in db_name:
                bckp_db_name = db_name[:db_name.index('.')] + ' ' + datetime.isoformat(datetime.today().replace(microsecond=0), sep=' ').replace(':', '-') + '.db'
            else:
                bckp_db_name = db_name + ' ' + datetime.isoformat(datetime.today().replace(microsecond=0), sep=' ').replace(':', '-') + '.db'
            os.rename('backup_db\\' + db_name, 'backup_db\\' + bckp_db_name)
            self.log_and_print('Database "{}" connected, checked and backuped.'.format(db_name))

    def __del__(self):
        self.__CONN.close()

    def write_data(self, data):
        """Writing data to the database: the size of the data tuple can only be 13, 30, 137 or 528.
        The sizes of input tuples can be changed in future versions of the parser.
        If the data is already exist in the table, it will be automatically updated."""
        """Запись данных в БД: размер кортежа data может быть только = 13, 30, 137 или 528.
        Размеры принимаемых кортежей могут быть изменены в будущих версиях парсера.
        Если данные уже существуют в таблице, они будут автоматически обновлены."""
        len_data_to_table = {13: ('matches', 'Match'), 30: ('players', 'Player'), 137: ('teams', 'Team'), 528: ('dump', 'Dump of match')} # needed to understand what is the data
        if len(data) not in len_data_to_table:
            raise DatabaseException('Database error while writing data into database: wrong len of data = {}, must be 13, 30, 137 or 528.'.format(str(len(data))))
        self.__CURSOR.execute('SELECT id FROM {};'.format(len_data_to_table[len(data)][0])) # getting tuple IDs from database
        IDs = self.__CURSOR.fetchall()
        IDs = tuple(ID[0] for ID in IDs)
        if data[0] in IDs: # update (delete old) data if data already exist in database (cheking by ID)
            self.log_and_print('{} "{}" data already exist. Data will be updated...'.format(len_data_to_table[len(data)][1], data[1]))
            self.delete_data(len_data_to_table[len(data)][0], data[0])
        self.__CURSOR.execute("INSERT INTO {} VALUES({});".format(len_data_to_table[len(data)][0], ', '.join(['?'] * len(data))), data)
        self.__CONN.commit()
        self.log_and_print('{} data of {} added into database.'.format(len_data_to_table[len(data)][1], data[1]))

    def update_dump_value(self, ID, col, val):
        try:
            self.__CURSOR.execute('UPDATE dump SET {} = "{}" WHERE id = {};'.format(col, str(val), str(ID)))
            self.__CONN.commit()
        except Exception as e:
            self.__CONN.close()
            raise DatabaseException("Database error while updating dump table: {}.".format(str(e)))

    def delete_data(self, table, ID):
        """Deleting row from table."""
        """Удаление строки из таблицы."""
        if table not in TABLES.keys() or table == 'db_version': # cheking correct input
            raise DatabaseException('Database error while deleting data from database: wrong table (getted {}, must be matches, players or teams).'.format(str(table)))
        if type(ID) == str:
            if ID.isdigit():
                ID = int(ID)
        if type(ID) != int:
            raise DatabaseException("""Database error while deleting data from database: wrong ID (getted {}, must be int).""".format(type(ID)))
        self.__CURSOR.execute('SELECT * FROM {} WHERE id = {};'.format(table, str(ID)))
        data_existing = self.__CURSOR.fetchall()
        if not data_existing:
            raise DatabaseException('Database error while deleting data from database: ID not found ({}).'.format(str(ID)))
        self.__CURSOR.execute('DELETE FROM {} WHERE id = {};'.format(table, str(ID)))
        self.__CONN.commit()

    def get_upcoming_matches_short(self):
        """Getting the short data of upcoming matches."""
        """Получение короткой информации предстоящих матчей."""
        self.__CURSOR.execute('SELECT id, title, date, tournament, format, url, status FROM matches WHERE status != "Match over" AND status != "Teams unknown" ORDER BY date;')
        return self.__CURSOR.fetchall()

    def get_upcoming_matches_full(self):
        """Getting the short data of upcoming matches."""
        """Получение короткой информации предстоящих матчей."""
        self.__CURSOR.execute('SELECT * FROM matches WHERE status = "Match upcoming" ORDER BY date;')
        return self.__CURSOR.fetchall()

    def get_dump_upcoming_matches(self):
        """Getting the data of upcoming matches."""
        """Получение информации предстоящих матчей."""
        self.__CURSOR.execute('SELECT * FROM dump WHERE status = "Match upcoming" ORDER BY date;')
        return tuple(self.__CURSOR.fetchall())

    def get_upcoming_matches_both_teams_unknown(self):
        """Getting the short data of upcoming matches where both teams unknown."""
        """Получение короткой информации предстоящих матчей где обе команды неизвестны."""
        self.__CURSOR.execute('SELECT id, title, date, tournament, format, url FROM matches WHERE status = "Teams unknown" ORDER BY date;')
        return tuple(self.__CURSOR.fetchall())

    def get_upcoming_match(self, ID):
        """Getting the data of upcoming match."""
        """Получение информации о предстоящем матче."""
        if type(ID) == str:
            if ID.isdigit():
                ID = int(ID)
        if type(ID) != int:
            raise DatabaseException("""Database error while deleting data from database: wrong ID (getted {}, must be int).""".format(type(ID)))
        self.__CURSOR.execute('SELECT * FROM matches WHERE id = {};'.format(str(ID)))
        return self.__CURSOR.fetchall()[0]

    def get_team(self, ID):
        """Getting the data of team."""
        """Получение информации о команде."""
        if type(ID) == str:
            if ID.isdigit():
                ID = int(ID)
        if type(ID) != int:
            raise DatabaseException("""Database error while deleting data from database: wrong ID (getted {}, must be int).""".format(type(ID)))
        self.__CURSOR.execute('SELECT * FROM teams WHERE id = {};'.format(ID))
        return self.__CURSOR.fetchall()[0]

    def get_player(self, ID):
        """Getting the data of player."""
        """Получение информации об игроке."""
        if type(ID) == str:
            if ID.isdigit():
                ID = int(ID)
        if type(ID) != int:
            raise DatabaseException("""Database error while deleting data from database: wrong ID (getted {}, must be int).""".format(type(ID)))
        self.__CURSOR.execute('SELECT * FROM players WHERE id = {};'.format(ID))
        return self.__CURSOR.fetchall()[0]

    def get_players_short(self):
        """Getting the short data of players."""
        """Получение короткой информации об игроках."""
        self.__CURSOR.execute('SELECT id, player, current_team, url FROM players WHERE current_team != "No team" ORDER BY current_team;')
        return tuple(self.__CURSOR.fetchall())

    def update_current_team(self, ID, current_team):
        """Updating current team of player."""
        """Обновление текущей команды игрока."""
        if type(ID) == str:
            if ID.isdigit():
                ID = int(ID)
        if type(ID) != int or type(current_team) != str:
            raise DatabaseException("Database error while changing match URL: wrong input (getted {} and {}, must be int and str).".format(type(ID), type(current_team)))
        self.__CURSOR.execute('SELECT id FROM players WHERE id = {};'.format(str(ID)))
        player = self.__CURSOR.fetchall()
        if not player:
            raise DatabaseException('Database error while updating current team of player: ID "{}" not found).'.format(str(ID)))
        self.__CURSOR.execute('UPDATE players SET current_Team = "{}" WHERE id = {};'.format(current_team, str(ID)))
        self.__CONN.commit()

    def get_date_last_update(self, ID, table=''):
        if type(ID) == str:
            if ID.isdigit():
                ID = int(ID)
        if type(ID) != int or type(table) != str:
            raise DatabaseException("Database error while getting date last update: wrong input (getted {} and {}, must be int and str).".format(type(ID), type(table)))
        if table not in ('teams', 'players'):
            raise DatabaseException('Database error while getting date last update: wrong input (table must be "teams" or "players", getted "{}").'.format(table))
        self.__CURSOR.execute('SELECT date_last_update FROM {} WHERE id = {};'.format(table, str(ID)))
        date_last_update = self.__CURSOR.fetchall()
        if date_last_update:
            return date_last_update[0][0]
        else:
            return datetime.isoformat(datetime.fromtimestamp(0), sep=' ')

    def get_date_last_played_match(self, ID, obj=''):
        if type(ID) == str:
            if ID.isdigit():
                ID = int(ID)
        if type(ID) != int or type(obj) != str:
            raise DatabaseException("Database error while getting date last update: wrong input (getted {} and {}, must be int and str).".format(type(ID), type(table)))
        if obj not in ('team', 'player'):
            raise DatabaseException('Database error while getting date last update: wrong input (table must be "teams" or "players", getted "{}").'.format(table))
        if obj == 'player':
            self.__CURSOR.execute('SELECT date FROM matches WHERE (team_1_players_ids LIKE "% {0},%" OR team_1_players_ids LIKE "{0},%" OR team_1_players_ids LIKE "% {0}" OR team_2_players_ids = "% {0},%" OR team_2_players_ids LIKE "{0},%" OR team_2_players_ids LIKE "% {0}") AND Status = "Match over" ORDER BY date DESC;'.format(str(ID)))
        else:
            self.__CURSOR.execute('SELECT date FROM matches WHERE (team_1_id = {0} OR team_2_id = {0}) AND Status = "Match over" ORDER BY date DESC;'.format(str(ID)))
        dates = self.__CURSOR.fetchall()
        if dates:
            return dates[0][0]
        else:
            return datetime.isoformat(datetime.fromtimestamp(0), sep=' ')
