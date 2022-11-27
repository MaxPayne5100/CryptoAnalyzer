import configparser

config = configparser.ConfigParser()
config.add_section('bot')
config.set('bot', 'token', '5511283383:AAHevZVOhu1rqyM_hasn0OpeMp1WRiwynpI')
config.add_section('azure')
config.set('azure', 'acc_name', 'diplomastorageaccount')
config.set('azure', 'acc_key',
           'G9yeDPq1GG9j7vWhbaqDj2dvqhGOGZpXxX7oEE7zinEvehnVSek2tQftconpKWG7hNbFrpjAhPxH+AStfREzkg==')
with open(r"configfile.ini", 'w') as config_file:
    config.write(config_file)
