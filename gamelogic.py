import random
cols=40
rows=35
class Cell():
	def __init__(self,row,col):
		self.col=col
		self.row=row
		self.walls=[True,True,True,True]
		self.visited=False
	def getRandomNeighbor(self,grid):
		neighbors=[]
		top,right,bottom,left=None,None,None,None
		if index(self.row,self.col-1):
			left=grid[index(self.row,self.col-1)]
		if index(self.row+1,self.col):
			bottom= grid[index(self.row+1,self.col)]
		if index(self.row,self.col+1):
			right= grid[index(self.row,self.col+1)]
		if index(self.row-1,self.col):
			top= grid[index(self.row-1,self.col)]
		if top is not None and not top.visited:
			neighbors.append(top)
		if right is not None and not right.visited:
			neighbors.append(right)
		if bottom is not None and not bottom.visited:
			neighbors.append(bottom)
		if left is not None and not left.visited:
			neighbors.append(left)
		if len(neighbors)>0:
			return neighbors[random.randint(0,len(neighbors)-1)]
		else:
			return None
	def getRandomNeighborForSolve(self,grid):
		neighbors=[]
		top,right,bottom,left=None,None,None,None
		if index(self.row,self.col-1):
			left=grid[index(self.row,self.col-1)]
		if index(self.row+1,self.col):
			bottom= grid[index(self.row+1,self.col)]
		if index(self.row,self.col+1):
			right= grid[index(self.row,self.col+1)]
		if index(self.row-1,self.col):
			top= grid[index(self.row-1,self.col)]
		if top is not None and not top.visited and not self.walls[0]:
			neighbors.append(top)
		if right is not None and not right.visited and not self.walls[1]:
			neighbors.append(right)
		if bottom is not None and not bottom.visited and not self.walls[2]:
			neighbors.append(bottom)
		if left is not None and not left.visited and not self.walls[3]:
			neighbors.append(left)
		if len(neighbors)>0:
			return neighbors[random.randint(0,len(neighbors)-1)]
		else:
			return None
def index(r,c):
	if r<0 or c<0 or r>rows-1 or c>cols-1:
		return False
	else:
		return c + r * cols
def removeWall(current,neighbor):
	if current.row < neighbor.row:
		current.walls[2]=False
		neighbor.walls[0]=False
	elif current.row > neighbor.row:
		current.walls[0]=False
		neighbor.walls[2]=False
	if current.col > neighbor.col:
		current.walls[3]=False
		neighbor.walls[1]=False
	elif current.col < neighbor.col:
		current.walls[1]=False
		neighbor.walls[3]=False

def generateMaze():
	grid=[]
	for r in range(0,rows):
		for c in range(0,cols):
			grid.append(Cell(r,c)) 
	stack=[]
	current=grid[0]
	stack.append(current)
	while len(stack)>0:
		current.visited=True
		neighbor=current.getRandomNeighbor(grid)
		if neighbor:
			neighbor.visited=True
			removeWall(current,neighbor)
			stack.append(neighbor)
			current=neighbor
		else:
			current=stack.pop()
	return grid
def generateMazeSolution(maze,difficulty="easy"):
	for cell in maze:
		cell.visited=False;
	reachedEndOfMaze=False;
	steps=[]
	stack=[]
	current=maze[0]
	hasPassedStepThreshold=False
	addStep=True
	#steps.append(current)
	while not reachedEndOfMaze:
		current.visited=True
		if addStep:
			steps.append(current)
		addStep=True
		neighbor=current.getRandomNeighborForSolve(maze)
		if neighbor:
			if neighbor.row ==rows-1 and neighbor.col==cols-1:
				steps.append(neighbor)
				reachedEndOfMaze=True
				return steps
			neighbor.visited=True
			stack.append(current)
			current=neighbor
		else:
			current=stack.pop()
			if difficulty=="easy":
				#steps.append(current)
				pass
			elif difficulty=="hard":
				addStep=False;
				steps.pop()
			elif difficulty=="medium" and hasPassedStepThreshold:
				addStep=False;
				steps.pop()
		if len(steps)>250:
			hasPassedStepThreshold=True
	return steps
def updatePlayer(player,direction,maze):
	currentRow=player.row
	currentCol=player.col
	if direction == "top":
		if not maze[index(currentRow-1,currentCol)].walls[2] and not maze[index(currentRow,currentCol)].walls[0]:
			player.row=player.row-1
		elif player.isAbleToPhase and player.row-1>=0:
			player.row=player.row-1
			player.isAbleToPhase=False
	elif direction== "bottom":
		if not maze[index(currentRow+1,currentCol)].walls[0] and not maze[index(currentRow,currentCol)].walls[2]:
			player.row=player.row+1
		elif player.isAbleToPhase and player.row+1<rows:
			player.row=player.row+1
			player.isAbleToPhase=False
	elif  direction=="left":
		if not maze[index(currentRow,currentCol-1)].walls[1] and not maze[index(currentRow,currentCol)].walls[3]:
			player.col=player.col-1
		elif player.isAbleToPhase and player.col-1>=0:
			player.col=player.col-1
			player.isAbleToPhase=False
	elif direction=="right":
		if not maze[index(currentRow,currentCol+1)].walls[3] and not maze[index(currentRow,currentCol)].walls[1]:
			player.col=player.col+1
		elif player.isAbleToPhase and player.col+1<cols:
			player.col=player.col+1
			player.isAbleToPhase=False
