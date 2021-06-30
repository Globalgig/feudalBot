import random

def generateExplore():
	buildingSlotWeight = [2,3,4,2,1]
	buildingSlots = [0,1,2,3,4]
	b = random.choices(buildingSlots, weights = buildingSlotWeight)

	monsterDifficultyWeight = [8,12,6,3,1]
	monsterDifficulty = [0,1,2,3,4]
	m = random.choices(monsterDifficulty, weights = monsterDifficultyWeight)

	return b,m