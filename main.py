import math
import os
import re

import khl.requester
import wget
from khl import Bot, Message, MessageTypes, RawMessage
import random
import json
import pandas as pd
import numpy as np


def username_sl(status: str, usernamecache: dict = None):
    if status == 'load':
        fp = open('data/usernamecache.json', 'r', encoding='utf-8')
        data = json.load(fp)
        return data
        fp.close()
    if status == 'save':
        fp = open('data/usernamecache.json', 'w', encoding='utf-8')
        json.dump(usernamecache, fp, ensure_ascii=False)
        fp.close()


def skill_load(begin: int, end: int, sn_col: int, sc_col: int, df: pd.DataFrame, user: dict, userID: str, rn: str):
    for n in range(begin, end):
        sn = str(df[sn_col][n])
        if sn != 'nan':
            sc = df[sc_col][n]
            if sn.find('Ω') != -1:
                sn = sn[:-2]
            if sn.find('：') != -1:
                sn = sn[:-1]
            user[userID]['pc'][rn]['skill'][sn] = sc
        else:
            continue


def role_load(ui: str, rn: str, df: pd.DataFrame, user: dict):
    user[ui]['pc'][rn] = {}
    user[ui]['pc'][rn]['hp'] = [df[6][8], df[6][8]]
    user[ui]['pc'][rn]['san'] = [df[32][1], df[15][8]]
    user[ui]['pc'][rn]['mp'] = [df[24][8], df[24][8]]
    user[ui]['pc'][rn]['attributes'] = {}
    user[ui]['pc'][rn]['attributes']['str'] = int(df[20][1])
    user[ui]['pc'][rn]['attributes']['con'] = int(df[20][3])
    user[ui]['pc'][rn]['attributes']['siz'] = int(df[20][5])
    user[ui]['pc'][rn]['attributes']['dex'] = df[26][1]
    user[ui]['pc'][rn]['attributes']['app'] = df[26][3]
    user[ui]['pc'][rn]['attributes']['int'] = df[26][5]
    user[ui]['pc'][rn]['attributes']['pow'] = df[32][1]
    user[ui]['pc'][rn]['attributes']['edu'] = df[32][3]
    user[ui]['pc'][rn]['attributes']['luck'] = df[32][5]
    user[ui]['pc'][rn]['skill'] = {}
    skill_load(14, 18, 5, 17, df, user, ui, rn)
    skill_load(18, 21, 7, 17, df, user, ui, rn)
    skill_load(21, 32, 5, 17, df, user, ui, rn)
    skill_load(32, 40, 7, 17, df, user, ui, rn)
    skill_load(40, 44, 5, 17, df, user, ui, rn)
    skill_load(44, 48, 7, 17, df, user, ui, rn)
    skill_load(14, 29, 27, 39, df, user, ui, rn)
    skill_load(29, 32, 29, 39, df, user, ui, rn)
    skill_load(32, 45, 27, 39, df, user, ui, rn)


def init_bot(status: str, bot_settings: dict = None):
    if status == 'load':
        fp = open('data/bot_settings.json', 'r', encoding='utf-8')
        data = json.load(fp)
        fp.close()
        return data
    if status == 'save':
        fp = open('data/bot_settings.json', 'w', encoding='utf-8')
        json.dump(bot_settings, fp, ensure_ascii=False)
        fp.close()


def coc_games_sl(status: str, coc_games: dict = None):
    if status == 'load':
        fp = open('data/coc_games.json', 'r', encoding='utf-8')
        data = json.load(fp)
        fp.close()
        return data
    if status == 'save':
        fp = open('data/coc_games.json', 'w', encoding='utf-8')
        json.dump(coc_games, fp, ensure_ascii=False)
        fp.close()


def Dice(dice_face: int = None, dice_num: int = 1, dice_config: str = None):
    if dice_config is not None:
        dice_num, dice_face = [int(i) for i in dice_config.rsplit('D')]
    dice_point_list = list()
    result = 0
    for i in range(0, dice_num):
        dice_point = random.randint(1, dice_face)
        result += dice_point
        dice_point_list.append(dice_point)
    return result, dice_point_list


def skillDice(skill_num: int, user_id: str, config: str):
    dice = random.randint(1, 100)
    if dice < 5:
        judge = '大成功'
    elif dice < math.floor(skill_num / 2):
        judge = '艰难成功'
    elif dice < skill_num:
        judge = '普通成功'
    elif dice < 95:
        judge = '失败'
    else:
        judge = '大失败'
    output = '(met)' + user_id + '(met)投掷【.ra ' + config + ' ' + str(skill_num) + '】 总结果为' + str(
        dice) + '，检定技能：' + config + ',掷骰1d100=' + str(dice) + ',(ins)' + judge + '(ins)'
    return output


def sanDice(san: int, user_id: str, config: str):
    output = '(met)' + user_id + '(met)投掷【.san ' + config
    output += ' ' + str(san) + '】'
    success, fail = config.rsplit('/')
    if success.find('D') != -1:
        success, cache = Dice(dice_config=success)
    else:
        success = int(success)
    if fail.find('D') != -1:
        fail, cache = Dice(dice_config=fail)
    else:
        fail = int(fail)
    dice_point = random.randint(1, 100)
    if dice_point <= san:
        output += '(ins)理智判定成功'
        if success == 0:
            san_point = 0
            output += '。(ins)'
        else:
            san_point = success
            output += ',理智值降低：' + str(success) + '(ins)'
    else:
        output += '(ins)理智判定失败'
        san_point = fail
        output += ',理智值降低：' + str(fail) + '(ins)'
    output += '(spl)1d100=' + str(dice_point) + '(spl)'
    return san_point, output


attributes_dict = {'力量': 'str', '体质': 'con', '体型': 'siz', '敏捷': 'dex', '外貌': 'app', '智力': 'int', '意志': 'pow',
                   '教育': 'edu', '幸运': 'luck', '灵感': 'int', '知识': 'edu'}
coc_roles = ['GM', 'KP', 'PL']
coc_channel_names = ['_主频道_语音', '_主频道_文字', '_地图', '_KP', '_录卡']
# init Bot
bot = Bot(token=init_bot('load')['token'])


# manage_channel_whitelist dice_whitelist_channel

@bot.command(name='DiceDetect', aliases=['dd'], prefixes=['.'])
async def DiceDetect(msg: Message):
    bot_setting = init_bot('load')
    channel_id = msg.ctx.channel.id
    user_id = msg.author.id
    if user_id in bot_setting['GM'] and channel_id not in bot_setting['dice_whitelist_channel']:
        bot_setting['dice_whitelist_channel'].append(channel_id)
        init_bot('save', bot_setting)
        output = '(met)' + user_id + '(met)该频道已经可以丢骰子了，(ง •_•)ง加油祝各位皆为欧皇'
        await msg.reply(output, use_quote=False)


@bot.command(name='ManageDetect', aliases=['md'], prefixes=['.'])
async def ManageDetect(msg: Message):
    bot_setting = init_bot('load')
    channel_id = msg.ctx.channel.id
    user_id = msg.author.id
    if user_id in bot_setting['GM'] and channel_id not in bot_setting['manage_channel_whitelist']:
        bot_setting['manage_channel_whitelist'].append(channel_id)
        output = '(met)' + user_id + '(met)该频道已经可以创建房间了，(ง •_•)ง加油调查员'
        await msg.reply(output, use_quote=False)
        init_bot('save', bot_setting)


@bot.command(name='DelDiceDetect', aliases=['ddd'], prefixes=['.'])
async def DiceDetect(msg: Message):
    bot_setting = init_bot('load')
    channel_id = msg.ctx.channel.id
    user_id = msg.author.id
    if user_id in bot_setting['GM'] and channel_id in bot_setting['dice_whitelist_channel']:
        bot_setting['dice_whitelist_channel'].pop(bot_setting['dice_whitelist_channel'].index(channel_id))
        init_bot('save', bot_setting)
        output = '(met)' + user_id + '(met)骰娘不再祝福这里。'
        await msg.reply(output, use_quote=False)


@bot.command(name='DelManageDetect', aliases=['dmd'], prefixes=['.'])
async def ManageDetect(msg: Message):
    bot_setting = init_bot('load')
    channel_id = msg.ctx.channel.id
    user_id = msg.author.id
    if user_id in bot_setting['GM'] and channel_id in bot_setting['manage_channel_whitelist']:
        bot_setting['manage_channel_whitelist'].pop(bot_setting['manage_channel_whitelist'].index(channel_id))
        init_bot('save', bot_setting)
        output = '(met)' + user_id + '(met)不会再有调查员遭遇不幸。'
        await msg.reply(output, use_quote=False)


@bot.command(name='DelChannel', aliases=['dc'], prefixes=['.'])
async def DelChannel(msg: Message, b: Bot):
    bot_setting = init_bot('load')
    channel_id = msg.ctx.channel.id
    user_id = msg.author.id
    guide = await b.fetch_guild(msg.ctx.guild.id)
    if user_id in bot_setting['GM']:
        await guide.delete_channel(channel_id)


@bot.command(name='addUser', aliases=['au'], prefixes=['.'])
async def add_User(msg: Message, config: str = None):
    if config is None:
        await msg.delete()
    else:
        bot_setting = init_bot('load')
        if msg.ctx.channel.id in bot_setting['manage_channel_whitelist']:
            usernamecache = username_sl('load')
            if msg.author.id not in usernamecache.keys():
                usernamecache[msg.author.id] = {}
            usernamecache[msg.author.id]['name'] = config
            if 'pc' not in usernamecache[msg.author.id].keys():
                usernamecache[msg.author.id]['pc'] = {}
            username_sl('save', usernamecache)
            await msg.reply('用户添加成功', use_quote=False)


@bot.command(name='r', aliases=['R', 'rd', 'RD'], prefixes=['.'])
async def default_dice(msg: Message, config: str = None):
    if config is None:
        await msg.delete()
    else:
        bot_setting = init_bot('load')
        if msg.ctx.channel.id in bot_setting['dice_whitelist_channel']:
            dice = bonus = error = 0
            multi = 1
            dice_num = '1'
            output = '(met)' + msg.author.id + '(met)投掷【.rd ' + config + '】 (ins)掷骰结果为'
            cache = config.upper()
            dice_point_list = list()
            try:
                if cache.find('*') != -1:
                    multi = int(cache.rsplit('*')[-1])
                    cache = cache.rsplit('*')[0]
                if cache.find('+') != -1:
                    bonus = int(cache.rsplit('+')[-1])
                    cache = cache.rsplit('+')[0]
                if cache.find('D') != -1:
                    dice, dice_point_list = Dice(dice_config=cache)
                else:
                    dice = random.randint(1, int(cache))
            except ValueError:
                error = 1
                await msg.delete()
            if error != 1:
                output += str((dice + bonus) * multi) + '(ins)'
                if int(dice_num) != 1:
                    output += ',(spl)'
                    output += ' '.join([str(point) for point in dice_point_list])
                    output += '(spl)'
                await msg.reply(output, use_quote=False)


re_digit = re.compile('\d.')


@bot.command(name='ra', aliases=['RA'], prefixes=['.'])
async def skill_judge(msg: Message, config='', skill_num: str = None):
    bot_setting = init_bot('load')
    coc_games = coc_games_sl('load')
    user = username_sl('load')
    guild_id = msg.ctx.guild.id
    user_id = msg.author.id
    if msg.ctx.channel.id in bot_setting['dice_whitelist_channel']:
        if config == '':
            await msg.delete()
        if config in attributes_dict.keys():
            config = attributes_dict[config]
        if skill_num is not None or re_digit.search(config) is not None:
            if skill_num is not None:
                skill_num = int(skill_num)
                output = skillDice(skill_num, user_id, config)
            elif re_digit.search(config) is not None:
                cache = re_digit.search(config).span()
                skill_num = int(config[cache[0]:])
                config = config[:cache[0]]
                output = skillDice(skill_num, user_id, config)
            await msg.reply(output, use_quote=False)
        else:
            if user_id not in coc_games[guild_id]['player'].keys():
                output = '(met)' + user_id + '(met)不存在该名玩家，使用(ins).join+游戏名称(ins)加入这场游戏。'
            elif 'role' not in coc_games[guild_id]['player'][user_id].keys():
                output = '(met)' + user_id + '(met)当前玩家没有可用角色，使用(ins).playrole+角色名称(ins)加入这场游戏。'
            else:
                pc_name = coc_games[guild_id]['player'][user_id]['role']
                if config in user[user_id]['pc'][pc_name]['skill'].keys():
                    skill_num = user[user_id]['pc'][pc_name]['skill'][config]
                elif config in user[user_id]['pc'][pc_name]['attributes'].keys():
                    skill_num = user[user_id]['pc'][pc_name]['attributes'][config]
                output = skillDice(skill_num, user_id, config)
            await msg.reply(output, use_quote=False)


@bot.command(name='SanCheck', aliases=['san', 'sc'], prefixes=['.'])
async def sanCheck(msg: Message, b: Bot, config: str, san: int = None):
    bot_setting = init_bot('load')
    coc_games = coc_games_sl('load')
    user = username_sl('load')
    channel_id = msg.ctx.channel.id
    guild_id = msg.ctx.guild.id
    user_id = msg.author.id
    if config is None and san is None:
        await msg.delete()
    else:
        config = config.upper()
        if msg.ctx.channel.id in bot_setting['dice_whitelist_channel']:
            if san is not None:
                san_point, output = sanDice(san, user_id, config)
            else:
                if user_id not in coc_games[guild_id]['player'].keys():
                    output = '(met)' + user_id + '(met)不存在该名玩家，使用(ins).join+游戏名称(ins)加入这场游戏。'
                elif 'role' not in coc_games[guild_id]['player'][user_id].keys():
                    output = '(met)' + user_id + '(met)当前玩家没有可用角色，使用(ins).playrole+角色名称(ins)加入这场游戏。'
                else:
                    pc_name = coc_games[guild_id]['player'][user_id]['role']
                    san = user[user_id]['pc'][pc_name]['attributes']['pow']
                    san_point, output = sanDice(san, user_id, config)
            user[user_id]['pc'][pc_name]['san'][0] -= san_point
            username_sl('save', user)
            await msg.reply(output, use_quote=False)


@bot.command(name='createNewRoom', aliases=['cnr'], prefixes=['.'])
async def createNewRoom(msg: Message, b: Bot, config: str = None):
    coc_roles_id = {}
    coc_games = coc_games_sl('load')
    bot_setting = init_bot('load')
    channel_id = msg.ctx.channel.id
    guild_id = msg.ctx.guild.id
    if config is None:
        await msg.delete()
    else:
        if channel_id in bot_setting['manage_channel_whitelist'] and guild_id not in coc_games.keys():
            coc_games[guild_id] = {}
            guide = await b.fetch_guild(guild_id)
            roles = [role for role in await guide.fetch_roles()]
            names = [role.name for role in roles]
            ids = [role.id for role in roles]
            roles_ids = dict(zip(names, ids))
            for role in coc_roles:
                coc_roles_id[role] = roles_ids[role]
            coc_games[guild_id]['name'] = config
            coc_games[guild_id]['role'] = coc_roles_id
            await guide.create_channel(config, is_category=1)
            category_list = [category for category in await guide.fetch_channel_category_list()]
            for category in category_list:
                if category.name == coc_games[guild_id]['name']:
                    coc_games[guild_id]['category_id'] = category.id
                    category_id = category.id
            voice_channel = await guide.create_channel(config + '_主频道_语音', category=category_id, type=2)
            text_channel = await guide.create_channel(config + '_主频道_文字', category=category_id, type=1)
            map_channel = await guide.create_channel(config + '_地图', category=category_id, type=1)
            kp_channel = await guide.create_channel(config + '_KP', category=category_id, type=1)
            card_channel = await guide.create_channel(config + '_录卡', category=category_id, type=1)
            await kp_channel.update_permission(role_id=coc_games[guild_id]['role']['KP'], allow=2048)
            await kp_channel.update_permission(role_id='0', deny=2048)
            channel_list = [voice_channel, text_channel, map_channel, kp_channel, card_channel]
            channel_name = [(config + name) for name in coc_channel_names]
            for name in channel_name:
                index = channel_name.index(name)
                coc_games[guild_id][name] = channel_list[index].id
            await guide.grant_role(msg.author, coc_games[guild_id]['role']['KP'])
            bot_setting['dice_whitelist_channel'].append(text_channel.id)
            bot_setting['dice_whitelist_channel'].append(kp_channel.id)
            bot_setting['manage_channel_whitelist'].append(kp_channel.id)
            bot_setting['manage_channel_whitelist'].append(card_channel.id)
            coc_games[guild_id]['player'] = {}
            coc_games_sl('save', coc_games)
            init_bot('save', bot_setting)
            await card_channel.send(
                '本骰娘的录卡较为简单，登记玩家名后((ins).au 玩家名(ins))直接把车好的卡发进来就可以了，导入完成后使用(ins).pr 角色名(ins)使用角色。')
            await msg.reply(('(met)' + msg.author.id + '(met)房间创建成功'), use_quote=False)


@bot.command(name='join', prefixes=['.'])
async def JoinRoom(msg: Message, b: Bot, config: str = None):
    if config is None:
        await msg.delete()
    else:
        bot_setting = init_bot('load')
        coc_games = coc_games_sl('load')
        username = username_sl('load')
        guild_id = msg.ctx.guild.id
        channel_id = msg.ctx.channel.id
        user_id = msg.author.id
        if channel_id in bot_setting['manage_channel_whitelist'] and config == coc_games[guild_id]['name']:
            guide = await b.fetch_guild(guild_id)
            coc_games[guild_id]['player'][user_id] = {'name': username[user_id]['name'], 'role': None}
            await guide.grant_role(msg.author, coc_games[guild_id]['role']['PL'])
            channels_list = [channel for channel in await guide.fetch_channel_list()]
            for channel in channels_list:
                if channel.name == (coc_games[guild_id]['name'] + '_主频道_语音') and channel.parent_id == \
                        coc_games[guild_id]['category_id']:
                    await channel.moveUser(msg.author)
            output = '(met)' + user_id + '(met)成功加入游戏。'
            await msg.reply(output, use_quote=False)
            coc_games_sl('save', coc_games)


@bot.command(name='closeRoom', aliases=['cr'], prefixes=['.'])
async def closeRoom(msg: Message, b: Bot, config: str = None):
    if config is None:
        await msg.delete()
    else:
        bot_setting = init_bot('load')
        coc_games = coc_games_sl('load')
        try:
            guide = await b.fetch_guild(msg.ctx.guild.id)
            guideuser = await guide.fetch_user(msg.author.id)
            roles_id = [cache for cache in coc_games[msg.ctx.guild.id]['role'].values()]
            for role in guideuser.roles:
                if role in roles_id:
                    for name in coc_channel_names[:]:
                        await guide.delete_channel((coc_games[msg.ctx.guild.id][(config + name)]))
                    await guide.delete_channel((coc_games[msg.ctx.guild.id]['category_id']))
                    try:
                        await guide.revoke_role(msg.author, coc_games[msg.ctx.guild.id]['role']['KP'])
                        if coc_games[msg.ctx.guild.id]['player'] is not None:
                            for user in coc_games[msg.ctx.guild.id]['player'].keys():
                                await guide.revoke_role(user, coc_games[msg.ctx.guild.id]['role']['PL'])
                    except khl.requester.HTTPRequester.APIRequestFailed:
                        print('继续执行')
                    try:
                        bot_setting['dice_whitelist_channel'].pop(
                            bot_setting['dice_whitelist_channel'].index(
                                coc_games[msg.ctx.guild.id][(config + '_主频道_文字')]))
                        bot_setting['dice_whitelist_channel'].pop(
                            bot_setting['dice_whitelist_channel'].index(
                                coc_games[msg.ctx.guild.id][(config + '_KP')]))
                        bot_setting['manage_channel_whitelist'].pop(bot_setting['manage_channel_whitelist'].index(
                            coc_games[msg.ctx.guild.id][(config + '_KP')]))
                        bot_setting['manage_channel_whitelist'].pop(bot_setting['manage_channel_whitelist'].index(
                            coc_games[msg.ctx.guild.id][(config + '_录卡')]))
                    except ValueError:
                        print('继续执行')
                    del coc_games[msg.ctx.guild.id]
                    coc_games_sl('save', coc_games)
                    init_bot('save', bot_setting)
        except KeyError:
            print('继续执行')


@bot.command(name='delrole', aliases=['dr'], prefixes=['.'])
async def delrole(msg: Message, config: str, confirm: str):
    bot_setting = init_bot('load')
    user = username_sl('load')
    channel_id = msg.ctx.channel.id
    user_id = msg.author.id
    if channel_id in bot_setting['dice_whitelist_channel'] or channel_id in bot_setting['manage_channel_whitelist']:
        if user_id in user.keys():
            if config in user[user_id]['pc'].keys() and config == confirm:
                del user[user_id]['pc'][config]
                output = '(met)' + user_id + '(met) (ins)' + config + '(ins) 他已经离开了你，这一切是不可挽回的。'
                username_sl('save', user)
                await msg.reply(output, use_quote=False)


@bot.command(name='playrole', aliases=['role', 'pr', 'ur'], prefixes=['.'])
async def playrole(msg: Message, config: str = 'list'):
    bot_setting = init_bot('load')
    coc_games = coc_games_sl('load')
    user = username_sl('load')
    guild_id = msg.ctx.guild.id
    channel_id = msg.ctx.channel.id
    user_id = msg.author.id
    if channel_id in bot_setting['dice_whitelist_channel']:
        if user_id in user.keys():
            if config == 'list':
                if user[user_id]['pc'] != {}:
                    pc = [i for i in user[user_id]['pc'].keys()]
                    pc = '、'.join(pc)
                    output = '(met)' + user_id + '(met)你的可用角色有：' + pc + '。'
                else:
                    output = '(met)' + user_id + '(met)你没有可用角色。'
            else:
                if user[user_id]['pc'] is not None and config in user[user_id]['pc'].keys() and user_id in \
                        coc_games[guild_id]['player'].keys():
                    coc_games[guild_id]['player'][user_id]['role'] = config
                    output = '(met)' + user_id + '(met)你以(ins)' + config + '(ins)的身份加入了游戏。'
                elif user_id not in coc_games[guild_id]['player'].keys():
                    output = '(met)' + user_id + '(met)你并没有加入这场游戏，使用(ins).join+游戏名称(ins)加入这场游戏。'
                elif user[user_id]['pc'] is None:
                    output = '(met)' + user_id + '(met)你没有可用角色。'
                elif config not in user[user_id]['pc'].keys():
                    pc = [i for i in user[user_id]['pc'].keys()]
                    pc = '、'.join(pc)
                    output = '(met)' + user_id + '(met)该角色不在你的可用角色中。可用角色：' + pc + '。'
        else:
            output = '(met)' + user_id + '(met)并没有记录你的玩家名，使用(ins).au+玩家名称(ins)。'
        coc_games_sl('save', coc_games)
        await msg.reply(output, use_quote=False)


@bot.command(name='help', aliases=[''], prefixes=['.', '?', '？'])
async def help(msg: Message, config: str = 'list'):
    bot_setting = init_bot('load')
    if msg.ctx.channel.id in bot_setting['manage_channel_whitelist']:
        await msg.reply('还在施工中，暂时没有帮助呢', use_quote=False)


async def loadCard(msg: Message):
    coc_games = coc_games_sl('load')
    username = username_sl('load')
    guild_id = msg.ctx.guild.id
    if guild_id in coc_games.keys():
        coc_game_name = coc_games[guild_id]['name']
        if msg.ctx.channel.id == coc_games[guild_id][(coc_game_name + '_录卡')] and msg.author.id in username.keys():
            wget.download(msg.content, 'data/PlayerCard/')
            file = os.listdir('data/PlayerCard/')
            file = 'data/PlayerCard/' + file[0]
            data = pd.read_excel(file, sheet_name='人物卡')
            data.columns = np.arange(0, 67, 1)
            pl_name = data[4][2]
            if pl_name == username[msg.author.id]['name']:
                role_name = data[4][1]
                role_load(msg.author.id, role_name, data, username)
                username_sl('save', username)
                await msg.reply(('(met)' + msg.author.id + '(met)角色卡导入成功'), use_quote=False)
            else:
                await msg.reply(('(met)' + msg.author.id + '(met)该角色玩家名与你所登记的玩家名不符'), use_quote=False)
            os.remove(file)
        else:
            await msg.reply(('(met)' + msg.author.id + '(met)你还未登记玩家名使用(ins).au+玩家名(ins)来登记'), use_quote=False)


bot.client.register(MessageTypes.FILE, loadCard)

bot.run()
