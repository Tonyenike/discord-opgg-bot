import discord
import messages
import requests
from tabulate import tabulate
import os, sys, time
from bs4 import BeautifulSoup
import math
import numpy

discord_api_key="NjcwNDY1NDA4MzQ3Nzk5NTgy.XjH-4A.5ihcbTXn4-KBzZjBUMuhGAGc6No"
DEVELOPMENT_MODE = True
server_list = ["na", "euw", "eune", "ru", "kr", "lan", "oce", "br", "las", "tr", "cn", "jp"]
version = "1.4.0"
author  = "Me Too Thanks#7924"

ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(math.floor(n/10)%10!=1)*(n%10<4)*n%10::4])

def argsort(myArray):
    array = numpy.array(myArray)
    order = array.argsort()
    return order.argsort()

async def process_commands(selfie, text_words, message):
    resp = {}
    resp['server_name'] = "na"
    for i in range(len(text_words)):
        if text_words[i] == '!server':
            if i + 1 == len(text_words):
                await message.channel.send(messages.server_arg_missing)
                return None
            resp.server_name = text_words[i + 1]
            if not server_name in server_list:
                await message.channel.send(messages.server_not_found(server_name))
                return None
            text_words.pop(i + 1)
            text_words.pop(i)
        elif text_words[i] == '!shutdown':
            if(str(message.author) == author):
                await message.channel.send(messages.goodbye)
                await selfie.close()
            else:
                await message.channel.send(messages.no)
            return None
        elif text_words[i] == '!version':
            await message.channel.send("`Version: " + version + "`")
            return None
        elif text_words[i][0] == '!':
            await message.channel.send(messages.command_not_recognized(text_words[i]))
            return None
    resp['user_name'] = ''.join(text_words)
    resp['pretty'] = ' '.join(text_words)
    return resp


class MyClient(discord.Client):
    
    def __init__(self):
        global DEVELOPMENT_MODE
        if len(sys.argv) == 1:
            DEVELOPMENT_MODE = True
            print("DEVELOPMENT MODE IS ENABLED")
        elif sys.argv[1] == "prod":
            DEVELOPMENT_MODE = False
        super().__init__()
    
    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))

    async def on_message(self, message):
        if DEVELOPMENT_MODE and not(message.channel.guild.id == 670463741082730498):
            return
        text_words = message.content.split()
        num_words = len(text_words)
        if len(text_words) and '!opgg' ==  text_words[0]:
            if num_words == 1:
                await message.channel.send(messages.greeting)
                return
            text_words.pop(0)
            respy = await process_commands(self, text_words, message)
            if respy is None:
                return
            server_name = respy['server_name']
            url = "https://" + server_name + ".op.gg/summoner/?userName=" + respy['user_name']
            r = requests.get(url)
            soup = BeautifulSoup(r.text, 'html.parser')
            if soup.find(class_="Name") is None:
                await message.channel.send(messages.user_not_found(respy['pretty'], server_name))
                return
            refresh_button = soup.find(class_="GameListContainer")
            summoner_id = refresh_button['data-summoner-id']
            refresh_url = "https://" + server_name + ".op.gg/summoner/ajax/renew.json/"
            form_data = {"summonerId": summoner_id}
            resp = requests.post(refresh_url, form_data)
            refresh_url2 = "https://" + server_name + ".op.gg/summoner/ajax/renewStatus.json/"
            try:
                # If we have an error renewing, then this summoner was renewed recently.
                # Proceed assuming that their data is accurate
                while(resp.json()['finish'] == False):
                    time.sleep(.1)
                    resp = requests.post(refresh_url2, form_data)
            except ValueError:
                pass
            r = requests.get(url)
            soup = BeautifulSoup(r.text, "html.parser")
            user_name_on_opgg = soup.find(class_="Name").string
            game_history = soup.find_all(class_="GameItemWrap", limit=10)
            if len(game_history) == 0:
                await message.channel.send("`" + user_name_on_opgg + "` has not played any games recently")
                return
            gameModes, victory_or_defeat, kdas, kp, score, champion, rank = [], [], [], [], [], [], []
            match_detail_url_1 = "https://" + server_name + ".op.gg/summoner/matches/ajax/detail/gameId="
            match_detail_url_2 = "&summonerId=" + str(summoner_id) + "&gameTime="
            for el in game_history:
                game_id = str(el.find(class_="GameItem")['data-game-id'])
                game_time = str(el.find(class_="GameItem")['data-game-time'])
                match_detail_url = match_detail_url_1 + game_id + match_detail_url_2 + game_time
                match_detail_resp = requests.get(match_detail_url)
                match_detail_soup = BeautifulSoup(match_detail_resp.text, "html.parser")
                game_mode_str = el.find(class_="GameType").string.split()[0]
                game_mode_str = "Solo" if (game_mode_str == "Ranked") else game_mode_str
                gameModes.append(game_mode_str)
                champion.append(el.find(class_="ChampionName").find('a').get_text())
                victory_or_defeat.append("Loss" if (el.find(class_="Win") is None) else "Win")
                kdas.append             (el.find("span", class_="KDARatio").string.split()[0][0:4])
                kp.append               (el.find("div", class_="CKRate").string.split()[1])
                sum_names  = match_detail_soup.findAll("td", class_="SummonerName Cell")
                score_items = match_detail_soup.findAll("div", class_="OPScore Text")
                if len(score_items) is 0:
                    score.append("N/A")
                    rank.append("N/A")
                else:
                    other_scores=[]
                    for i in range(10):
                        other_scores.append(float(score_items[i].get_text()))
                        if sum_names[i].find('a').get_text() == user_name_on_opgg:
                            myScoreIndex = i
                            score.append(score_items[i].get_text())
                    ranks = argsort(other_scores)
                    rank.append(str(ordinal(10 - ranks[myScoreIndex]))) 
            res = [[i, j, k, l, m, n, o] for i, j, k, l, m, n, o in zip(gameModes, victory_or_defeat, champion, kdas, kp, score, rank)]
            headers = ["Game", "Result", "Champion", "KDA", "KP", "OPGG", "Rank"]
            res.insert(0, headers)
            development_str = "DEVELOPMENT MODE:\n" if DEVELOPMENT_MODE else ""
            table_str = tabulate(res, headers="firstrow", tablefmt="fancy_grid", numalign="left")
            final_string =  '```\n' + development_str + 'STATS FOR ' + user_name_on_opgg + ":\n" + table_str + "```" 
            await message.channel.send(final_string)
           
            return

def main():
    client = MyClient()
    client.run(discord_api_key)

if __name__ == "__main__":
    main()
