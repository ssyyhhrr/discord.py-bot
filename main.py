import os
import json
import random
import discord
import time
import asyncio
from dotenv import load_dotenv
from discord.ext import tasks, commands

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

INTENTS = discord.Intents.default()
INTENTS.members = True

bot = commands.AutoShardedBot(command_prefix=commands.when_mentioned_or("!"), owner_id=518124039714242562, intents=INTENTS)

jackpotEmbed = None
participants = {}

pets = {}

class Pet():
    def __init__(self, name, animal):
        self.name = name
        self.animal = animal
        self.age = 0
        self.health = 100
        self.food = 100
    
    def feedPet(self):
        self.food = min(100, self.food + 10)

    async def info(self, ctx):
        EMBED = discord.Embed(title=self.name, description=self.animal, color=0xffff00)
        EMBED.add_field(name="Age", value=self.age)
        EMBED.add_field(name="Health", value=self.health)
        EMBED.add_field(name="Food", value=self.food)
        await ctx.send(embed=EMBED)

@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")
    depleteFood.start()
    increaseAge.start()

@bot.event
async def on_member_join(member):
    if not member.id in data:
        data[member.id] = {'coins': 0}
        data[member.id] = {'daily': 0}
        with open("users.json", "w") as f:
            json.dump(data, f, indent=4)

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

@bot.command()
async def coins(ctx):
    getConfig()
    await ctx.reply(f"You have **{str(data[str(ctx.message.author.id)]['coins'])}** coins.")

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

@bot.command()
async def quiz(ctx):
    getConfig()
    with open("questions.json", "r") as f:
        questionsArr = json.load(f)
        question = random.choice(questionsArr)
    EMBED = discord.Embed(title="Quiz Question", description=question[0], color=0xffa500)
    EMBED.add_field(name="Answers", value="**1.** True\n**2.** False")
    message = await ctx.reply(embed=EMBED)
    await message.add_reaction("1️⃣")
    await message.add_reaction("2️⃣")
    def check(reaction, user):
        return user == ctx.message.author and (str(reaction.emoji) == "1️⃣" or str(reaction.emoji) == "2️⃣")
    try:
        reaction, user = await bot.wait_for("reaction_add", timeout=60.0, check=check)
    except asyncio.TimeoutError:
        EMBED = discord.Embed(title="Quiz Question", description=question[0], color=0x808080)
        EMBED.add_field(name="Answers", value="**1.** True\n**2.** False")
        await message.edit(embed=EMBED)
    else:
        if (str(reaction.emoji) == "1️⃣" and question[1] == "true") or (str(reaction.emoji) == "2️⃣" and question[1] == "false"):
            EMBED = discord.Embed(title="Quiz Question", description=question[0], color=0x00ff00)
            EMBED.add_field(name="Answers", value="**1.** True\n**2.** False")
            await message.edit(embed=EMBED)
            data[str(ctx.message.author.id)]["coins"] += 100
            setConfig()
            await ctx.send(f"{ctx.message.author.mention}, you are correct! +**100** coins!")
        else:
            EMBED = discord.Embed(title="Quiz Question", description=question[0], color=0xff0000)
            EMBED.add_field(name="Answers", value="**1.** True\n**2.** False")
            await message.edit(embed=EMBED)
            await ctx.send(f"{ctx.message.author.mention}, you are incorrect :(")

@bot.command()
async def daily(ctx):
    getConfig()
    if int(time.time()) - data[str(ctx.message.author.id)]["daily"] > 86400:
        data[str(ctx.message.author.id)]["coins"] += 1000
        data[str(ctx.message.author.id)]["daily"] = time.time()
        await ctx.send(f"{ctx.message.author.mention}, you have claimed your daily **1000** coins!")
        setConfig()
        return
    else:
        await ctx.reply(f"24 hours has not passed since your last claim!")
        return

@bot.command()
async def jackpot(ctx, bet = None):
    global jackpotEmbed
    global participants
    getConfig()
    if not bet:
        await ctx.send("Invalid syntax. `!jackpot (bet)`")
        return
    try:
        betAmount = int(bet)
        if betAmount < 1:
            raise Exception()
    except:
        await ctx.send("Enter a valid bet amount.")
        return
    if data[str(ctx.message.author.id)]["coins"] < betAmount:
        await ctx.send("You do not have sufficient coins.")
        return
    data[str(ctx.message.author.id)]["coins"] -= betAmount
    setConfig()
    if jackpotEmbed == None:
        participants = {}
        EMBED = discord.Embed(title="Jackpot", description="Bets will close in **30** seconds.", color=0xffd700)
        EMBED.add_field(name="Jackpot Participants", value=ctx.message.author.mention)
        jackpotEmbed = await ctx.send(embed=EMBED)
        participants[ctx.message.author.mention] = betAmount
        await drawWinner()
    else:
        participants[ctx.message.author.mention] = betAmount
        EMBED = discord.Embed(title="Jackpot", description="Bets will close in **30** seconds.", color=0xffd700)
        EMBED.add_field(name="Jackpot Participants", value='\n'.join(participants))
        await jackpotEmbed.edit(embed=EMBED)
        await ctx.message.add_reaction("✅")

@bot.command()
async def pet(ctx, name = None, animal = None):
    global pets
    if ctx.message.author in pets:
        if pets[ctx.message.author] != None:
            await ctx.send("You already have a pet!")
            return
    if not name or not animal:
        await ctx.send("Invalid syntax. `!pet (name) (animal)`")
        return
    pets[ctx.message.author] = Pet(name, animal)
    await pets.get(ctx.author).info(ctx)

@bot.command()
async def feed(ctx):
    if ctx.message.author in pets:
        if pets[ctx.message.author] != None:
            pets[ctx.message.author].feed()
        else:
            await ctx.reply("You do not have a pet!")
            return
    else:
        await ctx.reply("You do not have a pet!")
        return

@bot.command()
async def info(ctx):
    if ctx.message.author in pets:
        if pets[ctx.message.author] != None:
            await pets[ctx.message.author].info(ctx)
        else:
            await ctx.reply("You do not have a pet!")
            return
    else:
        await ctx.reply("You do not have a pet!")
        return

@tasks.loop(seconds=30.0)
async def depleteFood():
    for i in range(len(list(pets.values()))):
        pet = list(pets.values())[i]
        if pet != None:
            pet.food = max(0, pet.food - 1)
            if pet.food == 0:
                pet.health = max(0, pet.health - 1)
            if pet.food == 100:
                pet.health = min(100, pet.health + 5)
            if pet.health == 0:
                pet = None

@tasks.loop(seconds=60.0)
async def increaseAge():
    for i in range(len(list(pets.values()))):
        pet = list(pets.values())[i]
        if pet != None:
            pet.age += 1

async def drawWinner():
    global jackpotEmbed
    global participants
    await asyncio.sleep(30)
    ticket = random.randint(1, sum(list(participants.values())))
    total = 0
    for i in range(len(list(participants.keys()))):
        total += list(participants.values())[i]
        if ticket < total:
            winner = list(participants.keys())[i]
            break
    data[str(winner[2:20])]["coins"] += sum(list(participants.values()))
    setConfig()
    EMBED = discord.Embed(title="Jackpot", description=f"The winner is {winner}\nThey won **{sum(list(participants.values()))}** coins!", color=0x808080)
    EMBED.add_field(name="Jackpot Participants", value='\n'.join(participants))
    await jackpotEmbed.edit(embed=EMBED)
    jackpotEmbed = None

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