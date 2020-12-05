from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, join_room, leave_room, emit, rooms, send, close_room
import random
from threading import Timer
import eventlet
import time
import json;
from gamelogic import generateMaze, updatePlayer, generateMazeSolution
from datetime import datetime
eventlet.monkey_patch()
app= Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
socketio=SocketIO(app)
ROOMS={}
PLAYERS={}
seedList=[]
class Player():
	def __init__(self,col,row,playerID,playerName="unnamed",roomID="unassigned"):
		self.col=col
		self.row=row
		self.playerName=playerName
		self.roomID=roomID
		self.playerID=playerID
		self.phasesLeft=3
		self.score=0
		self.isAbleToPhase=False
		self.isRacing=False
		self.color={'r':random.randint(0,255),'g':random.randint(0,255),'b':random.randint(0,255)}
	def serialize(self):
		return{
		'col': self.col,
		'row': self.row,
		'roomID': self.roomID,
		'playerID': self.playerID,
		'playerName':self.playerName,
		'isAbleToPhase':self.isAbleToPhase,
		'color':self.color,
		'score': self.score
		}
class Bot(Player):
	def __init__(self,col,row,playerID,playerName,roomID):
		super().__init__(col,row,playerID,playerName,roomID)
		self.path=ROOMS[self.roomID].solutions.pop()
		self.playerName=self.generateName()
	def moveBot(self):
		if ROOMS[self.roomID].isRoundOnGoing and self.isRacing:
			self.nextStep=self.path[0]
			self.row=self.nextStep.row
			self.col=self.nextStep.col
			self.path.pop(0)
			message=json.dumps(self.serialize())
			socketio.emit("players_updated",message,room=self.roomID)
			#t.start();
	def generateName(self):
		firstName= random.choice(ROOMS[self.roomID].botNames)
		ROOMS[self.roomID].botNames.remove(firstName)
		secondName =random.choice(ROOMS[self.roomID].botNames)
		number=""
		if random.randint(1,2) ==2:
			number=random.randint(10,999)
		ROOMS[self.roomID].botNames.remove(secondName)
		return firstName+random.choice(["_"," ",""])+secondName+str(number)
class Room():
	def __init__(self,seed,maze):
		self.playerList=[]
		self.gameStarted=False
		self.isRoundOnGoing=False
		self.seed=seed
		self.maze=maze
		self.solutions=[generateMazeSolution(maze) for i in range(1,20)][16:20]
		random.shuffle(self.solutions)
		self.solutions.append(generateMazeSolution(maze,"medium"))
		self.solutions.append(generateMazeSolution(maze,"hard"))
		self.roundsLeft=3
		self.playersDoneRacing=0
		self.roundStartTime=datetime.utcnow()
		self.roundEndTimer=None
		self.botNames=["Monkey","Pants","Unicorn","Noob","TTV","Bert","Banana","Master","Overlord","Booty","Blaster","Icy"]
	def add_player(self,player):
		self.playerList.append(player)
	def remove_player(self,playerID):
		for player in self.playerList:
			if player.playerID == playerID:
				self.playerList.remove(player)
	def addBots(self):
		numberOfBots=10-len(self.playerList)
		if numberOfBots>0:
			for i in range(0,random.randint(3,4)):
				self.add_player(Bot(0,0,random.randint(1,10000000),("bot #"+str(i)),self.seed))
	def moveAllBots(self):
		if self.isRoundOnGoing:
			for player in self.playerList:
				if type(player).__name__=="Bot" and player.isRacing:
					player.moveBot()
					if player.row==34 and player.col==39:
						finishReached(player,self.seed)
			eventlet.spawn_after(.1,self.moveAllBots)
	def serialize(self,requestSID="none"):
		return{
		'playerList':[player.serialize() for player in self.playerList if player.playerID != requestSID],
		'completePlayerList':[player.serialize() for player in self.playerList],
		'gameStarted':self.gameStarted,
		'maze': [cell.walls for cell in self.maze],
		'roundsLeft': self.roundsLeft
		}
def finishReached(player,roomID,sid=""):
	player.isRacing=False
	raceCompletionTime=(datetime.utcnow()-ROOMS[roomID].roundStartTime).total_seconds()
	player.score+=round(1000/raceCompletionTime)
	print(round(raceCompletionTime,2))
	message=json.dumps(player.serialize())
	if sid:
		socketio.emit("players_updated",message,room=roomID,skip_sid=sid)
	else:
		socketio.emit("players_updated",message,room=roomID)
	ROOMS[roomID].playerList.sort(key= lambda x:x.score,reverse=True)
	message=json.dumps(ROOMS[roomID].serialize())
	socketio.emit("update_leaderboard",message,room=roomID)
	if sid:
		socketio.emit("finished_race",str(round(raceCompletionTime,2)),room=sid)
	ROOMS[roomID].playersDoneRacing+=1
	if ROOMS[roomID].playersDoneRacing==3 or ROOMS[roomID].playersDoneRacing>=len(ROOMS[roomID].playerList):
		ROOMS[roomID].isRoundOnGoing=False
		message=json.dumps(ROOMS[roomID].serialize(sid))
		ROOMS[roomID].roundsLeft-=1
		ROOMS[roomID].roundEndTimer.cancel()
		if ROOMS[roomID].roundsLeft>0:
			socketio.emit("round_over",message,room=roomID)
			eventlet.spawn_after(3,startNextRound,roomID)
		else:
			message=ROOMS[roomID].playerList[0].playerName
			socketio.emit("game_won",message,room=roomID)
			socketio.close_room(roomID)
			del ROOMS[roomID]
			#del PLAYERS[request.sid]
@app.route("/")
def index():
	return render_template('index.html')
@socketio.on('entered_queue')
def handleConnect(data):
	if data['name'] == "":
		PLAYERS[request.sid]=Player(0,0,request.sid)
	else:
		PLAYERS[request.sid]=Player(0,0,request.sid,data['name'])
	matchFound=False
	for seed,room in ROOMS.items():
		print(str(len(room.playerList)))
		print(str(room.gameStarted))
		if len(room.playerList)<10 and room.gameStarted==False:
			matchFound=True
			PLAYERS[request.sid].roomID=seed
			room.add_player(PLAYERS[request.sid])
			join_room(seed)
			emit("update_player_count",len(room.playerList),room=seed)
			print("In room" +str(PLAYERS[request.sid].roomID))
	if not matchFound:
		seed=random.randint(1,100000)
		while seed in seedList:
			seed=random.randint(1,100000)
		seedList.append(seed)
		room=Room(seed,generateMaze())
		PLAYERS[request.sid].roomID=seed
		room.add_player(PLAYERS[request.sid])
		ROOMS[seed]=room
		room.addBots()
		join_room(seed)
		eventlet.spawn_after(4,queueOver,seed)
	print("new connect event " +str(PLAYERS[request.sid].roomID))
	emit('join_room',{'room':seed,'playerID':request.sid,'numberOfPlayers':len(room.playerList)})
@socketio.on('disconnect')
def handleDisconnect():
	print(ROOMS)
	if request.sid in PLAYERS:
		roomID=PLAYERS[request.sid].roomID
		if len(ROOMS[roomID].playerList)==1:
			leave_room(roomID)
			ROOMS[roomID].remove_player(request.sid)
			del ROOMS[roomID]
			print(ROOMS)
			del PLAYERS[request.sid]
@socketio.on('get_room_details')
def getRoomDetails():
	roomID=PLAYERS[request.sid].roomID
	message=json.dumps(ROOMS[roomID].serialize(request.sid))
	print("getRoomDetails " +str(PLAYERS[request.sid].roomID))
	emit("start_game",message,room=request.sid)
@socketio.on('player_position_changed')
def playerPositionChanged(data):
	roomID=PLAYERS[request.sid].roomID
	if ROOMS[roomID].isRoundOnGoing and ROOMS[roomID].gameStarted:
		for player in ROOMS[roomID].playerList:
			if player.playerID==request.sid and player.isRacing:
				updatePlayer(player,data['direction'],ROOMS[roomID].maze)
				message=json.dumps(player.serialize())
				emit("local_player_updated",message,room=request.sid)
				if player.col==39 and player.row==34:
					finishReached(player,roomID,request.sid)
				else:
					message=json.dumps(player.serialize())
					emit("players_updated",message,room=roomID,skip_sid=request.sid)
@socketio.on('spacebar')
def onSpacebar():
	if PLAYERS[request.sid].phasesLeft>0 and not PLAYERS[request.sid].isAbleToPhase:
		PLAYERS[request.sid].isAbleToPhase=True
		PLAYERS[request.sid].phasesLeft-=1
		emit("able_to_phase",room=request.sid)
def queueOver(roomID):
	eventlet.spawn_after(3,startGame,roomID)
	socketio.emit("room_found",len(ROOMS[roomID].playerList),room=roomID)

def startGame(roomID):
	with app.test_request_context():
		ROOMS[roomID].gameStarted=True
		ROOMS[roomID].isRoundOnGoing=True
		socketio.emit("match_starting",room=roomID)
		for player in ROOMS[roomID].playerList:
			player.isRacing=True
			if type(player).__name__=="Bot":
				pass
			else:
				message=json.dumps(ROOMS[roomID].serialize(player.playerID))
				socketio.emit("start_game",message,room=player.playerID)
		ROOMS[roomID].moveAllBots()
		ROOMS[roomID].roundEndTimer=eventlet.spawn_after(150,forceRoundEnd,roomID)
def startNextRound(roomID):
	with app.test_request_context():
		ROOMS[roomID].maze=generateMaze()
		ROOMS[roomID].solutions=[generateMazeSolution(ROOMS[roomID].maze) for i in range(1,20)][16:20]
		random.shuffle(ROOMS[roomID].solutions)
		ROOMS[roomID].solutions.append(generateMazeSolution(ROOMS[roomID].maze,"medium"))
		ROOMS[roomID].solutions.append(generateMazeSolution(ROOMS[roomID].maze,"hard"))
		ROOMS[roomID].playersDoneRacing=0
		ROOMS[roomID].roundStartTime=datetime.utcnow()
		ROOMS[roomID].isRoundOnGoing=True
		for player in ROOMS[roomID].playerList:
			player.col=0
			player.row=0
			player.phasesLeft=3
			player.isAbleToPhase=False
			player.isRacing=True
			if type(player).__name__ == "Bot":
				player.path=ROOMS[roomID].solutions.pop()
		for player in ROOMS[roomID].playerList:
			message=json.dumps(ROOMS[roomID].serialize(player.playerID))
			socketio.emit("start_next_round",message,room=player.playerID)
		ROOMS[roomID].moveAllBots()
		ROOMS[roomID].roundEndTimer=eventlet.spawn_after(150,forceRoundEnd,roomID)

def forceRoundEnd(roomID):
	with app.test_request_context():
		ROOMS[roomID].isRoundOnGoing=False
		message=json.dumps(ROOMS[roomID].serialize())
		ROOMS[roomID].roundsLeft-=1
		if ROOMS[roomID].roundsLeft>0:
			socketio.emit("round_over",message,room=roomID)
			eventlet.spawn_after(3,startNextRound,roomID)
		else:
			message=ROOMS[roomID].playerList[0].playerName
			socketio.emit("game_won",message,room=roomID)
			socketio.close_room(roomID)
			del ROOMS[roomID]

if __name__=="__main__":
	socketio.run(app)