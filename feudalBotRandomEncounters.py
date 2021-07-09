import random

def generateExpand(eCount):
	buildingSlotWeight = [1,8,4,2]
	buildingSlots = [0,1,2,3]
	rSlots = random.choices(buildingSlots, weights = buildingSlotWeight)[0]

	#Will return rSlots, rDiff, rCost. Respectively, # of buildings slots, difficulty value, and food cost of acquiring

	return rSlots, expandDifficulty(eCount), expandCost(eCount)

def expandCost(eCount):
	return 10 * 2 ** eCount

def expandDifficulty(eCount):
	#Chooses a random value on a -2/+2 range where the value can't be less than zero
	return random.choices([x + eCount if x + eCount > 0 else 0 for x in range(-2,3)], weights = [1,2,4,2,1])

def generateAdventure(aCount):
	aDiff = adventureDifficulty(aCount)
	reward = [random.randint(0,aDiff[0]*4 + 5),random.randint(0,aDiff[0]*4 + 5),random.randint(0,aDiff[0]*4) + 5,random.randint(0,aDiff[0]*4 + 5)]

	return aDiff, reward


def adventureDifficulty(aCount):
	#Chooses a random name/value pair on a -3/+3 range where the value can't be less than zero
	names = ["rat", "goblin", "bandit", "bear", "troll", "minotaur", "giant", "dragon"]
	return random.choices([[x + aCount, names[x]] if x + aCount > 0 else [0, names[0]] for x in range(-3,4)], weights = [1,2,4,8,4,2,1])[0]