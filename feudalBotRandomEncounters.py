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
	return random.choices([x + eCount if x + eCount >= 0 else 0 for x in range(-2,3)], weights = [1,2,4,2,1])

def generateAdventure():
	adventureDifficultyWeight = [16,20,20,16,8,4,2,1]
	adventureDifficulty = [[0,"nothing"],[1,"a goblin"],[2,"a bandit"],[3,"a bear"],[4,"a troll"],[5,"a minotaur"],[6,"a giant"],[7,"a dragon"]]
	aDiff = random.choices(adventureDifficulty, weights = adventureDifficultyWeight)[0]

	if not aDiff[0]:
		aDiff[0] = aDiff[0] * 3 + random.randint(0,2)

	reward = [random.randint(0,aDiff[0]*4 + 5),random.randint(0,aDiff[0]*4 + 5),random.randint(0,aDiff[0]*4) + 5,random.randint(0,aDiff[0]*4 + 5)]
	return aDiff, reward