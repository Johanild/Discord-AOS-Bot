import os
import re
import random
import discord
import json
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='$', intents=intents)
bot.remove_command('help')
blackjack_multiplier = 1
coinflip_multiplier = 0.95
dice_multiplier = 5.5

with open("emojis.json", "r") as emoji_data:
    emojis = json.load(emoji_data)


def replace_emotes(guild, text):
    def replace(match):
        emoji_name = match.group(1)
        custom_emoji = discord.utils.get(guild.emojis, name=emoji_name)

        if custom_emoji:
            return f'<:{emoji_name}:{custom_emoji.id}>'
        else:
            return match.group(0)

    pattern = re.compile(r':([a-zA-Z0-9_]+):')
    return pattern.sub(replace, text)


def create_user(user_id):
    with open('users.json', 'r') as file:
        data = json.load(file)
    data[f"{user_id}"] = {
        "Inventory": {},
        "Balance": 0,
        "Flags": {
            "Banned": False,
            "Administartor": False,
            "Moderator": False
        },
        "Statistics": {
            "bj_win": 0,
            "bj_loss": 0,
            "bj_tie": 0,
            "cf_win": 0,
            "cf_loss": 0
        }
    }
    with open("users.json", "w") as file:
        json.dump(data, file, indent=4)


def get_balance(user_id):
    with open('users.json', 'r') as file:
        data = json.load(file)
    if str(user_id) in data:
        return data[str(user_id)]["Balance"]
    else:
        create_user(user_id)
        return 0


def update_balance(user_id, mode, amount):
    with open("users.json", "r") as file:
        data = json.load(file)

    if str(user_id) not in data:
        create_user(user_id)
    if mode == "add":
        data[str(user_id)]["Balance"] += int(amount)
    elif mode == "remove":
        data[str(user_id)]["Balance"] -= int(amount)
    elif mode == "erase":
        data[str(user_id)]["Balance"] = 0

    with open("users.json", "w") as file:
        json.dump(data, file, indent=4)


def check_perms(user_id, perm):
    with open("users.json", "r") as file:
        data = json.load(file)
    return data[str(user_id)]["Flags"][perm]


def manage_statistics(user_id: str, game: str, outcome: str):
    with open("statistics.json", "r") as stats_file:
        stats_data = json.load(stats_file)
    with open("users.json", "r") as users_file:
        users_data = json.load(users_file)

    if f"{game}_{outcome}" in stats_data:
        stats_data[f"{game}_{outcome}"] += 1
        stats_data[f"{game}_total"] += 1
        stats_data[f"{game}_winrate"] = round(stats_data[f"{game}_win"] / stats_data[f"{game}_total"] * 100, 2)
        if f"{game}_tie" in stats_data:
            stats_data[f"{game}_tierate"] = round(stats_data[f"{game}_tie"] / stats_data[f"{game}_total"] * 100, 2)

    if str(user_id) not in users_data:
        create_user(user_id)
    users_data[str(user_id)]["Statistics"][f"{game}_{outcome}"] += 1

    with open("users.json", "w") as users_file:
        json.dump(users_data, users_file, indent=4)
    with open("statistics.json", "w") as stats_file:
        json.dump(stats_data, stats_file, indent=4)


def generate_loadout():
    with open("weapons.json", "r") as file:
        data = json.load(file)
    loadout = []
    types = ["Marksman", "Trooper", "Commando", "Melee", "Grenade", "Block"]
    for i in range(6):
        weapon = random.choice(data[types[i]])
        loadout.append(weapon)
    return loadout


@bot.event
async def on_ready():
    print("Bot ready")


@bot.command()
async def help(ctx, *args):
    if len(args) == 0:
        title = "Informations and commands"
        description = "This is prototype of AOS Casino bot developed by v0v0\n\n**List of commands:**\n​   Coinflip - Starts a game of coinflip\n​   Blackjack - Starts a game of blackjack\n​   Dice - Starts a game of dice\n​   Balance - Checks yours or someones balance\n​   Statistics - Displays your statistics\n​   Donate - Lets you donate your balance to someone\n​   Loadout - Generates random loadout\n​   Leaderboard - Shows token amount leaderboard\n\nIf you need help with any specific command, use: `$help (command)`"
    else:
        if args[0] == "coinflip" or args[0] == "cf":
            title = "Informations about $coinflip command"
            description = f"**Coinflip is a minigame in which you chose which face of a coin you think will land on, if you guess correctly you will be awarded with tokens.**\nCommand syntax: `$coinflip [wager]`\nWin probability: `50%`\nWin multiplier: `{coinflip_multiplier}x` wager\nWager restrictions: `100` - `50k` tokens"
        elif args[0] == "blackjack" or args[0] == "bj":
            title = "Informations about $blackjack command"
            description = f"**Blackjack is a minigame in which you play against dealer (bot), your objective is to reach card value as close to 21 as possible without going past that number. If both you and dealer go past 21 the person that is closer to 21 wins. If you and dealer get the same card values theres a tie and you get your tokens back.**\nCommand syntax: `$blackjack [wager]`\nWin probability: `Unspecified`\nWin multiplier: `{blackjack_multiplier}x` wager\nBlackjack win (21) multiplier: `{1 + blackjack_multiplier}`\nWager restrictions: `100` - `50k` tokens"
        elif args[0] == "dice" or args[0] == "dc":
            title = "Informations about $dice command"
            description = f"**Dice is a minigame in which you predict which number a D6 dice will land on. If you guess correctly you will be awarded with tokens.**\nCommand syntax: `$dice [number] [wager]`\nWin probability: `16.7%`\nWin multiplier: `{dice_multiplier}`x wager\nWager restrictions: `100` - `50k` tokens"
        elif args[0] == "balance" or "bal":
            title = "Informations about $balance command"
            description = f"This command lets you see yours or someone elses balance, optional arguments: \n`@mention` - Lets you see mentioned users balance\n`user ID` - Lets you see balance of user with given Discord ID"
        elif args[0] == "loadout":
            title = "Informations about $loadout command"
            description = f"This command generates random AOS loadout, optional arguments:\n`number` - Lets you generate specific amount of loadouts (Up to 10)"
    embed = discord.Embed(title=title, description=description, color=discord.Color.blurple())
    await ctx.reply(embed=embed, mention_author=True)


@bot.command(aliases=["cf"])
async def coinflip(ctx, wager):
    wager = int(wager)
    user_id = str(ctx.author.id)
    button_clicked = False

    if wager is None:
        await ctx.reply("Incorrect syntax, please specify wager amount. Example: $coinflip 100", mention_author=False)
        return
    elif wager < 100 or wager > 50000:
        await ctx.reply("Wager amount must be between 100 and 50000", mention_author=False)
        return

    async def button_callback(interaction: discord.Interaction):
        nonlocal button_clicked

        if button_clicked or str(interaction.user.id) != user_id:
            return

        button_clicked = True
        selected_button = interaction.data["custom_id"]
        balance = get_balance(user_id)

        if balance >= wager:
            if selected_button == "cancel":
                embed = discord.Embed(title="Coinflip canceled", description="You have canceled your coinflip",
                                      color=discord.Color.red())
                await interaction.response.send_message(embed=embed)
                button_clicked = True
                return

            outcomeface = random.choice(["heads", "tails"])
            if selected_button == outcomeface:
                outcome, amount, selected_color = "won", wager * coinflip_multiplier, discord.Color.blurple()
                update_balance(user_id, "add", amount)
                manage_statistics(user_id, "cf", "win")
            else:
                outcome, amount, selected_color = "lost", wager, discord.Color.red()
                update_balance(user_id, "remove", wager)
                manage_statistics(user_id, "cf", "loss")

            embed = discord.Embed(title=f"You {outcome} {amount} tokens!",
                                  description=f"The coin has landed on {outcomeface}\nYour balance is now {get_balance(user_id)} tokens",
                                  color=selected_color)
            embed.set_image(
                url="https://cdn.discordapp.com/attachments/1117592667979776050/1122553419991891969/head.png" if outcomeface == "heads" else "https://cdn.discordapp.com/attachments/1117592667979776050/1122553433350746254/tail.png")
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Insufficient balance.")

    view = discord.ui.View()
    button1 = discord.ui.Button(label="Heads", custom_id="heads", style=discord.ButtonStyle.danger, emoji=emojis["head"])
    button2 = discord.ui.Button(label="Tails", custom_id="tails", style=discord.ButtonStyle.primary, emoji=emojis["tail"])
    button3 = discord.ui.Button(label="Cancel", custom_id="cancel", style=discord.ButtonStyle.danger, emoji="⚫")

    button1.callback, button2.callback, button3.callback = button_callback, button_callback, button_callback

    view.add_item(button1)
    view.add_item(button2)
    view.add_item(button3)

    embed = discord.Embed(title="Coin Flip", description="Please select coin face:", color=discord.Color.blurple())
    await ctx.send(embed=embed, view=view)


@bot.command(aliases=["bal", "bl"])
async def balance(ctx, *args):
    if len(args) <= 1:
        user_id = str(ctx.author.id) if len(args) == 0 else (
            str(ctx.message.mentions[0].id if ctx.message.mentions != [] else args[0]))
        user_name = ctx.author.name if len(args) == 0 else ((await bot.fetch_user(int(user_id))).global_name)
        balance = get_balance(user_id)
        embed = discord.Embed(title=f"{user_name}'s balance", description=f"The balance is {balance} tokens",
                              color=discord.Color.blurple())
        await ctx.send(embed=embed)
    elif len(args) <= 3:
        if ctx.message.mentions != []:
            user_id = str(ctx.message.mentions[0].id)
            user_name = str(ctx.message.mentions[0].name)
        else:
            user_id = int(args[1])
            user = await bot.fetch_user(user_id)
            user_name = user.global_name
        sender_id = str(ctx.author.id)
        operation = args[0]
        amount = int(args[2]) if len(args) > 2 else None
        if check_perms(sender_id, "Administrator") is True:
            update_balance(user_id, operation, amount)
            embed = discord.Embed(title="Balance edit",
                                  description=f"{user_name}'s balance has been successfully updated.",
                                  color=discord.Color.blurple())
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Insufficient permissions", description="You dont have permissions to do this.",
                                  color=discord.Color.red())
            await ctx.send(embed=embed)


@bot.command()
async def donate(ctx, reciever, amount):
    button_clicked = False
    if ctx.message.mentions != []:
        reciever_id = str(ctx.message.mentions[0].id)
        reciever_name = str(ctx.message.mentions[0].name)
    else:
        reciever_id = int(reciever)
        reciever_name = (await bot.fetch_user(reciever_id)).name
    sender_id = str(ctx.author.id)
    balance = get_balance(sender_id)

    async def button_callback(interaction: discord.Interaction):
        nonlocal button_clicked
        if button_clicked or str(interaction.user.id) != sender_id:
            return

        button_clicked = True
        button_id = interaction.data['custom_id']

        if button_id == "cancel":
            embed = discord.Embed(title="Donation cancelled",
                                  description=f"Donation of `{amount}` to `{reciever_name}` has been cancelled.",
                                  color=discord.Color.red())
            await interaction.response.send_message(embed=embed)

        elif button_id == "confirm":
            update_balance(sender_id, "remove", amount)
            update_balance(reciever_id, "add", amount)
            embed = discord.Embed(title="Succesfully donated",
                                  description=f"You have succesfully donated `{amount}` tokens to `{reciever_name}`!",
                                  color=discord.Color.blurple())
            await interaction.response.send_message(embed=embed)

        else:
            await interaction.response.send_message("Insufficient balance.")

    if get_balance(sender_id) >= int(amount):
        view = discord.ui.View()
        button1 = discord.ui.Button(label="Confirm", custom_id="confirm", style=discord.ButtonStyle.success, emoji="⚫")
        button2 = discord.ui.Button(label="Cancel", custom_id="cancel", style=discord.ButtonStyle.danger, emoji="⚫")

        button1.callback, button2.callback = button_callback, button_callback

        view.add_item(button1)
        view.add_item(button2)

        embed = discord.Embed(title="Donation confirmation",
                              description=f"Are you sure you want to donate `{amount}` tokens to `{reciever_name}`?\nYour balance after that will be `{balance - int(amount)}`.",
                              color=discord.Color.blurple())
        await ctx.send(embed=embed, view=view)


@bot.command()
async def loadout(ctx, amount = None):
    if amount == None:
        marksman, trooper, commando, melee, grenade, block = generate_loadout()
        title="Random loadout generated"
        description=f"Marksman: {marksman}\nTrooper: {trooper}\nCommando: {commando}\nMelee: {melee}\nGrenade: {grenade}\nBlock: {block}"
    else:
        amount = int(amount)
        amount = 10 if amount > 10 else amount
        title = f"{amount} random loadouts generated"
        description = ""
        for index in range(int(amount)):
            marksman, trooper, commando, melee, grenade, block = generate_loadout()
            description += f"{index}. {marksman}, {trooper}, {commando}, {melee}, {grenade}, {block}\n"
    embed = discord.Embed(title=title, description=description, color=discord.Color.blurple())
    await ctx.send(embed=embed)


@bot.command(aliases=["lb"])
async def leaderboard(ctx, cap=10):
    with open("users.json", "r") as file:
        data = json.load(file)
    if int(cap) > 20:
        cap = 20
    if int(cap) > len(data.keys()):
        cap = len(data.keys())
    message_data = []
    message = ""
    for user_id in data:
        user_name = (await bot.fetch_user(user_id)).name
        user_balance = int(data[user_id]["Balance"])
        message_data.append((user_balance, user_name))
    sorted_message_data = sorted(message_data, key=lambda x: x[0], reverse=True)
    for index in range(cap):
        instance = sorted_message_data[index]
        line = f"{index}. {instance[1]}: {instance[0]}\n"
        message += line

    embed = discord.Embed(title="Balance Leaderboard", description=message, color=discord.Color.blurple())
    await ctx.send(embed=embed)


import discord


@bot.command(aliases=["bj"])
async def blackjack(ctx, wager: int):
    async def end_game(outcome, temp_description):
        description = f"Dealers Cards: {''.join([emojis[card] for card in dealer_cards])} Total: {dealer_total}\n\nYour Cards: \u200B \u200B \u200B \u200B \u200B \u200B \u200B{''.join([emojis[card] for card in user_cards])} Total: {user_total}\n\n{temp_description}"
        manage_statistics(user_id, "bj", outcome)
        if outcome == "win":
            update_balance(user_id, "add", wager * blackjack_multiplier)
            color = discord.Color.blurple()
        elif outcome == "loss":
            update_balance(user_id, "remove", wager)
            color = discord.Color.red()
        else:
            color = discord.Color.blurple()
        embed.description = description
        embed.color = color
        await message.edit(embed=embed, view=None)

    def deal_cards(amount):
        nonlocal all_cards
        chosen_cards = []
        value_cards = 0
        for _ in range(amount):
            chosen_card = all_cards.pop(random.randint(0, len(all_cards)-1))
            chosen_card_symbol = chosen_card[0]
            chosen_cards.append(chosen_card_symbol)
            value_cards += chosen_card[1]
        return chosen_cards, value_cards

    async def button_callback(interaction: discord.Interaction):
        nonlocal user_total, message, embed, dealer_total, user_total, user_aces_swapped, dealer_aces_swapped
        await interaction.response.defer()

        if str(interaction.user.id) != user_id:
            return

        selected_button = interaction.data["custom_id"]

        if selected_button == "hit":
            dealt_card, dealt_total = deal_cards(1)
            user_cards.append(dealt_card[0])
            user_total += dealt_total
            if user_total < 21:
                embed.description = f"Dealers Cards: {emojis['CR']}{''.join([emojis[card] for card in dealer_cards[1:]])} Total: ?\n\nYour Cards: \u200B \u200B \u200B \u200B \u200B \u200B \u200B{''.join([emojis[card] for card in user_cards])} Total: {user_total}\n\n"
                await message.edit(embed=embed)
            elif user_total == 21:
                if user_total > dealer_total:
                    await end_game("win", f"**You have won `{int(wager * blackjack_multiplier)}`, the dealer has drew worse hand!")
                elif user_total < dealer_total:
                    await end_game("win", f"**You have won `{int(wager * blackjack_multiplier)}`, the dealer has busted!")
                elif dealer_total == 21:
                    await end_game("tie", "**Tie, the dealer has drawn cards of the same value.**")
            elif user_total > 21:
                if "CA" in user_cards and user_cards.count("CA") > user_aces_swapped:
                    user_total -= 10
                    user_aces_swapped += 1
                    embed.description = f"Dealers Cards: {emojis['CR']}{''.join([emojis[card] for card in dealer_cards[1:]])} Total: ?\n\nYour Cards: \u200B \u200B \u200B \u200B \u200B \u200B \u200B{''.join([emojis[card] for card in user_cards])} Total: {user_total}\n\n"
                    await message.edit(embed=embed)
                else:
                    if user_total < dealer_total:
                        await end_game("win", f"**You have won `{int(wager * blackjack_multiplier)}`, the dealer has busted by more!**")
                    elif user_total > dealer_total:
                        if dealer_total <= 21:
                            await end_game("loss", "**You have lost by bust.**")
                        elif dealer_total > 21:
                            await end_game("loss", "**You have lost, the dealer has busted by less.**")
                    elif user_total == dealer_total:
                        await end_game("tie", "**Tie, both you and the dealer have busted.**")

        elif selected_button == "stand":
            while dealer_total < 17:
                dealt_card, dealt_total = deal_cards(1)
                dealer_cards.append(dealt_card[0])
                if dealer_total + dealt_total > 21 and "CA" in dealer_cards and dealer_cards.count("CA") > dealer_aces_swapped:
                    dealer_total_temp = dealer_total + dealt_total
                    dealer_total = dealer_total_temp - 10
                    dealer_aces_swapped += 1
                else:
                    dealer_total += dealt_total
            if user_total < 21:
                if user_total > dealer_total:
                    await end_game("win", f"**You have won `{int(wager * blackjack_multiplier)}`, the dealer has drew worse hand!**")
                elif user_total < dealer_total:
                    if dealer_total > 21:
                        await end_game("win", f"**You have won `{int(wager * blackjack_multiplier)}`, the dealer has busted.**")
                    elif dealer_total <= 21:
                        await end_game("loss", "**You have lost, the dealer has drew better hand.**")
                elif user_total == dealer_total:
                    await end_game("tie", "**Tie, the dealer has drawn cards of the same value.**")

    user_id = str(ctx.author.id)
    all_cards = [("C2", 2), ("C3", 3), ("C4", 4), ("C5", 5), ("C6", 6), ("C7", 7), ("C8", 8), ("C9", 9), ("C10", 10), ("CJ", 10), ("CQ", 10), ("CK", 10), ("CA", 11), 
                 ("C2", 2), ("C3", 3), ("C4", 4), ("C5", 5), ("C6", 6), ("C7", 7), ("C8", 8), ("C9", 9), ("C10", 10), ("CJ", 10), ("CQ", 10), ("CK", 10), ("CA", 11), 
                 ("C2", 2), ("C3", 3), ("C4", 4), ("C5", 5), ("C6", 6), ("C7", 7), ("C8", 8), ("C9", 9), ("C10", 10), ("CJ", 10), ("CQ", 10), ("CK", 10), ("CA", 11), 
                 ("C2", 2), ("C3", 3), ("C4", 4), ("C5", 5), ("C6", 6), ("C7", 7), ("C8", 8), ("C9", 9), ("C10", 10), ("CJ", 10), ("CQ", 10), ("CK", 10), ("CA", 11)]

    if wager is None:
        await ctx.reply("Incorrect syntax, please specify wager amount. Example: $coinflip 100", mention_author=True)
        return
    elif wager < 100 or wager > 50000:
        await ctx.reply("Wager amount must be between 100 and 50000", mention_author=True)
        return
    balance = get_balance(user_id)
    if balance < wager:
        await ctx.reply(f"Insufficient balance, your current balance: `{balance}`", mention_author=True)
        return

    dealer_cards, dealer_total = deal_cards(2)
    user_cards, user_total = deal_cards(2)
    dealer_aces_swapped = 0
    user_aces_swapped = 0

    view = discord.ui.View()
    button1 = discord.ui.Button(label="Hit", custom_id="hit", style=discord.ButtonStyle.primary)
    button2 = discord.ui.Button(label="Stand", custom_id="stand", style=discord.ButtonStyle.secondary)

    button1.callback, button2.callback = button_callback, button_callback

    view.add_item(button1)
    view.add_item(button2)

    if dealer_total == 22:
        dealer_total = 12
        dealer_aces_swapped += 1
    if user_total == 22:
        user_total = 12
        user_aces_swapped +=1

    embed = discord.Embed(title=f"{ctx.author.global_name}'s Blackjack session",
                          description=f"Dealers Cards: {emojis['CR']}{emojis[dealer_cards[1]]} Total: ?\n\nYour Cards: \u200B \u200B \u200B \u200B \u200B \u200B \u200B{''.join([emojis[card] for card in user_cards])} Total: {user_total}",
                          color=discord.Color.blurple())
    message = await ctx.send(embed=embed, view=view)

    if dealer_total == 21 or user_total == 21:
        if user_total == 21 and dealer_total != 21:
            await end_game("win", f"**You have won `{int(wager * blackjack_multiplier)}` by drawing blackjack!**")
        elif user_total != 21 and dealer_total == 21:
            await end_game("loss", "**You have lost, the dealer has drawn blackjack.**")
        elif user_total == dealer_total:
            await end_game("tie", "**Tie, both you and the dealer have drawn blackjack.**")


@bot.command(aliases=["stats", "stat", "st"])
async def statistics(ctx):
    user_id = ctx.author.id
    with open("users.json", "r") as file:
        data = json.load(file)
    
    if str(user_id) not in data:
        create_user(user_id)
    cf_wins = data[str(user_id)]["Statistics"]["cf_win"]
    cf_loses = data[str(user_id)]["Statistics"]["cf_loss"]
    cf_total = cf_wins + cf_loses
    try:
        cf_winrate = round(cf_wins / cf_total * 100, 2)
    except ZeroDivisionError:
        cf_winrate = 0
    bj_wins = data[str(user_id)]["Statistics"]["bj_win"]
    bj_loses = data[str(user_id)]["Statistics"]["bj_loss"]
    bj_ties = data[str(user_id)]["Statistics"]["bj_tie"]
    bj_total = bj_wins + bj_loses + bj_ties
    try:
        bj_winrate = round(bj_wins / (bj_wins + bj_loses) * 100, 2)
    except ZeroDivisionError:
        bj_winrate = 0
    embed = discord.Embed(title=f"{ctx.author.global_name}'s Statistics", description=f"**Coinflip:**\n​   Wins: {cf_wins}\n​   Losses: {cf_loses}\n​   Winrate: {cf_winrate}%\n**Blackjack:**\n​   Wins: {bj_wins}\n​   Losses: {bj_loses}\n​   Ties: {bj_ties}\n​   Winrate: {bj_winrate}%", color=discord.Color.blurple())
    await ctx.send(embed=embed)


@bot.command(aliases=["dc"])
async def dice(ctx, number: int, wager: int):
    user_id = ctx.author.id
    selected_number = random.randint(1, 6)
    description = f"The dice has landed on {selected_number}, you have "
    if int(number) == selected_number:
        description += f"won `{int(wager * dice_multiplier)}` tokens!"
        update_balance(user_id, "add", wager*dice_multiplier)
        manage_statistics(user_id, "dc", "win")
        color = discord.Color.blurple()
    else:
        description += "lost."
        update_balance(user_id, "remove", wager)
        manage_statistics(user_id, "dc", "loss")
        color = discord.Color.red()
    embed = discord.Embed(title=f"{ctx.author.global_name}'s Dice Roll", description=description, color=color)
    embed.set_image(url=emojis[f"image_D{selected_number}"])
    await ctx.send(embed=embed)


with open("token.txt", "r") as file:
    TOKEN = file.read()
bot.run(TOKEN)
