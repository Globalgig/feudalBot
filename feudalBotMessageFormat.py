import discord

def formatRows(title, rows):

	embed = discord.Embed(title = title)
	for row in rows:
		embed.add_field(name = row[1], value = row[2], inline = True)
	return embed


def displayTown(row, names):
	embed = discord.Embed(title = row[2])
	for index, item in enumerate(row[3:]):
		embed.add_field(name = names[index+3], value = item, inline = True)
	return embed
