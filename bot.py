import discord
import messages
import requests
import tabulate
import os
import sys
import time
from bs4 import BeautifulSoup
import math
import numpy

tabulate.MIN_PADDING = 0
from tabulate import tabulate

discord_api_key = "NjcwNDY1NDA4MzQ3Nzk5NTgy.XjH-4A.5ihcbTXn4-KBzZjBUMuhGAGc6No"
DEVELOPMENT_MODE = True
server_list = ["na", "euw", "eune", "ru", "kr", "lan", "oce", "br", "las", "tr", "cn", "jp"]
version = "1.4.2"
author = "Me Too Thanks#7924"
bot_id = "OPGG BOT#7083"

ordinal = lambda n: "%d%s" % (n, "tsnrhtdd"[(math.floor(n / 10) % 10 != 1) * (n % 10 < 4) * n % 10::4])


def argsort(my_array):
    array = numpy.array(my_array)
    order = array.argsort()
    return order.argsort()


async def process_commands(selfie, text_words, message):
    resp = {'server_name': "na", 'latest': False}
    indices_to_delete = []
    for i in range(len(text_words)):
        if text_words[i] == '!server':
            if i + 1 == len(text_words):
                await message.channel.send(messages.server_arg_missing)
                return None
            resp['server_name'] = text_words[i + 1]
            if not resp['server_name'] in server_list:
                await message.channel.send(messages.server_not_found(server_name))
                return None
            indices_to_delete.append(i + 1)
            indices_to_delete.append(i)
        elif text_words[i] == '!shutdown':
            if str(message.author) == author:
                await message.channel.send(messages.goodbye)
                await selfie.close()
            else:
                await message.channel.send(messages.no)
            return None
        elif text_words[i] == '!version':
            await message.channel.send("`Version: " + version + "`")
            return None
        elif text_words[i] == '!latest':
            resp['latest'] = True
            indices_to_delete.append(i)
        elif text_words[i][0] == '!':
            await message.channel.send(messages.command_not_recognized(text_words[i]))
            return None
    for index in sorted(indices_to_delete, reverse=True):
        del text_words[index]
    resp['user_name'] = ''.join(text_words)
    resp['pretty'] = ' '.join(text_words)
    return resp


def fetch_game_detail_soup(soup, match_detail_url_1, match_detail_url_2):
    game_id = str(soup.find(class_="GameItem")['data-game-id'])
    game_time = str(soup.find(class_="GameItem")['data-game-time'])
    match_detail_url = match_detail_url_1 + game_id + match_detail_url_2 + game_time
    match_detail_resp = requests.get(match_detail_url)
    match_detail_soup = BeautifulSoup(match_detail_resp.text, "html.parser")
    return match_detail_soup


def generate_team_table(team, match_detail_soup):
    if team == 1:
        my_slice = slice(0, 5, 1)
    else:
        my_slice = slice(5, 10, 1)
    sum_names_div = match_detail_soup.findAll("td", class_="SummonerName Cell")
    score_items_div = match_detail_soup.findAll("div", class_="OPScore Text")
    cs_div = match_detail_soup.findAll("td", class_="CS Cell")
    damage_div = match_detail_soup.findAll("div", class_="ChampionDamage")
    pinks_div = match_detail_soup.findAll("span", class_="SightWard")
    headers = ["Summoner", "OPGG", "CS", "Damage", "Pinks"]
    res = [headers]
    for i, j, k, l, m in zip(sum_names_div[my_slice], score_items_div[my_slice],
                             cs_div[my_slice], damage_div[my_slice], pinks_div[my_slice]):
        new_row = [i.find('a').get_text(),
                   j.get_text(),
                   k.find("div", class_="CS").get_text(),
                   l.get_text(),
                   m.get_text()]
        res.append(new_row)
    table_str = tabulate(res, headers="firstrow", tablefmt="fancy_grid", numalign="left")
    return table_str


def generate_latest_game_string(soup, match_detail_url_1, match_detail_url_2):
    game_history = soup.find_all(class_="GameItemWrap", limit=10)
    match_detail_soup = fetch_game_detail_soup(game_history[0], match_detail_url_1, match_detail_url_2)
    table_ally = generate_team_table(1, match_detail_soup)
    table_enemy = generate_team_table(2, match_detail_soup)
    development_str = "DEVELOPMENT MODE:\n" if DEVELOPMENT_MODE else ""

    print(match_detail_soup.findAll("table", class_="GameDetailTable")[0].get_text())
    ally_win_msg = "Victory" if "Victory" in match_detail_soup.findAll(
        "table", class_="GameDetailTable")[0].get_text() else "Defeat"
    ally_color = " (Blue Team)\n" if "(Blue Team)" in match_detail_soup.findAll(
        "table", class_="GameDetailTable")[0].get_text() else " (Red Team)\n"
    enemy_color = " (Red Team)\n" if ally_color == " (Blue Team)\n" else " (Blue Team)\n"
    opposite_win_msg = "Victory" if ally_win_msg == "Defeat" else "Defeat"
    final_string = '```\n' + development_str + \
                   ally_win_msg + ally_color + table_ally + \
                   "\n\n" + \
                   opposite_win_msg + enemy_color + table_enemy + "```"
    return final_string


def generate_match_history_string(soup, match_detail_url_1, match_detail_url_2):
    user_name_on_opgg = soup.find(class_="Name").string
    game_history = soup.find_all(class_="GameItemWrap", limit=10)
    game_modes, victory_or_defeat, kdas, kp, score, champion, rank = [], [], [], [], [], [], []
    for el in game_history:
        match_detail_soup = fetch_game_detail_soup(el, match_detail_url_1, match_detail_url_2)
        game_mode_str = el.find(class_="GameType").string.split()[0]
        game_mode_str = "Norm" if (game_mode_str == "Normal") else game_mode_str
        game_mode_str = "Solo" if (game_mode_str == "Ranked") else game_mode_str
        game_modes.append(game_mode_str)
        champion.append(el.find(class_="ChampionName").find('a').get_text())
        victory_or_defeat.append("Loss" if (el.find(class_="Win") is None) else "Win")
        kdas.append(el.find("span", class_="KDARatio").string.split()[0][0:4])
        kp.append(el.find("div", class_="CKRate").string.split()[1])
        sum_names = match_detail_soup.findAll("td", class_="SummonerName Cell")
        score_items = match_detail_soup.findAll("div", class_="OPScore Text")
        if len(score_items) is 0:
            score.append("N/A")
            rank.append("N/A")
        else:
            other_scores = []
            my_score_index = -1
            for i in range(10):
                other_scores.append(float(score_items[i].get_text()))
                if sum_names[i].find('a').get_text() == user_name_on_opgg:
                    my_score_index = i
                    score.append(score_items[i].get_text())
            ranks = argsort(other_scores)
            if my_score_index != -1:
                rank.append(str(ordinal(10 - ranks[my_score_index])))
            else:
                rank.append("N/A")
    res = [[i, j, k, l, m, n, o] for i, j, k, l, m, n, o in
           zip(game_modes, victory_or_defeat, champion, kdas, kp, score, rank)]
    headers = ["Game", "Result", "Champion", "KDA", "KP", "OPGG", "Rank"]
    res.insert(0, headers)
    development_str = "DEVELOPMENT MODE:\n" if DEVELOPMENT_MODE else ""
    table_str = tabulate(res, headers="firstrow", tablefmt="fancy_grid", numalign="left")
    final_string = '```\n' + development_str + 'STATS FOR ' + user_name_on_opgg + ":\n" + table_str + "```"
    return final_string


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

    async def on_reaction_add(self, reaction, user):
        if DEVELOPMENT_MODE and not (reaction.message.channel.guild.id == 670463741082730498):
            return
        if str(reaction.message.author) == bot_id:
            # await reaction.message.channel.send("You reacted to my message!")
            pass
        return

    async def on_message(self, message):
        if DEVELOPMENT_MODE and not (message.channel.guild.id == 670463741082730498):
            return
        text_words = message.content.split()
        num_words = len(text_words)
        if len(text_words) and '!opgg' == text_words[0]:
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
            bot_loading_msg = await message.channel.send(messages.loading)
            refresh_button = soup.find(class_="GameListContainer")
            summoner_id = refresh_button['data-summoner-id']
            refresh_url = "https://" + server_name + ".op.gg/summoner/ajax/renew.json/"
            form_data = {"summonerId": summoner_id}
            resp = requests.post(refresh_url, form_data)
            refresh_url2 = "https://" + server_name + ".op.gg/summoner/ajax/renewStatus.json/"
            try:
                # If we have an error renewing, then this summoner was renewed recently.
                # Proceed assuming that their data is accurate
                while not resp.json()['finish']:
                    time.sleep(.2)
                    resp = requests.post(refresh_url2, form_data)
            except ValueError:
                pass
            r = requests.get(url)
            soup = BeautifulSoup(r.text, "html.parser")
            user_name_on_opgg = soup.find(class_="Name").string
            game_history = soup.find_all(class_="GameItemWrap", limit=10)
            if len(game_history) == 0:
                await bot_loading_msg.delete()
                await message.channel.send("`" + user_name_on_opgg + "` has not played any games recently")
                return
            match_detail_url_1 = "https://" + server_name + ".op.gg/summoner/matches/ajax/detail/gameId="
            match_detail_url_2 = "&summonerId=" + str(summoner_id) + "&gameTime="

            if respy['latest']:
                final_string = generate_latest_game_string(soup, match_detail_url_1, match_detail_url_2)
            else:
                final_string = generate_match_history_string(soup, match_detail_url_1, match_detail_url_2)

            await bot_loading_msg.delete()
            await message.channel.send(final_string)
            return


def main():
    client = MyClient()
    client.run(discord_api_key)


if __name__ == "__main__":
    main()
