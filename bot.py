import discord
import messages
import requests
import os
import time
from bs4 import BeautifulSoup

server_list = ["na", "euw", "eune", "ru", "kr", "lan", "oce", "br", "las", "tr", "cn", "jp"]
DEVELOPMENT_MODE = False
discord_api_key="NjcwNDY1NDA4MzQ3Nzk5NTgy.XjH-4A.5ihcbTXn4-KBzZjBUMuhGAGc6No"

version = "1.2.0"

class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))

    async def on_message(self, message):
        if DEVELOPMENT_MODE and not(message.channel.guild.id == 670463741082730498):
            return
        text_words = message.content.split()
        num_words = len(text_words)
        if '!opgg' ==  text_words[0]:
            if num_words == 1:
                await message.channel.send(messages.greeting)
                return
            text_words.pop(0)
            server_name = "na"
            for i in range(num_words):
                if text_words[i][0] == '!':
                    if text_words[i] == '!server':
                        if i + 1 == num_words:
                            await message.channel.send(messages.server_arg_missing)
                            return
                        server_name = text_words[i + 1]
                        if not server_name in server_list:
                            await message.channel.send(messages.server_not_found(server_name))
                            return
                        text_words.pop(i + 1)
                        text_words.pop(i)
                    elif text_words[i] == '!shutdown':
                        if(str(message.author) == "Me Too Thanks#7924"):
                            await message.channel.send(messages.goodbye)
                            await self.close()
                            return
                        else:
                            await message.channel.send(messages.no)
                            return
                    elif text_words[i] == '!version':
                        await message.channel.send("`Version: " + version + "`")
                        return
                    else:
                        await message.channel.send(messages.command_not_recognized(text_words[i]))
                        return
                url = "https://" + server_name + ".op.gg/summoner/?userName=" + ''.join(text_words)
                r = requests.get(url)
                soup = BeautifulSoup(r.text, 'html.parser')
                if soup.find(class_="Name") is None:
                    await message.channel.send(messages.user_not_found(' '.join(text_words), server_name))
                    return
                refresh_button = soup.find(id="SummonerRefreshButton")
                summoner_id = int(refresh_button['onclick'][39:47])
                refresh_url = "https://" + server_name + ".op.gg/summoner/ajax/renew.json/"
                form_data = {"summonerId": summoner_id}
                requests.post(refresh_url, form_data)
                refresh_url2 = "https://" + server_name + ".op.gg/summoner/ajax/renewStatus.json/"
                while(True):
                    time.sleep(.1)
                    resp = requests.post(refresh_url2, form_data)
                    if resp.json()['finish'] == True:
                        break
                r = requests.get(url)
                soup = BeautifulSoup(r.text, 'html.parser')
                user_name_on_opgg = soup.find(class_="Name").string
                game_history = soup.find_all(class_="GameItemWrap", limit=10)
                gameModes         = [el.find(class_="GameType").string.split()[0] + " "*(6 - len(el.find(class_="GameType").string.split()[0])) for el in game_history]
                victory_or_defeat = ["|Defeat " if (el.find(class_="Win") is None) else "|Victory" for el in game_history]
                kdas =              ["|" + el.find("span", class_="KDARatio").string.split()[0][0:4] for el in game_history]
                kp   =              ["|" + el.find("div", class_="CKRate").string.split()[1] for el in game_history]
                res = [i + j + k + l for i, j, k, l in zip(gameModes, victory_or_defeat, kdas, kp)] 
                myString = '\n'.join(res)
                myDivider="\n" + "-" * 26 + "\n"
                DEV_STR = "DEVELOPMENT MODE:\n" if DEVELOPMENT_MODE else ""
                await message.channel.send('```\n' + DEV_STR + 'STATS FOR ' + user_name_on_opgg + ": " + myDivider + "Game  |Outcome|KDA |KP" + myDivider +  myString + "```")
                return

client = MyClient()
client.run(discord_api_key)
