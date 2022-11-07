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

# Mysteriously, find_env only worked when I specified the .env file name
load_dotenv('environment/feudalBot.env')
TOKEN = os.getenv('DISCORD_TOKEN')

con = sqlite3.connect('feudalBot.db')
c = con.cursor()
turn_timer = 60

bot = commands.Bot(command_prefix='^')

# Setup tables and begin timer
@bot.event
async def on_ready():
	with open("tables/tableSetup.txt") as tableFile:
		for line in tableFile:
			c.execute(line)
	con.commit()
	print("Tables setup!")

	# Populate csv-based tables
	unitsCSV = "csvs/units.csv"
	df = pandas.read_csv(unitsCSV)
	df.to_sql("units", con, if_exists = "append", index = False)

	buildingsCSV = "csvs/buildings.csv"
	df = pandas.read_csv(buildingsCSV)
	df.to_sql("buildings", con, if_exists = "append", index = False)
	con.commit()
	print("CSV-based tables populated!")
	
	await timer()

@bot.command(name = 'begin')
async def begin(ctx):
	c.execute('SELECT * FROM township WHERE guildId = ?', (ctx.message.guild.id,))
	row = c.fetchone()
	if not row:
		c.execute('INSERT INTO township (guildId, name) VALUES (?, "help")', (ctx.message.guild.id,))
		c.execute('INSERT INTO resources (guildId) VALUES (?)', (ctx.message.guild.id,))
		con.commit()
	else:
		ctx.send("There is already an active game in this server!")

# DISPLAY 
@bot.command(name = 'display', aliases = ['d'])
async def display(ctx, displayType):
	displayType = displayType.lower()

	# Default display township resources page
	if displayType in ["resources", "resource", "r"]:
		c.execute('SELECT * FROM resources WHERE guildId = ?', (ctx.message.guild.id,))
		row = c.fetchone()
		await ctx.send(embed = generateResourceEmbed(row))
		return

	if displayType in ["township", "t"]:
		c.execute('SELECT level, daysPassed FROM township WHERE guildId = ?', (ctx.message.guild.id,))
		row = c.fetchone()
		await ctx.send(embed = generateTownshipEmbed(row))
		return

# BUILD
@bot.command(name = "build", aliases = ['b'])
async def build(ctx, buildingName):
	buildingName = buildingName.lower()
	c.execute('SELECT * FROM buildingsAcquired WHERE guildID = ? AND name = ?', (ctx.message.guild.id, buildingName))
	row = c.fetchone()
	if not row:
		c.execute('SELECT * FROM buildings WHERE name = ?', (buildingName,))
		building = c.fetchone()
		c.execute('SELECT wood, stone, metal, power, crystals FROM resources WHERE guildId = ?', (ctx.message.guild.id,))
		resources = c.fetchone()
		c.execute('SELECT level FROM township WHERE guildId = ?', (ctx.message.guild.id,))
		level = c.fetchone()[0]

		if level < building[2]:
			await ctx.send("Not high enough level!")
			return
		elif resources[0] < building[3]:
			await ctx.send("Not enough wood!")
			return
		elif resources[1] < building[4]:
			await ctx.send("Not enough stone!")
			return
		elif resources[2] < building[5]:
			await ctx.send("Not enough metal!")
			return
		elif resources[3] < building[6]:
			await ctx.send("Not enough power!")
			return
		elif resources[4] < building[7]:
			await ctx.send("Not enough crystals!")
			return
		else:
			c.execute('INSERT INTO buildingsAcquired (guildId, name) VALUES (?, ?)', (ctx.message.guild.id, buildingName))
			c.execute('UPDATE resources SET food = food - ?, wood = wood -?, stone = stone - ?, metal = metal - ?, power = power - ?, crystals = crystals - ? WHERE guildId = ?', (building[3], building[4], building[5], building[6], building[7], building[8], ctx.message.guild.id,))
			con.commit()
			await ctx.send("Built a: " + buildingName)
	else:
		await ctx.send("Building is either already purchased or not found!")

# UPGRADE
@bot.command(name = "upgrade", aliases = ['u'])
async def upgrade(ctx):
	c.execute('SELECT level from township where guildId = ?', (ctx.message.guild.id,))
	level = c.fetchone()[0]
	c.execute('SELECT food, wood, stone, metal, power, crystals FROM resources WHERE guildId = ?', (ctx.message.guild.id,))
	resources = c.fetchone()

	upgradeValue = 100 * pow(2, level)

	if resources[0] < upgradeValue:
		await ctx.send("Not enough food!")
		return
	elif resources[1] < upgradeValue:
		await ctx.send("Not enough wood!")
		return
	elif resources[2] < upgradeValue:
		await ctx.send("Not enough stone!")
		return
	elif resources[3] < upgradeValue:
		await ctx.send("Not enough metal!")
		return
	elif resources[4] < upgradeValue:
		await ctx.send("Not enough power!")
		return
	elif resources[5] < upgradeValue:
		await ctx.send("Not enough crystals!")
		return
	else:
		c.execute('UPDATE township SET level = level + 1 WHERE guildId = ?', (ctx.message.guild.id,))
		c.execute('UPDATE resources SET food = food - ?, wood = wood -?, stone = stone - ?, metal = metal - ?, power = power - ?, crystals = crystals - ? WHERE guildId = ?', (upgradeValue, upgradeValue, upgradeValue, upgradeValue, upgradeValue, upgradeValue, ctx.message.guild.id,))
		con.commit()
		await ctx.send("Upgraded town hall to level : " + str(level + 1))



#DISPAY CURRENT RESOURCES AND SO ON
# @bot.command(name = 'display')
# async def select(ctx, displayType = None):
# 	#Display township stats
# 	if displayType == None or displayType == "Town":
# 		c.execute('SELECT * FROM township WHERE discord = ?', (ctx.message.author.id,))
# 		row = c.fetchone()

# 		#Gets all names from columns, kind of weird
# 		c.execute('SELECT name FROM PRAGMA_TABLE_INFO(?)', ("township",))
# 		names = c.fetchall()

# 		#Specific to each table. Gets the title of the table as a row and also the index from which the embed should start listing
# 		startpoint = 3
# 		title = str(row[2]) + "'s Township"
# 		await ctx.send(embed = displayTown(row, [x[0] for x in names], startpoint, title))

# 	#Display the perTurn stats
# 	elif displayType.lower() == "perturn" or displayType.lower() == "pt":
# 		c.execute('SELECT * FROM perTurn WHERE discord = ?', (ctx.message.author.id,))
# 		row = c.fetchone()
# 		c.execute('SELECT name FROM PRAGMA_TABLE_INFO(?)', ("perTurn",))
# 		names = c.fetchall()
# 		startpoint = 2
# 		title = "Resource Per Turn"
# 		await ctx.send(embed = displayTown(row, [x[0] for x in names], startpoint, title))

# 	elif displayType.lower() == "buildings" or displayType.lower() == "building":
# 		c.execute('SELECT buildingName, quantity FROM buildingsIG WHERE discord = ?', (ctx.message.author.id,))
# 		rows = c.fetchall()
# 		title = "Buildings"
# 		await ctx.send(embed = displayBuildingsUnits(rows, title))

# 	elif displayType.lower() == "units" or displayType.lower() == "unit":
# 		c.execute('SELECT unitName, quantity FROM unitsIG WHERE discord = ?', (ctx.message.author.id,))
# 		rows = c.fetchall()
# 		title = "Units"

# 		await ctx.send(embed = displayBuildingsUnits(rows, title))
# 	else:
# 		await ctx.send("Invalid argument! Try: 'Town', 'perTurn', 'Buildings', or 'Units'")
#Probably add functionality that lets you look at the value per turn table and also lets you look at other people's townships and units and also buildings and everything hahaha



@bot.command(name = 'recruit', aliases = ['r'], help = "Spend money to recruit a new unit! New units use up 1 popSpace.")
async def recruit(ctx, unit = ""):
	unit = unit.lower()
	if unit == "" or unit == "list" or unit == "l":
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

		#Here's the actual parsing of the variables
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
		c.execute('UPDATE perTurn SET moneyPerTurn = moneyPerTurn + ?, foodPerTurn = foodPerTurn + ?, woodPerTurn = woodPerTurn + ?, ironPerTurn = ironPerTurn + ? WHERE discord = ?', (purchase[5], purchase[6], purchase[7], purchase[8],ctx.message.author.id,))
		#township
		c.execute('UPDATE township SET popSpace = popSpace - 1, attackValue = attackValue + ?, defenseValue = defenseValue + ?, magicValue = magicValue + ? WHERE discord = ?', (purchase[8], purchase[10], purchase[11],ctx.message.author.id,))
		con.commit()

		await ctx.send("You have recruited a " + unit + "!")
		return



@bot.command(name = 'expand', aliases = ['e'], help = 'Explore for a new zone to add to your territory! Expends 1 attackValue on use.')
async def expand(ctx, arg = ""):
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




#This is the attack feature
@bot.command(name = 'pillage', aliases = ['p'], help = "Expend 1 attackValue to steal resources from a random player. Lose an extra (and gain no resources) on a failure.")
async def pillage(ctx):
	c.execute('SELECT * FROM township WHERE discord != ?', (ctx.message.author.id,))
	target = random.choice(c.fetchall())

	c.execute('SELECT * FROM township WHERE discord = ?', (ctx.message.author.id,))
	attacker = c.fetchone()

	if attacker[9] > target[10]:
		#attacker victory
		#Calculates the percent that should be stolen. More should be stolen in closer fights so strong players don't benefit from preying on weak players.
		percentStolen = round(1 - (attacker[9]/(attacker[9] + defender[10])),1)


		c.execute('UPDATE township SET money = money + ?, food = food + ?, wood = wood + ?, iron = iron + ?, attackValue = attackValue - 1 WHERE discord = ?', (round(target[3] * percentStolen), round(target[4] * percentStolen), round(target[5] * percentStolen), round(target[6] * percentStolen), attacker[1],))
		c.execute('UPDATE township SET money = money - ?, food = food - ?, wood = wood - ?, iron = iron - ? WHERE discord = ?', (round(target[3] * percentStolen), round(target[4] * percentStolen), round(target[5] * percentStolen), round(target[6] * percentStolen), target[1],))
		con.commit()
		await ctx.send("You have successfully raided " + str(target[2]) + " and stolen " + percentStolen + "% of their supplies. Your bounty is: " + str(target[3]) + " money, " + str(target[4]) + " food, " + str(target[5]) + " wood, and " + str(target[6]) + " iron! Huzzah!")	
	else:
		#defender victory
		c.execute('UPDATE township SET attackValue = attackValue - 2 WHERE discord = ?', (attacker[1],))
		await ctx.send("You have failed to raid " + str(target[2]) + "and have lost an extra attackValue!")
	return



@bot.command(name = 'adventure', aliases = ['a'], help = "Send your troops to fight for supplies! Expends 1 attackValue on use and an extra on a loss/ties.")
async def adventure(ctx, arg = ""):
	arg = arg.lower()
	c.execute("SELECT adventureCount FROM township WHERE discord = ?", (ctx.message.author.id,))
	aCount = c.fetchone()[0]
	if arg == "list" or arg == "l":
		#aDiffs is the potential range of aDiff. Purely for user purposes
		aDiffs = [aCount - 3 if aCount - 2 > 0 else 0, aCount + 3]
		await ctx.send("Your next adventure will have a difficulty of " + str(aDiffs[0]) + "-" + str(aDiffs[1]) + ".")
		return
	else:
		aDiff, reward = generateAdventure(aCount)
		c.execute('SELECT money, food, wood, iron, attackValue FROM township WHERE discord = ?', (ctx.message.author.id,))
		values = c.fetchone()

		if values[4] > aDiff[0]:
			await ctx.send("You have found a " + aDiff[1] + " and slayed it! Your township has gained: " + str(reward[0]) + " money, " + str(reward[1]) + " food, " + str(reward[2]) + " wood, and " + str(reward[3]) + " iron! Huzzah!")
			c.execute('UPDATE township SET money = money + ?, food = food + ?, wood = wood + ?, iron = iron + ?, attackValue = attackValue - 1 WHERE discord = ?', (reward[0],reward[1],reward[2],reward[3],ctx.message.author.id))
			
			#Catch statment to ensure no negative attackValues
			if values[4] < 1:
				c.execute('UPDATE township SET attackValue = 0 WHERE discord = ?', (ctx.message.author.id,))
			return	

		else:
			await ctx.send("You have found a " + aDiff[1] + " but you don't have enough strength to slay it! Your warriors have ran away, losing an extra attackValue!")
			c.execute('UPDATE township SET attackValue = attackValue - 2 WHERE discord = ?', (ctx.message.author.id,))

			#Catch statment to ensure no negative attackValues
			if values[4] < 2:
				c.execute('UPDATE township SET attackValue = 0 WHERE discord = ?', (ctx.message.author.id,))
			return



@bot.command(name = 'cast', help = "Invoke powerful spells at the cost of money. Use the 'list' argument to display all available spells.")
async def cast(ctx, arg = ""):
	arg = arg.lower()
	c.execute("SELECT magicValue FROM township WHERE discord = ?", (ctx.message.author.id,))
	mValue = c.fetchone()[0]
	if arg == "" or arg == "list" or arg == "l":
		c.execute('SELECT * FROM spellList')
		rows = c.fetchall()
		await ctx.send(embed = formatUnits("Units (Cost: [M,F,W,I])", rows))
	else:
		await ctx.send("Not implemented yet!")




#Much cuter now that the csvs are set up 
@bot.command(name = 'refreshLists', aliases = ['refresh'], help = 'Supplies the values that populate the building/unit tables.')
async def refreshLists(ctx):

	c.execute('DELETE FROM unitList')
	c.execute('DELETE FROM buildingList')
	con.commit()

	unitsCSV = "csvs/units.csv"
	df = pandas.read_csv(unitsCSV)
	df.to_sql("unitList", con, if_exists = "append", index = False)

	buildingsCSV = "csvs/buildings.csv"
	df = pandas.read_csv(buildingsCSV)
	df.to_sql("buildingList", con, if_exists = "append", index = False)
	con.commit()

	await ctx.send("Tables successfully refreshed!")



# @bot.command(name = "tutorial", aliases = ['t'], help = "DMs a guide for new players.")
# async def tutorial(ctx):
# 	await ctx.message.author.send(embed = displayTutorial())


# Basic Actions
@bot.command(name = "gather", aliases = ['g'], help = "Returns a small amount of every available resource.")
async def gather(ctx):
	c.execute('SELECT level FROM township WHERE guildId = ?', (ctx.message.guild.id,))
	level = c.fetchone()

	resources = [random.randint(0, 10 * (level[0] + 1)) for _ in range(6)]
	c.execute('UPDATE resources SET food = food + ?, wood = wood + ?, stone = stone + ?, metal = metal + ?, power = power + ?, crystals = crystals + ? WHERE guildId = ?', (resources[0], resources[1], resources[2], resources[3], resources[4], resources[5], ctx.message.guild.id,))
	con.commit()

@bot.command(name = "forage", aliases = ['f'], help = "Returns a medium amount of food.")
async def forage(ctx):
	c.execute('SELECT level FROM township WHERE guildId = ?', (ctx.message.guild.id,))
	level = c.fetchone()

	resource = random.randint(0, 30 * (level[0] + 1))
	c.execute('UPDATE resources SET food = food + ? WHERE guildId = ?', (resource, ctx.message.guild.id,))
	con.commit()

@bot.command(name = "woodcut", aliases = ['w'], help = "Returns a medium amount of wood.")
async def woodcut(ctx):
	c.execute('SELECT level FROM township WHERE guildId = ?', (ctx.message.guild.id,))
	level = c.fetchone()

	resource = random.randint(0, 30 * (level[0] + 1))
	c.execute('UPDATE resources SET wood = wood + ? WHERE guildId = ?', (resource, ctx.message.guild.id,))
	con.commit()

@bot.command(name = "mine", aliases = ['m'], help = "Returns a medium amount of stone.")
async def mine(ctx):
	c.execute('SELECT level FROM township WHERE guildId = ?', (ctx.message.guild.id,))
	level = c.fetchone()

	resource = random.randint(0, 30 * (level[0] + 1))
	c.execute('UPDATE resources SET stone = stone + ? WHERE guildId = ?', (resource, ctx.message.guild.id,))
	con.commit()

@bot.command(name = "smith", aliases = ['s'], help = "Returns a medium amount of metal.")
async def smith(ctx):
	c.execute('SELECT level FROM township WHERE guildId = ?', (ctx.message.guild.id,))
	level = c.fetchone()

	resource = random.randint(0, 30 * (level[0] + 1))
	c.execute('UPDATE resources SET metal = metal + ? WHERE guildId = ?', (resource, ctx.message.guild.id,))
	con.commit()

@bot.command(name = "train", aliases = ['t'], help = "Returns a medium amount of power.")
async def train(ctx):
	c.execute('SELECT level FROM township WHERE guildId = ?', (ctx.message.guild.id,))
	level = c.fetchone()

	resource = random.randint(0, 30 * (level[0] + 1))
	c.execute('UPDATE resources SET power = power + ? WHERE guildId = ?', (resource, ctx.message.guild.id,))
	con.commit()

@bot.command(name = "crystalhunt", aliases = ['c'], help = "Returns a medium amount of crystals.")
async def crystalhunt(ctx):
	c.execute('SELECT level FROM township WHERE guildId = ?', (ctx.message.guild.id,))
	level = c.fetchone()

	resource = random.randint(0, 30 * (level[0] + 1))
	c.execute('UPDATE resources SET crystals = crystals + ? WHERE guildId = ?', (resource, ctx.message.guild.id,))
	con.commit()

# Resource addition loop
async def timer():
	while True:
		await asyncio.sleep(turn_timer)
		c.execute('UPDATE resources SET food = food + foodPer, wood = wood + woodPer, stone = stone + stonePer, metal = metal + metalPer, power = power + powerPer, crystals = crystals + crystalsPer',)
		con.commit()

# COMMENCE!
bot.run(TOKEN)