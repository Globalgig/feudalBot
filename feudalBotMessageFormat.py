import discord

def formatUnits(title, rows):
	embed = discord.Embed(title = title)
	for row in rows:
		value = str(row[2]) + " [" + str(row[5]) + "," + str(row[6]) + "," + str(row[7]) + "," + str(row[8]) + "]"
		embed.add_field(name = row[1], value = value, inline = True)
	return embed

def formatBuildings(title, rows):
	embed = discord.Embed(title = title)
	for row in rows:
		val = str(row[2]) + "/" + str(row[3])
		embed.add_field(name = row[1], value = val, inline = True)
	return embed

def displayTown(row, names, startpoint, title):
	embed = discord.Embed(title = title)
	for index, item in enumerate(row[startpoint:]):
		embed.add_field(name = names[index+startpoint], value = item, inline = True)
	return embed

def displayBuildingsUnits(rows, title):
	embed = discord.Embed(title = title)
	for item in rows:
		embed.add_field(name = item[0], value = item[1], inline = True)
	return embed

def displayTutorial():
	embed = discord.Embed(title = "feudalBot Guide")
	embed.add_field(name = "Turns:", value = "In feudalBot, turns are calculated every thirty seconds. As many actions can be taken during one's turn, but only at the end of the turn are the perTurn values added to your township.", inline = False)
	embed.add_field(name = "Building (^b):", value = "Buildings all require materials to build and each take up 1 buildingSpace in your township. Residential buildings (hovel, house, estate) provide 1/2/3 popSpace respectively. The other buildings all provide 2 speciality slots for that type of unit. E.g. the lumbermill provides 2 slots for lumberjack units.", inline = False)
	embed.add_field(name = "Recruiting (^r)", value = "All units take up 1 popSpace and modify your township's resources per turn. Recruiting units costs the money amount detailed in the units table. Units are split into 3 tiers, 1/3/7, where the number is the quantity of respective buildings before one can recruit them. E.g. 7 lumbermills are required to recruit a beaver_lumberjack.", inline = False)
	embed.add_field(name = "Adventuring (^a)", value = "The adventure action lets your township fight monsters in order to gain more resources. The action always takes 1 attackValue to perform, but it expends an extra if your attackValue is less than or equal to the enemy's. Use the 'list' argument to show the potential difficulty range.", inline = False)
	embed.add_field(name = "Expanding (^e)", value = "The expand action lets your township grow larger, unlocking more buildingSpace. Expanding to a new tile always expends 1 attackValue (even on failures) and requires food to settle. Use the 'list' argument to show potential difficlty range and food costs.", inline = False)
	embed.add_field(name = "Pillaging (^p)", value = "Currently in the game, but it's not correct lmao.", inline = False)
	embed.add_field(name = "Wizarding (^w)", value = "Not implemented. ^:)", inline = False)
	embed.add_field(name = "Trading (^t)", value = "Not implemented.", inline = False)
	embed.add_field(name = "Displaying (^d)", value = "Displays your township's resources. Use the 'pt', 'building', or 'unit' argument to respectively display the perTurn, building, or unit tables for your township.", inline = False)
	return embed

def generateResourceEmbed(row):
	embed = discord.Embed(title = "Township resources:")
	embed.add_field(name = "Food (/d)", value = str(row[2]) + " (" + str(row[3]) + ")")
	embed.add_field(name = "Wood (/d)", value = str(row[4]) + " (" + str(row[5]) + ")")
	embed.add_field(name = "Stone (/d)", value = str(row[6]) + " (" + str(row[7]) + ")")
	embed.add_field(name = "Metal (/d)", value = str(row[8]) + " (" + str(row[9]) + ")")
	embed.add_field(name = "Power (/d)", value = str(row[10]) + " (" + str(row[11]) + ")")
	embed.add_field(name = "Crystals (/d)", value = str(row[12]) + " (" + str(row[13]) + ")")
	return embed

def generateTownshipEmbed(row):
	embed = discord.Embed(title = "Township statistics:")
	embed.add_field(name = "Level", value = str(row[0]))
	embed.add_field(name = "Days Passed", value = str(row[1]))
	return embed