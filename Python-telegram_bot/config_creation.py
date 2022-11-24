import configparser

config = configparser.ConfigParser()

config.add_section('bot')
config.set('bot', 'token', '5511283383:AAHgihqMKBIgcf94Im_YXG4VgYTeXtJvNRQ')
with open(r"configfile.ini", 'w') as config_file:
    config.write(config_file)
