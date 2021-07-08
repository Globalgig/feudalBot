import discord
import os
import sqlite3, csv
import pandas
import random
import asyncio
from feudalBotRandomEncounters import *
from feudalBotMessageFormat import *
from dotenv import load_dotenv
from discord.ext import commands

#Mysteriously, find_env only worked when I specified the .env file name...
load_dotenv('feudalBot.env')
TOKEN = os.getenv('DISCORD_TOKEN')

con = sqlite3.connect('feudalBot.db')
c = con.cursor()

bot = commands.Bot(command_prefix='^')

#THE GREAT SETUP OF TABLES
@bot.event
async def on_ready():
	#Most of these values are self-explanatory, but a few are less transparent. 
	#popSpace and buildingSpace are the available slots for units/buildings respectively in one's township. attackValue, defenseValue, and magicValue are the values which determine the success of certain actions (pillage/spells). expandCount & adventureCount keep track of ALL of a player's calls to expand/adventure (even unsuccessful ones) and determine the cost 
	c.execute('CREATE TABLE IF NOT EXISTS township (id integer PRIMARY KEY, discord integer, name varchar(255), money integer DEFAULT 100, food integer DEFAULT 100, wood integer DEFAULT 0, iron integer DEFAULT 0, popSpace integer DEFAULT 8, buildingSpace integer, attackValue integer DEFAULT 0, defenseValue integer DEFAULT 0, magicValue integer DEFAULT 0, expandCount integer DEFAULT 0, adventureCount integer DEFAULT 0)')
	c.execute('CREATE TABLE IF NOT EXISTS perTurn (id integer PRIMARY KEY, discord integer, moneyPerTurn integer DEFAULT 0, foodPerTurn integer DEFAULT 0, woodPerTurn integer DEFAULT 0, ironPerTurn integer DEFAULT 0)')
	c.execute('CREATE TABLE IF NOT EXISTS unitList (id integer PRIMARY KEY, unitName varchar(255), cost integer, requisiteBuilding varchar(255), requisiteQuantity integer, moneyPerTurn integer, foodPerTurn integer, woodPerTurn integer, ironPerTurn integer, attackValue integer, defenseValue integer, magicValue integer)')
	c.execute('CREATE TABLE IF NOT EXISTS buildingList (id integer PRIMARY KEY, buildingName varchar(255), woodCost integer, ironCost integer, popSlots integer)')
	c.execute('CREATE TABLE IF NOT EXISTS unitsIG (id integer PRIMARY KEY, discord integer, unitName varchar(255), quantity integer DEFAULT 0)')
	c.execute('CREATE TABLE IF NOT EXISTS buildingsIG (id integer PRIMARY KEY, discord integer, buildingName varchar(255), quantity integer DEFAULT 0)')
	con.commit()

	await timer()




#JOIN AND LEAVE COMMANDS
@bot.command(name = 'join', aliases = ['j', 'participate', 'enter', 'start', 'begin'], help = 'Enter a name to start your village.')
async def join(ctx, username = None):

	if username == None:
		await ctx.send("Please enter a township name.")
		return

	#Check if the player already has an ID
	identical = c.execute('SELECT * FROM township WHERE discord = ?', (ctx.message.author.id,))
	row = c.fetchone()
	if not row:
		c.execute('INSERT INTO township (discord, name, money, food, wood, iron, popSpace, buildingSpace, attackValue, defenseValue, magicValue) VALUES (?, ?, 100, 100, 50, 0, 4, 3, 0, 0, 0)', (ctx.message.author.id, username,))
		c.execute('INSERT INTO perTurn (discord, moneyPerTurn, foodPerTurn, woodPerTurn, ironPerTurn) VALUES (?, 3, 2, 1, 0)', (ctx.message.author.id,))
		
		#Each user gets a row for every building in buildingList. All values are set as 0.
		c.execute('SELECT buildingName FROM buildingList')
		buildingNames = c.fetchall()
		for name in buildingNames:
			c.execute('INSERT INTO buildingsIG (discord, buildingName, quantity) VALUES (?, ?, 0)', (ctx.message.author.id, name[0],))

		#Same but for units
		c.execute('SELECT unitName FROM unitList')
		unitNames = c.fetchall()
		for name in unitNames:
			c.execute('INSERT INTO unitsIG (discord, unitName, quantity) VALUES (?, ?, 0)', (ctx.message.author.id, name[0],))


		con.commit()
		await ctx.send(username + " has joined! Adventure awaits, huzzah!")
	else:
		await ctx.send("You're already in the game!")


@bot.command(name = 'leave', aliases = ['l'])
async def leave(ctx):
	c.execute('DELETE FROM township WHERE discord = ?', (ctx.message.author.id,))
	c.execute('DELETE FROM perTurn WHERE discord = ?', (ctx.message.author.id,))
	c.execute('DELETE FROM unitsIG WHERE discord = ?', (ctx.message.author.id,))
	c.execute('DELETE FROM buildingsIG WHERE discord = ?', (ctx.message.author.id,))
	con.commit()
	await ctx.send("You've left the game!")


#DISPAY CURRENT RESOURCES AND SO ON
@bot.command(name = 'display', aliases = ['d'])
async def select(ctx, displayType = None):
	#Display township stats
	if displayType == None or displayType == "Town":
		c.execute('SELECT * FROM township WHERE discord = ?', (ctx.message.author.id,))
		row = c.fetchone()

		#Gets all names from columns, kind of weird
		c.execute('SELECT name FROM PRAGMA_TABLE_INFO(?)', ("township",))
		names = c.fetchall()

		#Specific to each table. Gets the title of the table as a row and also the index from which the embed should start listing
		startpoint = 3
		title = str(row[2]) + "'s Township"
		await ctx.send(embed = displayTown(row, [x[0] for x in names], startpoint, title))

	#Display the perTurn stats
	elif displayType.lower() == "perturn" or displayType.lower() == "pt":
		c.execute('SELECT * FROM perTurn WHERE discord = ?', (ctx.message.author.id,))
		row = c.fetchone()
		c.execute('SELECT name FROM PRAGMA_TABLE_INFO(?)', ("perTurn",))
		names = c.fetchall()
		startpoint = 2
		title = "Resource Per Turn"
		await ctx.send(embed = displayTown(row, [x[0] for x in names], startpoint, title))

	elif displayType.lower() == "buildings" or displayType.lower() == "building":
		c.execute('SELECT buildingName, quantity FROM buildingsIG WHERE discord = ?', (ctx.message.author.id,))
		rows = c.fetchall()
		title = "Buildings"
		await ctx.send(embed = displayBuildingsUnits(rows, title))

	elif displayType.lower() == "units" or displayType.lower() == "unit":
		c.execute('SELECT unitName, quantity FROM unitsIG WHERE discord = ?', (ctx.message.author.id,))
		rows = c.fetchall()
		title = "Units"

		await ctx.send(embed = displayBuildingsUnits(rows, title))
	else:
		await ctx.send("Invalid argument! Try: 'Town', 'perTurn', 'Buildings', or 'Units'")


#Probably add functionality that lets you look at the value per turn table and also lets you look at other people's townships and units and also buildings and everything hahaha


#TURN ACTIONS
@bot.command(name = 'recruit', aliases = ['r'], help = "Spend money to recruit a new unit!")
async def recruit(ctx, unit = None):
	if unit == None or unit == "list":

		c.execute('SELECT * FROM unitList')
		rows = c.fetchall()
		await ctx.send(embed = formatUnits("Units (Cost: [M,F,W,I])", rows))

	else:
		#Setting all the proper variables before parsing them out below. A little unruly, admittedly
		c.execute('SELECT * FROM unitList WHERE unitName = ?', (unit,))
		purchase = c.fetchone()
		c.execute('SELECT quantity FROM buildingsIG WHERE discord = ? AND buildingName = (SELECT requisiteBuilding FROM unitList WHERE unitName = ?)', (ctx.message.author.id,unit,))
		curNumOfBuildings = c.fetchone()
		if not curNumOfBuildings:
			curNumOfBuildings = [0,]
		c.execute('SELECT requisiteQuantity FROM unitList WHERE unitName = ?', (unit,))
		reqNumOfBuildings = c.fetchone()
		c.execute('SELECT popSpace FROM township WHERE discord = ?', (ctx.message.author.id,))
		popSpace = c.fetchone()
		c.execute('SELECT money FROM township WHERE discord = ?', (ctx.message.author.id,))
		curMoney = c.fetchone()
		c.execute('SELECT quantity FROM unitsIG WHERE discord = ? AND unitName = ?', (ctx.message.author.id,unit))
		curNumOfUnits = c.fetchone()


		if popSpace == 0:
			await ctx.send("You don't have enough houses to recruit that unit!")
			return
		elif curMoney[0] < purchase[2]:
			await ctx.send("You don't have enough money to recruit that unit!")
			return
		elif curNumOfBuildings[0] < reqNumOfBuildings[0]:
			await ctx.send("You don't have the proper number of buildings to recruit that unit!")
			return
		elif purchase[3] != None:
			if curNumOfUnits[0] >= curNumOfBuildings[0] * 2:
				await ctx.send("You don't have enough space in your specialty buildings for that unit!")
				return
		
		c.execute('UPDATE unitsIG SET quantity = quantity + 1 WHERE unitName = ? AND discord = ?', (unit, ctx.message.author.id,))
		c.execute('UPDATE township SET money = money - ? WHERE discord = ?', (purchase[2],ctx.message.author.id,))

		#perTurn
		c.execute('UPDATE perTurn SET moneyPerTurn = moneyPerTurn + ?, foodPerTurn = foodPerTurn + ?, woodPerTurn = woodPerTurn + ?, ironPerTurn = ironPerTurn + ?', (purchase[5], purchase[6], purchase[7], purchase[8],))
		#township
		c.execute('UPDATE township SET popSpace = popSpace - 1, attackValue = attackValue + ?, defenseValue = defenseValue + ?, magicValue = magicValue + ?', (purchase[8], purchase[10], purchase[11],))
		con.commit()

		await ctx.send("You have recruited a " + unit + "!")
		return



@bot.command(name = 'expand', aliases = ['e'], help = 'Explore for a new zone to add to your territory! Expends 1 attackValue on use.')
async def expand(ctx, arg = None):
	arg = arg.lower()
	c.execute("SELECT expandCount FROM township WHERE discord = ?", (ctx.message.author.id,))
	eCount = c.fetchone()[0]
	if arg == "list" or arg == "l":
		eDiffs = [eCount - 2 if eCount - 2 > 0 else 0, eCount + 2]
		await ctx.send("The cost of acquiring a new zone is " + str(expandCost(eCount)) + " food and will require between " + str(eDiffs[0]) + "-" + str(eDiffs[1]) + " attackValue.")
		return
	else:
		buildingSlots, clearDifficulty, acquireCost = generateExpand(eCount)
		c.execute('SELECT attackValue, food FROM township WHERE discord = ?', (ctx.message.author.id,))
		value = c.fetchone()
		if value[0] < clearDifficulty:
			await ctx.send("You have found a new tile with slots:" + str(buildingSlots) + ", difficulty: " + str(clearDifficulty) + ", cost: " + str(acquireCost) + ". However, you don't have enough attackValue to acquire it.")
			return
		elif value[1] < acquireCost:
			await ctx.send("You have found a new tile with slots:" + str(buildingSlots) + ", difficulty: " + str(clearDifficulty) + ", cost: " + str(acquireCost) + ". However, you don't have enough food to acquire it.")
			return
		else:
			await ctx.send("You have acquired a new tile with slots:" + str(buildingSlots) + ", difficulty: " + str(clearDifficulty) + ", cost: " + str(acquireCost) + "!")
			c.execute('UPDATE township SET buildingSpace = buildingSpace + ?, food = food - ? WHERE discord = ?', (buildingSlots, acquireCost, ctx.message.author.id,))
			con.commit()
			return





@bot.command(name = 'build', aliases = ['b'], help = 'Specify building to buy or leave empty for a list.')
async def build(ctx, building = None):
	if building == None or building == "list":

		#List buildings
		c.execute('SELECT * FROM buildingList')
		rows = c.fetchall()
		await ctx.send(embed = formatBuildings("Building Cost (Wood/Iron)", rows))

	else:
		#Check if player has enough resources
		c.execute('SELECT * FROM township WHERE discord = ?', (ctx.message.author.id,))
		playerResources = c.fetchone()
		c.execute('SELECT * FROM buildingList WHERE buildingName = ?', (building,))
		purchase = c.fetchone()

		#8 is popSpace. 5 is wood. 6 is iron.
		if playerResources[8] <= 0:
			await ctx.send("You don't have enough space to build that!")
			return
		elif playerResources[5] < purchase[2]:
			await ctx.send("You don't have enough wood to build that!")
			return
		elif playerResources[6] < purchase[3]:
			await ctx.send("You don't have enough iron to build that!")
			return
		else:

			c.execute('UPDATE buildingsIG SET quantity = quantity + 1 WHERE buildingName = ? AND discord = ?', (building, ctx.message.author.id,))
			c.execute('UPDATE township SET wood = wood - ?, iron = iron - ?, popSpace = popSpace + ?, buildingSpace = buildingSpace - 1 WHERE discord = ?', (purchase[2],purchase[3],purchase[4],ctx.message.author.id,))
			con.commit()

			await ctx.send("You have built a " + building + "!")
			return


#This is the attack feature
@bot.command(name = 'pillage', aliases = ['p'], help = "Expend 1 attackValue to steal resources from a random player. Lose an extra (and gain no resources) on a failure.")
async def pillage(ctx):
	c.execute('SELECT * FROM township WHERE discord != ?', (ctx.message.author.id,))
	target = random.choice(c.fetchall())

	c.execute('SELECT * FROM township WHERE discord = ?', (ctx.message.author.id,))
	attacker = c.fetchone()

	if attacker[9] > target[10]:
		#attacker victory
		c.execute('UPDATE township SET money = money + ?, food = food + ?, wood = wood + ?, iron = iron + ?, attackValue = attackValue - 1 WHERE discord = ?', (round(target[3] * .1), round(target[4] * .1), round(target[5] * .1), round(target[6] * .1), attacker[1],))
		c.execute('UPDATE township SET money = money - ?, food = food - ?, wood = wood - ?, iron = iron - ? WHERE discord = ?', (round(target[3] * .1), round(target[4] * .1), round(target[5] * .1), round(target[6] * .1), target[1],))
		con.commit()
		await ctx.send("You have successfully raided " + str(target[2]) + " and stolen: " + str(target[3]) + " money, " + str(target[4]) + " food, " + str(target[5]) + " wood, and " + str(target[6]) + " iron! Huzzah!")	
	else:
		#defender victory
		c.execute('UPDATE township SET attackValue = attackValue - 2 WHERE discord = ?', (attacker[1],))
		await ctx.send("You have failed to raid " + str(target[2]) + "and have lost an extra attackValue!")
	return

@bot.command(name = 'adventure', aliases = ['a'])
async def adventure(ctx):
	aDiff, reward = generateAdventure()
	c.execute('SELECT money, food, wood, iron, attackValue FROM township WHERE discord = ?', (ctx.message.author.id,))
	values = c.fetchone()

	if values[4] >= aDiff[0]:
		await ctx.send("You have found " + aDiff[1] + " and slayed it! Your township has gained: " + str(reward[0]) + " money, " + str(reward[1]) + " food, " + str(reward[2]) + " wood, and " + str(reward[3]) + " iron! Huzzah!")
		c.execute('UPDATE township SET money = money + ?, food = food + ?, wood = wood + ?, iron = iron + ? WHERE discord = ?', (reward[0],reward[1],reward[2],reward[3],ctx.message.author.id))
		return	
	else:
		await ctx.send("You have found " + aDiff[1] + " but you don't have enough strength to slay it! Your warriors have ran away!")
		return



#Much cuter now that the csvs are set up 
@bot.command(name = 'refreshLists', aliases = ['refresh'], help = 'Supplies the values that populate the building/unit tables.')
async def refreshLists(ctx):

	c.execute('DELETE FROM unitList')
	c.execute('DELETE FROM buildingList')
	con.commit()

	unitsCSV = "./feudalBotUnits.csv"
	df = pandas.read_csv(unitsCSV)
	df.to_sql("unitList", con, if_exists = "append", index = False)

	buildingsCSV = "./feudalBotBuildings.csv"
	df = pandas.read_csv(buildingsCSV)
	df.to_sql("buildingList", con, if_exists = "append", index = False)
	con.commit()

	await ctx.send("Tables successfully refreshed!")


async def timer():
	while True:
		await asyncio.sleep(30)
		c.execute('SELECT * FROM township')
		players = c.fetchall()
		for player in players:
			c.execute('SELECT * FROM perTurn WHERE discord = ?', (player[1],))
			modifiers = c.fetchone()
			c.execute('UPDATE township SET money = money + ?, food = food + ?, wood = wood + ?, iron = iron + ? WHERE discord = ?', (modifiers[2], modifiers[3], modifiers[4], modifiers[5], player[1],))
		con.commit()


#COMMENCE!
bot.run(TOKEN)