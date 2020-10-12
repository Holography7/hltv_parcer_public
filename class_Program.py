from bs4 import BeautifulSoup
import requests
from fake_useragent import UserAgent # pip install fake-useragent
import time
from datetime import datetime
from datetime import date
from datetime import timedelta
import os

class ProgramException(Exception):
    pass

class Program():
    user_agent = UserAgent().chrome
    source_urls = ('https://www.hltv.org', '/matches', '/stats/players', '/team', '?startDate=', '&endDate=')
    settings = {'db_filename': 'hltv_compact.db', 'auto_mode': True, 'log_add_mode': 'w', 'log_namefile': 'parcer.log', 'proxy_mode': False, 'download_html_count_retries': 3, 'cache': False, 'cobblestone': False, 'dust2': True, 'inferno': True, 'mirage': True, 'nuke': True, 'overpass': True, 'season': False, 'train': True, 'tuscan': False, 'vertigo': True}
    proxies = {}
    faster_proxy = None
    loading_progress = {'message': None, 'loading_points': 0, 'max_loading_points': 0, 'enable_in_print': False} # data for prograss bar.

    def __init__(self, config_namefile, error_run=False):
        """Importing settings."""
        """Импортирование настроек."""
        if not error_run:
            imported_settings = {'db_filename': False, 'auto_mode': False, 'log_add_mode': False, 'log_namefile': False, 'proxy_mode': False, 'download_html_count_retries': False, 'cache': False, 'cobblestone': False, 'dust2': False, 'inferno': False, 'mirage': False, 'nuke': False, 'overpass': False, 'season': False, 'train': False, 'tuscan': False, 'vertigo': False}
            try:
                with open(config_namefile) as config_file: # Reading config file
                    for line in config_file:
                        if line[0] == '#' or line == '\n': # Comment line is passing
                            continue
                        elif line[0] == '[' and Program.settings['proxy_mode']:
                            proxies = line[1:-2]
                            Program.proxies = {proxy.strip(): 0 for proxy in proxies.split(',')}
                            continue
                        try:
                            setting = line[:line.index('=')].lower()
                            if setting in Program.settings.keys(): # Reading setting in line
                                value = line[line.index('=') + 1:line.index('\n')] # Reading value of setting in line if exist
                                if value == 'True': # Convert str into bool or int
                                    value = True
                                elif value == 'False':
                                    value = False
                                elif value.isdigit():
                                    value = int(value)
                                Program.settings[setting] = value # Saving setting
                                imported_settings[setting] = True # Setting marking as was read
                        except ValueError: # Line without "=" passing
                            continue
            except Exception as e: # Some errors while reading file
                raise ProgramException('Program error while importing config: {}.'.format(e))
            else:
                for key in Program.settings.keys(): # Cheking for correct values of settings
                    if key == 'db_filename':
                        if type(Program.settings[key]) != str:
                            raise ProgramException('Program error while importing config: wrong type input in "db_filename" (must be str, getted {}).'.format(type(Program.settings[key])))
                    elif key == 'log_namefile':
                        if not os.path.isfile(Program.settings[key]):
                            with open(Program.settings[key], 'w', encoding='utf-8') as log_file:
                                log_file.write('Log file initialized {}'.format(datetime.now().replace(microsecond=0).isoformat(' ')))
                    elif key == 'download_html_count_retries':
                        if type(Program.settings[key]) != int:
                            raise ProgramException('Program error while importing config: value of setting "{}" is not digit (getted "{}").'.format(key, Program.settings[key]))
                    elif key in ('auto_mode', 'log_add_mode', 'cache', 'cobblestone', 'dust2', 'inferno', 'mirage', 'nuke', 'overpass', 'season', 'train', 'tuscan', 'vertigo'):
                        if type(Program.settings[key]) != bool:
                            raise ProgramException('Program error while importing config: value of setting "{}" is not bool (getted "{}").'.format(key, Program.settings[key]))
                if Program.settings['log_add_mode']: # Additional interpretation of the log_add_mode setting
                    Program.settings['log_add_mode'] = 'a' # If True, logging will from end of log file
                else:
                    Program.settings['log_add_mode'] = 'w' # Else past log will clean
                # Start logging
                with open(Program.settings['log_namefile'], Program.settings['log_add_mode'], encoding='utf-8') as log_file:
                    log_file.write(datetime.now().replace(microsecond=0).isoformat(' ') + '\t\t' + '-' * 128 + '\n')
                    log_file.write(datetime.now().replace(microsecond=0).isoformat(' ') + '\t\t' +'Config imported.\n')
                print('Config imported.')
                self.config_imported = True # Using only for testing
                if Program.settings['download_html_count_retries'] > 20: # Additional interpretation of the download_html_count_retries setting
                    Program.settings['download_html_count_retries'] = 20 # Max count retries of download HTML is 20
                    with open(Program.settings['log_namefile'], 'a', encoding='utf-8') as log_file:
                        log_file.write(datetime.now().replace(microsecond=0).isoformat(' ') + '\t\t' + 'Warning: download_html_count_retries more than 20. Count set to 20.\n')
                    print('Warning: download_html_count_retries more than 20. Count set to 20.')
                if False in imported_settings.values(): # Warning if some settings wasn't imported (not marked in imported_settings)
                    with open(Program.settings['log_namefile'], 'a', encoding='utf-8') as log_file:
                        log_file.write(datetime.now().replace(microsecond=0).isoformat(' ') + '\t\t' + 'Warning: some settings in config file "{}" not founded. This settengs using default values:\n'.format(config_namefile))
                    print('Warning: some settings in config file "{}" not founded. This settengs using default values:'.format(config_namefile))
                    for key in imported_settings.keys():
                        if imported_settings[key] == False:
                            with open(Program.settings['log_namefile'], 'a', encoding='utf-8') as log_file:
                                log_file.write(datetime.now().replace(microsecond=0).isoformat(' ') + '\t\t' + '{}={}\n'.format(key, Program.settings[key]))
                            print('{}={}'.format(key, Program.settings[key]))

    def log_and_print(self, input_string, write_mode='a', do_print=True, do_log=True, input_by_user=False, answer=False):
        """Print text and write in log file."""
        """Вывод текста и запись его в лог файл."""
        if 'str_to_log' in dir(input_string):
            input_string.str_to_log = True
            input_string_to_log = '\n' + str(input_string)
            input_string.str_to_log = False
            input_string = str(input_string)
        else:
            input_string_to_log = str(input_string)
            input_string = str(input_string)
        if do_print:
            if Program.loading_progress['enable_in_print']:
                print('\r' + ' ' * len('{} |██████████████████████████████████████████████████| 100.00% [{}/{}]'.format(Program.loading_progress['message'], str(Program.loading_progress['loading_points']), str(Program.loading_progress['max_loading_points']))), end='') # clear previos progress bar
                if input_by_user:
                    print('\r' + '[{}/{}] '.format(str(Program.loading_progress['loading_points']), str(Program.loading_progress['max_loading_points'])) + input_string, end='')
                else:
                    print('\r' + input_string) # print input string
                    print('\r{} |{}| {}% [{}/{}]'.format(Program.loading_progress['message'], '█' * int(Program.loading_progress['loading_points'] / Program.loading_progress['max_loading_points'] * 100 // 4) + ' ' * (25 - int(Program.loading_progress['loading_points'] / Program.loading_progress['max_loading_points'] * 100 // 4)), str(round(Program.loading_progress['loading_points'] / Program.loading_progress['max_loading_points'] * 100, 2)), str(Program.loading_progress['loading_points']), str(Program.loading_progress['max_loading_points'])), end='') # print progress bar
            else:
                if input_by_user:
                    print(input_string, end='')
                else:
                    print(input_string)
        if do_log:
            try:
                with open(Program.settings['log_namefile'], write_mode, encoding='utf-8') as log_file:
                    log_file.write('{}\t\t{}\n'.format(datetime.now().replace(microsecond=0).isoformat(' '), input_string_to_log))
            except Exception as e:
                raise ProgramException('Program error while logging: {}.'.format(e))

    def init_progress_bar(self, message, max_loading_points):
        if type(max_loading_points) != int:
            raise ProgramException('Program error while initialization progress bar: max_loading_points is not int (getted "{}").'.format(type(max_loading_points)))
        Program.loading_progress['message'], Program.loading_progress['max_loading_points'], Program.loading_progress['enable_in_print'] = str(message), max_loading_points, True

    def close_progress_bar(self):
        print('\r' + ' ' * len('{} |██████████████████████████████████████████████████| 100.00% [{}/{}]'.format(Program.loading_progress['message'], str(Program.loading_progress['loading_points']), str(Program.loading_progress['max_loading_points']))), end='')
        Program.loading_progress['message'], Program.loading_progress['loading_points'], Program.loading_progress['max_loading_points'], Program.loading_progress['enable_in_print'] = None, 0, 0, False
        print('\r', end='')

    def download_html(self, url):
        for i in range(Program.settings['download_html_count_retries']): # Max 20 retries
            time.sleep(1) # Necessary delay between downloads
            try: # Downloading HTML
                if Program.settings['proxy_mode']:
                    req = requests.get(url, headers={'User-Agent': Program.user_agent}, proxies={'https': 'https://' + Program.faster_proxy}, timeout=60)
                else:
                    req = requests.get(url, headers={'User-Agent': Program.user_agent}, timeout=60)
            except requests.Timeout as e:
                self.log_and_print('Error: timed out.')
                self.log_and_print(str(e))
            except requests.exceptions.ProxyError as e:
                self.log_and_print('Error: proxy temporarily unavailable.')
                self.log_and_print(str(e))
            except requests.exceptions.ConnectionError as e:
                self.log_and_print('Error: failed connect to proxy.')
                self.log_and_print(str(e))
            except (requests.exceptions.ChunkedEncodingError, requests.exceptions.ReadTimeout) as e:
                self.log_and_print('Error: getted HTML, but reading failed.')
                self.log_and_print(str(e))
            except (Exception, BaseException) as e:
                self.log_and_print("Unknown error while downloading HTML: {}.".format(str(e)))
            except:
                self.log_and_print("Unknown error while downloading HTML.")
            else: # return BS if download is successful
                if req.status_code == 200:
                    return BeautifulSoup(req.text, 'html.parser')
                else:
                    self.log_and_print('Error {} while uploading {} (HTML-error).'.format(str(req.status_code), url))
            if i != Program.settings['download_html_count_retries'] - 1: # Message of re-download
                Program.user_agent = UserAgent().chrome
                self.log_and_print("Attempt to re-download HTML (retries {} remain).".format(Program.settings['download_html_count_retries'] - i - 1))
        raise ProgramException('Program error while downloading HTML "{}": ended attempts to re-download.'.format(url)) # When retries of download is ended

    def get_id_from_url(self, *urls):
        """Getting an ID from a URL."""
        """Получение ID из URL."""
        if len(urls) == 1: # Unpack urls if it's getted as any array
            if type(urls[0]) == list or type(urls[0]) == tuple or type(urls[0]) == set:
                urls == urls[0]
        elif len(urls) == 0: # Or throw exception if it's empty
            raise ProgramException('Program error while getting ID from URL: getted noting.')
        prev_path = ('matches', 'players', 'player', 'team') # This paths must be before ID in URL
        IDs = []
        for url in urls: # Getting ID from URL
            try:
                parts = url.split('/')
            except AttributeError: # If url not a str
                raise ProgramException('Program error while getting ID from URL: getted not str (getted "{}").'.format(type(url)))
            if len(parts) == 1: # If url doesn't contain any symbol '/'
                raise ProgramException('Program error while getting ID from URL: URL must have at least 1 symbol "/" (getted "{}").'.format(url))
            prev = 'https' # Just initialization previos path
            for i in parts: # Searching ID in parts of URL
                ID_getted = False
                if i.isdigit():
                    if prev in prev_path: # Cheking that previous path in prev_path
                        IDs.append(int(i)) # Adding ID in list
                        ID_getted = True
                        break
                    else:
                        raise ProgramException('Program error while getting ID from URL: URL must be from HLTV.org, this URL is unknown ("{}").'.format(url))
                prev = i
            if not ID_getted:
                raise ProgramException('Program error while getting ID from URL: ID not founded in URL "{}".'.format(url))
        if len(IDs) == 1: # If getted only 1 URL
            return IDs[0]
        else: # Or some URLs
            return tuple(IDs)

    def question(self, question_message, default_answer=True):
        """Method for asking questions to the user."""
        """Метод для задавания вопросов пользователю."""
        if type(question_message) != str:
            raise ProgramException('Program error while question: question is not str (getted "{}").'.format(type(question_message)))
        answers = {'y': True, 'n': False, '': default_answer}
        while(True):
            self.log_and_print(question_message, input_by_user=True)
            answer = input().lower()
            if answer in answers.keys():
                self.log_and_print('User types "{}"'.format(answer), do_print=False)
                return answers[answer]
            else:
                self.log_and_print('Wrong answer. Try again.')

    def str_pseudo_table(self, *rows, orientation='row', to_log=False, title=None): # if needed print Team, MapStats or Player objects
        if len(rows) == 0: # checking correct input
            raise ProgramException('Program error while creating pseudo-table: empty input.')
        for row in rows:
            if type(row) not in (list, tuple, set): # checking correct input
                raise ProgramException('Program error while creating pseudo-table: wrong input (getted "{}" as "{}").'.format(str(row), type(row)))
        if orientation not in ('row', 'rows', 'col', 'cols', 'column', 'columns'):
            raise ProgramException('Program error while creating pseudo-table: wrong input orientation (getted "{}", must be ("row", "rows", "col", "cols", "column", "columns")).'.format(str(orientation)))
        if type(to_log) != bool:
            raise ProgramException("""Program error while creating pseudo-table: wrong input to_log (getted "{}", must be "{}").""".format(type(to_log), type(False)))
        if orientation in ('col', 'cols', 'column', 'columns'): # Transpose a table
            rows = [[row[i] for row in rows] for i in range(len(rows[0]))]
        if to_log: # tabs multiplier for log and print
            tabs_multiplier = 4
        else:
            tabs_multiplier = 8
        width_cols = [(max([len(str(row[i])) for row in rows]) // tabs_multiplier + 1) * tabs_multiplier for i in range(len(rows[0]))] # needed to calculate width column
        count_dashes_cols = [width_col - 1 for width_col in width_cols] # count dashes for lines on top, bottom table and between rows
        count_tabs_for_cells = [[width_cols[i] // tabs_multiplier - (len(str(row[i])) + 1) // tabs_multiplier for i in range(len(width_cols))] for row in rows] # tabs for each cell
        place_lines = ('top', 'between', 'bottom') # keys for places lines
        if title: # title cell
            table_in_symbols = (sum(count_dashes_cols) + len(count_dashes_cols) - 1)
            title_line = '┌' + '─' * table_in_symbols + '┐\n'
            title_row = '│' + ' ' * ((table_in_symbols - len(str(title))) // 2) + str(title) + ' ' * ((table_in_symbols - len(str(title))) // 2 + (table_in_symbols - len(str(title))) % 2) + '│\n'
            intersections = {'left': ('├', '├', '└'), 'between': ('┬', '┼', '┴'), 'right': ('┤\n', '┤\n', '┘\n')} # crosses lines of table
        else:
            title_line = ''
            title_row = ''
            intersections = {'left': ('┌', '├', '└'), 'between': ('┬', '┼', '┴'), 'right': ('┐\n', '┤\n', '┘\n')} # crosses lines of table
        lines = {place_lines[i]: intersections['left'][i] + intersections['between'][i].join(['─' * count_dashes_col for count_dashes_col in count_dashes_cols]) + intersections['right'][i] for i in range(3)} # lines table
        rows_in_table = ['│' + '│'.join([str(rows[i][j]) + '\t' * count_tabs_for_cells[i][j] for j in range(len(rows[i]))]) + '│\n' for i in range(len(rows))] # generating rows in table
        table = title_line + title_row + lines['top'] + lines['between'].join(rows_in_table) + lines['bottom'] # generating pseudo-table
        return table
