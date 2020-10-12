from class_Parcer import *

start_time = time.time()
try:
    parcer = Parcer()
    parcer.download_matches()
    parcer.download_teams()
    parcer.download_players()
    parcer.check_current_team_of_players()
    parcer.dump_matches()
except Exception as e:
    program = Program('settings.cfg', error_run=True)
    if Program.loading_progress['enable_in_print']:
        program.close_progress_bar()
    if str(e) in ('Start cancelled.', 'Database update cancelled by user.', 'User stopped parcer.'):
        program.log_and_print(str(e))
    else:
        program.log_and_print('Parcer getted error: {}'.format(str(e)))
else:
    work_time = time.gmtime(time.time() - start_time)
    str_time = ''
    if work_time.tm_hour != 0:
        str_time += ' %s hours' % work_time.tm_hour
    if work_time.tm_min != 0:
        str_time += ' %s minutes' % work_time.tm_min
    if work_time.tm_sec != 0:
        str_time += ' %s seconds' % work_time.tm_sec
    parcer.log_and_print('Parcer worked{}.'.format(str_time))
