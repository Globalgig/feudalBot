import discord
import os
import sqlite3, csv
import pandas
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
	c.execute('CREATE TABLE IF NOT EXISTS township (id integer PRIMARY KEY, discord integer, name varchar(255), money integer DEFAULT 10, food integer DEFAULT 100, wood integer DEFAULT 0, iron integer DEFAULT 0, popSpace integer DEFAULT 8, buildingSpace integer, attackValue integer DEFAULT 0, defenseValue integer DEFAULT 0, magicValue integer DEFAULT 0)')
	c.execute('CREATE TABLE IF NOT EXISTS perTurn (id integer PRIMARY KEY, discord integer, moneyPerTurn integer DEFAULT 0, foodPerTurn integer DEFAULT 0, woodPerTurn integer DEFAULT 0, ironPerTurn integer DEFAULT 0)')
	c.execute('CREATE TABLE IF NOT EXISTS unitList (id integer PRIMARY KEY, unitName varchar(255), cost integer, requisiteBuilding varchar(255), requisiteQuantity integer, moneyPerTurn integer, foodPerTurn integer, woodPerTurn integer, ironPerTurn integer, attackValue integer, defenseValue integer, magicValue integer)')
	c.execute('CREATE TABLE IF NOT EXISTS buildingList (id integer PRIMARY KEY, buildingName varchar(255), woodCost integer, ironCost integer)')
	c.execute('CREATE TABLE IF NOT EXISTS unitsIG (id integer PRIMARY KEY, discord integer, unitName varchar(255), quantity integer DEFAULT 0)')
	c.execute('CREATE TABLE IF NOT EXISTS buildingsIG (id integer PRIMARY KEY, discord integer, buildingName varchar(255), quantity integer DEFAULT 0)')
	con.commit()


#JOIN AND LEAVE COMMANDS
@bot.command(name = 'join', aliases = ['j', 'participate', 'enter', 'start', 'begin'], help = 'Enter ruler name to start your village.')
async def join(ctx, username):

	#Check if the player already has an ID
	identical = c.execute('SELECT * FROM township WHERE discord = ?', (ctx.message.author.id,))
	row = c.fetchone()
	if not row:
		c.execute('INSERT INTO township (discord, name, money, food, wood, iron, popSpace, buildingSpace, attackValue, defenseValue, magicValue) VALUES (?, ?, 100, 100, 50, 0, 8, 4, 0, 0, 0)', (ctx.message.author.id, username,))
		c.execute('INSERT INTO perTurn (discord, moneyPerTurn, foodPerTurn, woodPerTurn, ironPerTurn) VALUES (?, 0, 0, 0, 0)', (ctx.message.author.id,))
		
		#Creates a row for every building in the buildingsIG table for every discord user joined where the quantity is 0
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
		title = "Township"

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
@bot.command(name = 'recruit', aliases = ['r'])
async def recruit(ctx, unit = None):
	if unit == None or unit == "list":

		c.execute('SELECT * FROM unitList')
		rows = c.fetchall()
		await ctx.send(embed = formatRows("Units (Cost)", rows))

		#Really weird join that should show the units which the player *could* buy given their buildings. What's the use though? Who knows.
		# c.execute('SELECT * FROM unitList u LEFT JOIN buildingsIG b on u.requisiteBuilding = b.buildingName WHERE u.requisiteQuantity >= b.quantity and b.discord = ?', (ctx.message.author.id,))
		# rows = c.fetchall()
		# await ctx.send(embed = formatRows("Units (Cost)", rows))


	else:
		c.execute('SELECT * FROM unitList WHERE unitName = ?', (unit,))
		purchase = c.fetchone()
		c.execute('SELECT quantity FROM buildingsIG WHERE discord = ? AND buildingName = (SELECT requisiteBuilding FROM unitList WHERE unitName = ?)', (ctx.message.author.id,unit,))
		curNumOfBuildings = c.fetchone()
		if not curNumOfBuildings:
			curNumOfBuildings = 0
		c.execute('SELECT requisiteQuantity FROM unitList WHERE unitName = ?', (unit,))
		reqNumOfBuildings = c.fetchone()
		c.execute('SELECT popSpace FROM township WHERE discord = ?', (ctx.message.author.id,))
		popSpace = c.fetchone()
		c.execute('SELECT money FROM township WHERE discord = ?', (ctx.message.author.id,))
		curMoney = c.fetchone()


		#create a category somewhere that figures out available space (from buildings, not buildingSpace)
		#and factors in population limit

		if popSpace == 0:
			await ctx.send("You don't have enough space to recruit that unit!")
			return
		elif curMoney[0] < purchase[2]:
			await ctx.send("You don't have enough money to recruit that unit!")
			return
		elif curNumOfBuildings < reqNumOfBuildings[0]:
			await ctx.send("You don't have the proper number of buildings to recruit that unit!")
			return
		else:
			c.execute('UPDATE unitsIG SET quantity = quantity + 1 WHERE unitName = ? AND discord = ?', (unit, ctx.message.author.id,))
			c.execute('UPDATE township SET money = money - ? WHERE discord = ?', (purchase[2],ctx.message.author.id,))

			#perTurn
			c.execute('UPDATE perTurn SET moneyPerTurn = moneyPerTurn + ?, foodPerTurn = foodPerTurn + ?, woodPerTurn = woodPerTurn + ?, ironPerTurn = ironPerTurn + ?', (purchase[5], purchase[6], purchase[7], purchase[8],))
			#township
			c.execute('UPDATE township SET popSpace = popSpace - 1, attackValue = attackValue + ?, defenseValue = defenseValue + ?, magicValue = magicValue + ?', (purchase[8], purchase[10], purchase[11],))
			con.commit()

			await ctx.send("You have recruited a " + unit + "!")
			endTurn(ctx)
			return



@bot.command(name = 'explore', aliases = ['e'], help = 'Explore for a new zone to add to your territory!')
async def explore(ctx):
	b, m = generateExplore()
	await ctx.send(b, m)

	await ctx.send("Not implemented! However, your turn has still ended.")
	endTurn(ctx)
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
		c.execute('SELECT buildingSpace, wood, iron FROM township WHERE discord = ?', (ctx.message.author.id,))
		playerResources = c.fetchone()
		c.execute('SELECT * FROM buildingList WHERE buildingName = ?', (building,))
		purchase = c.fetchone()

		if playerResources[9] <= 0:
			await ctx.send("You don't have enough space to build that!")
			return
		elif playerResources[6] < purchase[1]:
			await ctx.send("You don't have enough wood to build that!")
			return
		elif playerResources[7] < purchase[2]:
			await ctx.send("You don't have enough iron to build that!")
			return
		else:

			c.execute('UPDATE buildingsIG SET quantity = quantity + 1 WHERE buildingName = ? AND discord = ?', (building, ctx.message.author.id,))
			c.execute('UPDATE township SET wood = wood - ?, iron = iron - ? WHERE discord = ?', (purchase[1],purchase[2],ctx.message.author.id,))

			#So far buildings don't really have an effect. They just provide slots for people
			await ctx.send("You have built a " + building + "!")
			endTurn(ctx)
			return


#This is supposed to be like the attack feature
@bot.command(name = 'pillage', alisases = ['p'])
async def pillage(ctx, target):
	#implement
	await ctx.send("Not implemented! However, your turn has still ended.")
	endTurn(ctx)
	return


#Much cuter now that the csvs are set up 
@bot.command(name = 'setupGame', alisases = ['setup'], help = 'Supplies the values that populate the building/unit tables.')
async def setupGame(ctx):
	unitsCSV = "./feudalBotUnits.csv"
	df = pandas.read_csv(unitsCSV)
	df.to_sql("unitList", con, if_exists = "append", index = False)

	buildingsCSV = "./feudalBotBuildings.csv"
	df = pandas.read_csv(buildingsCSV)
	df.to_sql("buidingList", con, if_exists = "append", index = False)
	con.commit()

	await ctx.send("Game successfully setup!")


def endTurn(ctx):
	c.execute('SELECT * FROM perTurn WHERE discord = ?', (ctx.message.author.id,))
	modifiers = c.fetchone()

	c.execute('UPDATE township SET money = money + ?, food = food + ?, wood = wood + ?, iron = iron + ? WHERE discord = ?', (modifiers[2], modifiers[3], modifiers[4], modifiers[5], ctx.message.author.id,))
	con.commit()
	return

#COMMENCE!
bot.run(TOKEN)