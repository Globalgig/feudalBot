import random

def generateExplore():
	buildingSlotWeight = [2,4,2,1]
	buildingSlots = [2,1,2,3]
	rSlots = random.choices(buildingSlots, weights = buildingSlotWeight)[0]

	clearDifficultyWeight = [4,4,2,1]
	clearDifficulty = [0,1,2,3]
	rDiff = random.choices(clearDifficulty, weights = clearDifficultyWeight)[0] * 2 + random.randint(0,1)

	#ASSIMILATION COST. Use math, probably (don't leave as 10)
	rCost = 10

	return rSlots, rDiff, rCost

def generateAdventure():
	adventureDifficultyWeight = [16,20,20,16,8,4,2,1]
	adventureDifficulty = [[0,"nothing"],[1,"a goblin"],[2,"a bandit"],[3,"a bear"],[4,"a troll"],[5,"a minotaur"],[6,"a giant"],[7,"a dragon"]]
	aDiff = random.choices(adventureDifficulty, weights = adventureDifficultyWeight)[0]

	if not aDiff[0]:
		aDiff[0] = aDiff[0] * 3 + random.randint(0,2)

	reward = [random.randint(0,aDiff[0]*4 + 5),random.randint(0,aDiff[0]*4 + 5),random.randint(0,aDiff[0]*4) + 5,random.randint(0,aDiff[0]*4 + 5)]
	return aDiff, reward