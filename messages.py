greeting=("Hello! I am the OPGG BOT. I provide statistics on a given player\'s performance through the site OP.GG. "  
         "Please provide a username for me to look up by typing `!opgg <username>`. By default, I search the NA server. "  
         "You may specify a different server by doing including `!server <server>` anywhere after the initial `!opgg` keyword.")

server_arg_missing="Usage: `!server <server>`"

goodbye="Goodbye!"

development="DEVELOPMENT MODE BOT SAYS:\n"

no="You aren't the boss of me!"

def command_not_recognized(command):
    return "Command not recognized: `" + command + "`"

def server_not_found(servername):
    return "This server does not exist: `" + servername + "`"

def user_not_found(username, servername):
    return "Username `"  + username + "` cannot be found on the `" + servername + "` server."
