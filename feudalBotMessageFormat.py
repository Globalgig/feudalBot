import discord

def formatRows(title, rows):

	embed = discord.Embed(title = title)
	for row in rows:
		embed.add_field(name = row[1], value = row[2], inline = True)
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
