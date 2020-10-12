English:

Introduction

This parser loads data about upcoming matches from the site HLTV.org, as well as statistics of teams and players participating in it. The parser 
stores match data in the DB file specified in the settings.cfg file. The parser is able to update all this data, including if the match is over or 
postponed.

Dependencies

to run this parser, you will need additional modules in addition to Python itself:
1. fake_useragent
2. BeautifulSoup
To install these modules, you can enter the following commands in the console:
Windows:
pip install fake-useragent
pip install beautifulsoup4
Linux:
pip3 install fake-useragent
pip3 install beautifulsoup4

How do I launch it?
Use the python command run_parcer.py (Windows) or python3 run_parcer.py (Linux), located in the folder where the parser was downloaded.

How does it work?
1. the Parser imports settings from the settings.cfg file (more about settings later).
2. checking the proxy health, if they are specified.
3. Download the list of upcoming matches from https://www.hltv.org/matches
4. next, the Parser divides its work into 6 steps:
4.1. Updating matches that are already recorded in the database.
4.2. Adding new matches to the database.
4.3. Loading statistics of teams participating in uploaded and updated matches.
4.4. Loading statistics of players participating in uploaded and updated matches.
4.5. Checking the current team of players (whether they are part of this team).
4.6. Create "impressions" of new games.

How do I view the data?
So far, the parser does not have functionality for viewing uploaded data, so use any available SQLite browser to view this data.

What are the settings in settings.cfg?
1. db_filename - the name of the database file. All uploaded data is written to this file. If there is no file in the folder, the parser will 
create a new empty file.
2. auto_mode - initially it was a mode for catching bugs, but now it only plays the role of "run and watch". If you disable this feature,
the parser will ask you to continue loading every time it loads any information. I recommend that you leave this feature enabled.
3. log_add_mode - the parser keeps a log for each of its actions, but this log can be very large, especially after updating the database from the 
previous version (in my case, it took >100MB). If this function is disabled, the parser will overwrite the log file every time it starts. If 
enabled, the parser will add logging to the end of the file. I recommend disabling this feature, as the log file size may be very large.
4. log_namefile is the name of the log file. All parser logs are written to this file. If there is no file in the folder, the parser will create a 
new empty file.
5. proxy_mode - the parser can load data via a proxy server. This can avoid banning the IP address of the machine where the parser is running, but 
at the same time it can significantly slow down the parser. In the line below, there are square brackets that indicate the IP addresses of proxy 
servers separated by commas, through which the parser will load data. The parser will choose the fastest one and work through it. If you enable 
this feature, please make sure that the proxies you enter work stably, are not banned from HLTV, are fast, and support HTTPS. If the parser finds 
that proxy servers do not work, it will automatically disable the proxy_mode setting and will work from the IP address of the machine where parser 
is running.
6. download_html_count_retries - number of attempts to download data. If you specified a proxy, it is recommended to specify the number 20. if not, you can
leave it at 3. You can't specify the number of attempts more than 20.
7. List of map settings - here you can specify the current maps that CS:GO tournaments are currently played on. The parser will not load data 
about maps that are set to False in the settings.

What's next?
I can never say exactly what will be in the new version, but I can say for sure that I will update it every 2-3 months.



Русский:

Вступление

Даныый парсер загружает данные о предстоящих матчах с сайта HLTV.org, а так же статистику команд и игроков, участвующих в нём. Парсер хранит данные
о матчах в файле БД, указанной в файле settings.cfg. Парсер способен обновлять все эти данные, в том числе если матч окончен или отложен.

Зависимости

Для запуска данного парсера вам потребуется помимо самого Python дополнительные модули:
1. fake_useragent
2. BeautifulSoup
Чтобы установить эти модули, можно прописать в консоли команды: 
Windows:
pip install fake-useragent
pip install beautifulsoup4
Linux:
pip3 install fake-useragent
pip3 install beautifulsoup4

Как запустить?
Используйте команду python run_parcer.py (Windows) или python3 run_parcer.py (Linux), находясь в папке, где скачан парсер.

Как он работает?
1. Парсер импортирует настройки из файла settings.cfg (о настройках позже).
2. Проверка работоспособности прокси, если они указаны.
3. Загрузка списка предстоящих матчей с https://www.hltv.org/matches
4. Далее Парсер разделяет свою работу на 6 шагов:
4.1. Обновление матчей, которые уже записаны в БД.
4.2. Добавление новых матчей в БД.
4.3. Загрузка статистики команд, участвующих в загруженых и обновлённых матчах.
4.4. Загрузка статистики игроков, участвующих в загруженых и обновлённых матчах.
4.5. Проверка текущей команды игроков (являются ли они составом этой команды).
4.6. Создание "слепков" новых матчей.
Важно отметить, что парсер может работать очень долго, особенно если использовать прокси.

Как посмотреть данные?
Пока что парсер не имеет функционала по просмотру загруженных данных, поэтому для просмотра этих данных используйте любой доступный SQLite браузер.

Что за настройки в settings.cfg?
1. db_filename - имя файла БД. В этот файл записываются все загружаемые данные. Если файла в папке нет, парсер создаст новый пустой файл.
2. auto_mode - изначально это был режим для отлова багов, но сейчас он лишь играет роль "запустил и наблюдаешь". Если выключить эту функцию,
парсер будет спрашивать о продолжении загрузки каждый раз, когда он загрузит какую-либо информацию. Рекомендуется оставить эту функцию включенной.
3. log_add_mode - парсер ведёт лог для каждого своего действия, однако этот лог может быть очень большим, особенно после обновления БД с предыдущей
версии (в моём случае он занимал >100MB). Если данная функция выключена, парсер будет перезаписывать лог файл при каждом запуске. Если включить,
то парсер будет добавлять логгирование в конец файла. Рекомендуется выключить эту функцию, так как размер лог файла может оказаться очень большим.
4. log_namefile - имя лог файла. В этот файл записываются все логи парсера. Если файла в папке нет, парсер создаст новый пустой файл.
5. proxy_mode - парсер может загружать данные через прокси сервер. Это может позволить избежать бана IP-адреса машины, где запущен парсер, но в то
же время может сильно замедлить работу парсера. В строке ниже есть квадратные скобки, где указываются IP-адреса прокси серверов через запятую, 
через которые парсер будет загружать данные. Парсер выберет самый быстрый и будет работать через него. Если вы включаете эту функию, пожалуйста, 
убедитесь, что вводимые вами прокси работают стабильно, не забанены на HLTV, быстрые и поддерживают HTTPS. Если парсер обнаружит, что 
прокси-сервера не работают, он автоматически выключит настройку proxy_mode и будет работать с IP-адреса машины, где запущен парсер.
6. download_html_count_retries - количество попыток для загрузки данных. Если вы указали прокси, рекомендуется указать число 20, если нет - можете
оставить на 3. Вы не сможете указать число попыток больше, чем 20.
7. Список настроек карт - здесь вы указываете актуальные карты, на которых играются в данный момент времени турниры по CS:GO. Парсер не будет
загружать данные о картах, которые в настройках заданы как False.

Что будет дальше?
Я никогда не могу сказать точно что будет в новой версии, но точно могу сказать, что я буду его обновлять каждые 2-3 месяца.