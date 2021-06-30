import discord
import os
import sqlite3
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
	c.execute('CREATE TABLE IF NOT EXISTS township (id integer PRIMARY KEY, discord integer, name varchar(255), money integer DEFAULT 10, food integer DEFAULT 100, wood integer DEFAULT 0, iron integer DEFAULT 0, maxPopulation integer DEFAULT 4, curPopulation integer DEFAULT 0, buildingSpace integer, attackValue integer DEFAULT 0, defenseValue integer DEFAULT 0)')
	c.execute('CREATE TABLE IF NOT EXISTS resourceMods (id integer PRIMARY KEY, discord integer, moneyPerTurn integer DEFAULT 0, foodPerTurn integer DEFAULT 0, woodPerTurn integer DEFAULT 0, ironPerTurn integer DEFAULT 0)')
	c.execute('CREATE TABLE IF NOT EXISTS unitList (id integer PRIMARY KEY, unitName varchar(255), cost integer, requisiteBuilding varchar(255), requisiteQuantity integer)')
	c.execute('CREATE TABLE IF NOT EXISTS buildingList (id integer PRIMARY KEY, buildingName varchar(255), cost integer)')
	c.execute('CREATE TABLE IF NOT EXISTS unitsIG (id integer PRIMARY KEY, discord integer, unitName varchar(255), quantity integer DEFAULT 0)')
	c.execute('CREATE TABLE IF NOT EXISTS buildingsIG (id integer PRIMARY KEY, discord integer, buildingName varchar(255), cost integer, quantity integer DEFAULT 0)')
	con.commit()


#JOIN AND LEAVE COMMANDS
@bot.command(name = 'join', aliases = ['j', 'participate', 'enter', 'start', 'begin'], help = 'Enter ruler name to start your village.')
async def join(ctx, name):

	#Check if the player already has an ID
	identical = c.execute('SELECT * FROM township WHERE discord = ?', (ctx.message.author.id,))
	row = c.fetchone()
	if not row:
		c.execute('INSERT INTO township (discord, name, money, food, wood, iron, maxPopulation, curPopulation, buildingSpace, attackValue, defenseValue) VALUES (?, ?, 0, 0, 0, 0, 0, 0, 8, 0, 0)', (ctx.message.author.id, name,))
		con.commit()
		await ctx.send(name + " has joined! Adventure awaits, huzzah!")

	else:
		await ctx.send("You're already in the game!")


@bot.command(name = 'leave', aliases = ['l'])
async def leave(ctx):
	c.execute('DELETE FROM township WHERE discord = ?', (ctx.message.author.id,))
	c.execute('DELETE FROM resourceMods WHERE discord = ?', (ctx.message.author.id,))
	c.execute('DELETE FROM unitsIG WHERE discord = ?', (ctx.message.author.id,))
	c.execute('DELETE FROM buildingsIG WHERE discord = ?', (ctx.message.author.id,))
	con.commit()
	await ctx.send("You've left the game!")


#DISPAY CURRENT RESOURCES AND SO ON
@bot.command(name = 'display', aliases = ['d', 'displayTown', 'stats'])
async def select(ctx):
	c.execute('SELECT * FROM township WHERE discord = ?', (ctx.message.author.id,))
	row = c.fetchone()

	#Gets all names from columns, kind of weird
	c.execute('SELECT name FROM PRAGMA_TABLE_INFO(?)', ("township",))
	names = c.fetchall()

	await ctx.send(embed = displayTown(row, [x[0] for x in names]))


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

	#implement a way for all units to be shown not just the ones you are capable of buying

	else:
		c.execute('SELECT * FROM unitList WHERE unitName = ?', (unit,))
		purchase = c.fetchone()
		c.execute('SELECT quantity FROM buildingsIG WHERE discord = ? AND buildingName = (SELECT requisiteBuilding FROM unitList WHERE unitName = ?)', (ctx.message.author.id,unit,))
		curNumOfBuildings = c.fetchone()
		c.execute('SELECT requisiteQuantity FROM unitList where unitName = ?', (unit,))
		reqNumOfBuildings = c.fetchone()

		#create a category somewhere that figures out available space (from buildings, not buildingSpace)
		#and factors in population limit

		if curNumOfBuildings[0] >= reqNumOfBuildings[0]:
			c.execute('UPDATE unitsIG SET quantity = quantity + 1 WHERE unitName = ? AND discord = ?', (unit, ctx.message.author.id,))
			c.execute('UPDATE township SET money = money - ? WHERE discord = ?', (purchase[2],ctx.message.author.id,))

			#implement something that parses the effect of recruiting a unit, probably in another file lmao



@bot.command(name = 'explore', aliases = ['e'], help = 'Explore for a new zone to add to your territory!')
async def explore(ctx):
	b, m = generateExplore()
	await ctx.send(b, m)

	#probably repurpose the RandomEncounters into RandomEncounters&Interpreters



@bot.command(name = 'build', aliases = ['b'], help = 'Specify building to buy or leave empty for a list.')
async def build(ctx, building = None):
	if building == None or building == "list":

		#List buildings
		c.execute('SELECT * FROM buildingList')
		rows = c.fetchall()
		await ctx.send(embed = formatRows("Buildings (Cost)", rows))

	else:
		#Check if player has enoughs space
		c.execute('SELECT buildingSpace FROM township WHERE discord = ?', (ctx.message.author.id,))
		spaceAvail = c.fetchone()
		print(spaceAvail)
		if spaceAvail[0] <= 0:
			await ctx.send("You don't have enough space!")
			return
		#Passes the preliminary space check
		else:
			#Must cast building variable as a str before querying. Why?
			c.execute('SELECT * FROM buildingList WHERE buildingName = ?', (str(building),))
			purchase = c.fetchone()

			#TODO: Add in a check to see if they have enough money

			c.execute('UPDATE buildingsIG SET quantity = quantity + 1 WHERE buildingName = ? AND discord = ?', (building, ctx.message.author.id,))
			c.execute('UPDATE township SET money = money - ? WHERE discord = ?', (purchase[2],ctx.message.author.id,))

			#So far buildings don't really have an effect. They just provide slots for people.
			#Also put the endTurn routine here


#This is supposed to be like the attack feature
@bot.command(name = 'pillage', alisases = ['p'])
async def pillage(ctx, target):
	#implement
	return



@bot.command(name = 'setupGame', alisases = ['setup'], help = 'Supplies the values that populate the building/unit tables.')
async def setupGame(ctx):
	c.execute('INSERT INTO buildingList (buildingName, cost) VALUES ("House", 25)')

	c.execute('INSERT INTO unitList (unitName, cost, requisiteBuilding, requisiteQuantity) VALUES ("Peasant", 10, NULL, NULL)') 

	con.commit()


#COMMENCE!
bot.run(TOKEN)