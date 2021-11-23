import os
import json
import random
import discord
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

INTENTS = discord.Intents.default()
INTENTS.members = True

bot = commands.AutoShardedBot(command_prefix=commands.when_mentioned_or("!"), owner_id=518124039714242562, intents=INTENTS)

@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")

@bot.event
async def on_member_join(member):
    if not member.id in data:
        data[member.id] = {'coins': 0}
        with open("users.json", "w") as f:
            json.dump(data, f, indent=4)

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

@bot.command()
async def coins(ctx):
    getConfig()
    await ctx.reply(f"You have {str(data[str(ctx.message.author.id)]['coins'])} coins.")

@bot.command()
async def roulette(ctx, bet = None, colour = None):
    getConfig()
    if not bet or not colour:
        await ctx.send("Invalid syntax. `!roulette (bet) (colour)`")
        return
    try:
        betAmount = int(bet)
        if betAmount < 1:
            raise Exception()
    except:
        await ctx.send("Enter a valid bet amount.")
        return
    if colour != "red" and colour != "black":
        await ctx.send("Enter a valid colour.")
        return
    if data[str(ctx.message.author.id)]["coins"] < betAmount:
        await ctx.send("You do not have sufficient coins.")
        return
    
    select = random.randint(0, 1)
    if didWin(colour, select):
        data[str(ctx.message.author.id)]["coins"] += betAmount
    else:
        data[str(ctx.message.author.id)]["coins"] -= betAmount
    setConfig()
    await ctx.send(f"{'🔴' if select == 0 else '⚫'} The ball landed on {'red' if select == 0 else 'black'}. You {'won' if (didWin(colour, select)) else 'lost'} **{betAmount * (2 if (didWin(colour, select)) else 1)}** coins{'!' if (didWin(colour, select)) else '.'}")

def getConfig():
    global data
    with open("users.json", "r") as f:
        data = json.load(f)

def setConfig():
    with open("users.json", "w") as f:
        json.dump(data, f, indent=4)

def didWin(colour, select):
    return (colour == 'red' and select == 0) or (colour == 'black' and select == 1)

bot.run(TOKEN)