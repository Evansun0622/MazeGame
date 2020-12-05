var cols, rows;
var w = 20;
var grid = [];
var current;
var stack = [];
var player;
var seed = 46;
var isGameStarted = false;
var isRoundOngoing = false;
var timeUntilNextRound = 0;
var enemyPlayers = [];
var playerCount = 1;
var canvas;
var isConnected = false;
var socket;
var movementTimer;
if (document.domain == "localhost") {
    socket = io('ws://' + document.domain + ":5000", {
        transports: ['websocket']
    });
} else {
    socket = io('ws://' + document.domain, {
        transports: ['websocket']
    });
}
socket.on('connect_failed', function() {
    console.log('Connection Failed');
});
socket.on('error', function(data) {
    console.log(data);
});
socket.on('connect', function() {
    console.log("connected")
});

socket.on('disconnect', function() {
    console.log("disconnected")
})
socket.on('reconnecting', function() {
    console.log("recpmmectomg")
})
var localRequestID;
var isAbleToPhase = false;
var phaseCount = 3;
var mazeWidth;
var mazeHeight;
var roundCountDownTimer;
var frameCount = 0;
var timeUntilRoundEndForced = 150;
var winningPlayerName = "";
var hud;
var numberOfRounds;
var stopwatch = new Object();
stopwatch.seconds = 0;
stopwatch.minutes = 0;
stopwatch.timer;

function runStopWatch() {
    stopwatch.seconds += 1;
    if (stopwatch.seconds == 60) {
        stopwatch.seconds = 0;
        stopwatch.minutes += 1;
    }
    document.getElementById("timer").innerHTML = stopwatch.minutes + ":" + (stopwatch.seconds > 9 ? stopwatch.seconds : "0" + stopwatch.seconds);
    stopwatch.timer = setTimeout(runStopWatch, 1000)
}

function pauseStopWatch() {
    clearTimeout(stopwatch.timer);
}

function resetStopWatch() {
    clearTimeout(stopwatch.timer);
    stopwatch.seconds = 0;
    stopwatch.minutes = 0;
    runStopWatch();
}

function setup() {
    hud = new Hud();
    mazeHeight = 700;
    mazeWidth = 800;
    w = 20
    var canvasRatio = mazeHeight / mazeWidth;
    var windowRatio = window.innerHeight / (window.innerWidth - 255);
    var newHeight;
    var newWidth;
    if (windowRatio < canvasRatio) {
        newHeight = window.innerHeight * .90;
        newWidth = newHeight / canvasRatio;
        w = newHeight / 35;
    } else {
        newWidth = window.innerWidth * .65;
        newHeight = newWidth * canvasRatio;
        w = newHeight / 35;
    }

    canvas = createCanvas(newWidth, newHeight);
    canvas.parent('canvas-container');

    cols = 40;
    rows = 35;

}

function windowResized() {
    mazeHeight = 700;
    mazeWidth = 800;
    w = 20
    var canvasRatio = mazeHeight / mazeWidth;
    var windowRatio = window.innerHeight / (window.innerWidth - 255);
    var newHeight;
    var newWidth;
    if (windowRatio < canvasRatio) {
        newHeight = window.innerHeight * .90;
        newWidth = newHeight / canvasRatio;
        w = newHeight / 35;
    } else {
        newWidth = window.innerWidth * .65
        newHeight = newWidth * canvasRatio;
        w = newHeight / 35;
    }
    //newWidth=Math.floor(newWidth);
    //newHeight=Math.floor(newHeight);

    var c = document.getElementById("defaultCanvas0");
    heightToStyleHeightRatio=Math.round(c.height/c.style.height.replace("px",""));
    widthToStyleWidthRatio=Math.round(c.width/c.style.width.replace("px",""));
    c.width = newWidth*widthToStyleWidthRatio;
    c.height = newHeight*heightToStyleHeightRatio;
    c.style.width = newWidth + "px";
    c.style.height = newHeight + "px";
    canvas.width = newWidth;
    canvas.height = newHeight;
    clear()
    redraw();

}

function draw() {
    if (isGameStarted) {
        background('#000000');
        for (var i = 0; i < grid.length; i++) {
            grid[i].show();
        }
        enemyPlayers.forEach(function(x) {
            x.show();
        })
        player.show();
        hud.show();
    }
}

function generateMaze(maze) {
    grid = []
    for (var r = 0; r < rows; r++) {
        for (var c = 0; c < cols; c++) {
            var cell = new Cell(r, c);
            cell.walls = maze[index(r, c)];
            grid.push(cell);
        }
    }

    player = new Player({'r':0,'g':0,'b':255}, localRequestID);

}

function index(r, c) {
    if (r < 0 || c < 0 || r > rows - 1 || c > cols - 1) {
        return -1;
    } else {
        return c + r * cols
    }
}

function Hud() {
    this.show = function() {
        fontSize = canvas.width * .04;
        textSize(fontSize)
        textAlign(CENTER, CENTER)
        if (winningPlayerName != "" || player.finishedRace || (!isRoundOngoing && isGameStarted)) {
            fill(0, 0, 0, 200)
            rect(0, 0, canvas.width, canvas.height)
        }
        fill('#FFFFFF')
        stroke('#000000')
        if (winningPlayerName != "") {

            text(winningPlayerName + " has won the game", canvas.width / 2, canvas.height / 2);
        } 
        else if (player.finishedRace) {

            text("You finished the round in " + player.completedRaceTime + " seconds...", canvas.width / 2, canvas.height / 2);
            if (isRoundOngoing) {
                text("Wating for other players... " + timeUntilRoundEndForced + " seconds", canvas.width / 2, (canvas.height / 2) + fontSize + 5);
            }


    }
    if (!isRoundOngoing && isGameStarted) {
            text("Next Rounds starts in " + timeUntilNextRound, canvas.width / 2, (canvas.height / 2) + fontSize + 5);
        }

    }
}

function updateLeaderBoard(playerList) {
    var leaderboard = document.getElementById("leaderboard-entries");
    leaderboard.innerHTML = "";
    for (var i = 0; i < playerList.length; i++) {
        var node = document.getElementById("leaderboard-entry").cloneNode(true);
        node.id = "entry" + playerList[i].playerName;
        node.getElementsByTagName('div')[1].innerHTML = "#" + (i + 1) + " " + playerList[i].playerName;
        node.getElementsByTagName('div')[2].innerHTML =playerList[i].score;
        if (playerList[i].playerID == player.id) {
            node.style.color = "#f7dc6f";
        node.getElementsByTagName('div')[0].style.backgroundColor="rgb(0,0,255)";
        }
        else
        {
         node.getElementsByTagName('div')[0].style.backgroundColor="rgb("+playerList[i].color.r+","+playerList[i].color.g+","+playerList[i].color.b+")";
        }
        leaderboard.appendChild(node);
    }

}

function roundCountDown() {
    timeUntilNextRound -= 1;
    if (timeUntilNextRound > 0) {
        setTimeout(roundCountDown, 1000);
    }
}

function roundEndCountDown() {
    timeUntilRoundEndForced -= 1;
    if (timeUntilRoundEndForced > 0) {
        roundCountDownTimer = setTimeout(roundEndCountDown, 1000);
    }
}

function Cell(r, c) {
    this.r = r;
    this.c = c;
    this.walls = [true, true, true, true];
    this.visited = false;
    this.x = this.c * w;
    this.y = this.r * w;
    this.show = function() {
        this.x = this.c * w;
        this.y = this.r * w;
        var x = this.x;
        var y = this.y;
        stroke('#FFFFFF');
        //strokeWeight(8);
        if (this.walls[0]) {
            line(x, y, x + w, y);
        }
        if (this.walls[1]) {
            line(x + w, y, x + w, y + w);
        }
        if (this.walls[2]) {
            line(x + w, y + w, x, y + w);
        }
        if (this.walls[3]) {
            line(x, y + w, x, y);
        }
        if (this.r == rows - 1 && this.c == cols - 1) {
            fill("#FFD700");
            star(x + w / 2, y + w / 2, w / 4, w / 2, 5)
        }
    }
}

function star(x, y, radius1, radius2, npoints) {
    let angle = TWO_PI / npoints;
    let halfAngle = angle / 2.0;
    beginShape();
    for (let a = 0; a < TWO_PI; a += angle) {
        let sx = x + cos(a) * radius2;
        let sy = y + sin(a) * radius2;
        vertex(sx, sy);
        sx = x + cos(a + halfAngle) * radius1;
        sy = y + sin(a + halfAngle) * radius1;
        vertex(sx, sy);
    }
    endShape(CLOSE);
}

function Player(color, id) {
    this.r = 0;
    this.c = 0;
    this.color = color;
    this.id = id
    this.alpha = 255
    this.isAbleToPhase = false;
    this.finishedRace = false;
    this.score = 0;
    this.completedRaceTime = 0;
    modifier = -1;
    this.show = function() {
        var x = (this.c * w) + (.25 * w);
        var y = (this.r * w) + (.25 * w);
        noStroke();
            if (this.isAbleToPhase) {
                if (this.alpha >= 255) {
                    modifier = 1;
                } else if (this.alpha <= 100) {

                    modifier = -1;
                }
                this.alpha -= (10 * modifier);
                fill(this.color.r, this.color.g, this.color.b, this.alpha);
                stroke(255, 255, 255, this.alpha)

            } else {
                fill(this.color.r, this.color.g, this.color.b, 255);
                stroke('#FFFFFF')

            }
        
        rect(x, y, w - (.5 * w), w - (.5 * w));
        if (player.c == cols - 1 && player.r == rows - 1) {}
    }
}

function initializeEnemies(enemyPlayerList) {
    enemyPlayers = [];
    enemyPlayerList.forEach(function(x) {
        enemyPlayers.push(new Player(x.color, x.playerID));
    })
}

function updatePlayerPosition(direction) {
    /* if (direction == "left") {
         if (!grid[index(player.r, player.c - 1)].walls[1]) {
             player.c = player.c - 1;
         }
     } else if (direction == "top") {
         if (!grid[index(player.r - 1, player.c)].walls[2]) {
             player.r = player.r - 1;
         }

     } else if (direction == "right") {
         if (!grid[index(player.r, player.c + 1)].walls[3]) {
             player.c = player.c + 1;
         }
     } else if (direction == "bottom") {
         if (!grid[index(player.r + 1, player.c)].walls[0]) {
             player.r = player.r + 1;
         }

     }*/
    socket.emit("player_position_changed", {
        'direction': direction
    });
}
//Player controls
setInterval(function(){    kd.tick();
},100)
function movementTick()
{
    kd.tick();
    movementTimer=setTimeout(movementTick,100)
}
$(document).keypress(function(){
    clearTimeout(movementTimer);
    movementTick();
});
$(document).keyup(function(){
    clearTimeout(movementTimer);
});
kd.run(function() {
        kd.LEFT.down(function() {
            updatePlayerPosition("left")
        });

        kd.UP.down(function() {
            updatePlayerPosition("top")
        });

        kd.RIGHT.down(function() {
            updatePlayerPosition("right")
        });
        kd.DOWN.down(function() {
            updatePlayerPosition("bottom")
        });
        kd.A.down(function() {
            updatePlayerPosition("left")
        });

        kd.W.down(function() {
            updatePlayerPosition("top")
        });

        kd.D.down(function() {
            updatePlayerPosition("right")
        });
        kd.S.down(function() {
            updatePlayerPosition("bottom")
        });
    }
);

$(document).keydown(function(e) {
    if (e.keyCode == 32) {
        socket.emit('spacebar');

    }
});



//Server stuff
function startGame() {

    document.getElementById("start-screen").style.display = "none";
    document.getElementsByTagName("canvas")[0].style.display = "block";
    document.getElementById("queue").style.display = "block";
    document.getElementById("playerCount").style.display = "block";
    var name = document.getElementById("nameInput").value;
    socket.emit('entered_queue', {
        'name': name
    });
    socket.on('join_room', function(msg) {
        isConnected = true;
        localRequestID = msg.playerID;
        playerCount = msg.numberOfPlayers
        document.getElementById("playerCount").innerHTML = playerCount + "/10";


    });
    socket.on('update_player_count', function(msg) {
        playerCount = msg
        document.getElementById("playerCount").innerHTML = msg + "/10";

    });
    socket.on('room_found', function(data) {
        document.getElementById("playerCount").innerHTML = data + "/10";
        secondsRemaining = 3
        document.getElementById("queue").innerHTML = "Starting round 1 in " + secondsRemaining;
        startTimer = setInterval(function() {
            if (secondsRemaining > 0) {
                secondsRemaining -= 1;
                document.getElementById("queue").innerHTML = "Starting round 1 in " + secondsRemaining;
            } else {
                clearInterval(startTimer)
            }
        }, 1000);
    });

    socket.on('match_starting', function() {
        // socket.emit('get_room_details');
    })
    socket.on('start_game', function(data) {
        seed = JSON.parse(data).seed;
        var enemyPlayerList = JSON.parse(data).playerList;
        var completePlayerList = JSON.parse(data).completePlayerList;
        isGameStarted = true;
        isRoundOngoing = true;
        initializeEnemies(enemyPlayerList);
        generateMaze(JSON.parse(data).maze)
        updateLeaderBoard(completePlayerList)
        document.getElementById("lobby-screen").style.display = "none";
        numberOfRounds = JSON.parse(data).roundsLeft;
        document.getElementById("rounds").innerHTML = "Round 1 of " + JSON.parse(data).roundsLeft;
        document.getElementById("leaderboard").style.display = "block";
        timeUntilRoundEndForced = 150;
        roundCountDownTimer = setTimeout(roundEndCountDown, 1000);
        runStopWatch();
        movementTimer=setTimeout(movementTick,100)

    });
    socket.on('able_to_phase', function() {
        player.isAbleToPhase = !player.isAbleToPhase;
        if (player.isAbleToPhase) {
            phaseCount -= 1;
        }
    })
    socket.on('local_player_updated', function(data) {
        parsedData = JSON.parse(data);
        player.c = parsedData.col
        player.r = parsedData.row
        player.isAbleToPhase = parsedData.isAbleToPhase
    })
    socket.on('players_updated', function(data) {
        parsedData = JSON.parse(data);
        //  console.log(parsedData)
        enemyPlayers.forEach(function(player) {
            if (parsedData.playerID == player.id) {
                player.c = parsedData.col;
                player.r = parsedData.row;
            }
        });
    });
    socket.on("update_leaderboard", function(data) {
        var playerList = JSON.parse(data).completePlayerList;
        updateLeaderBoard(playerList);
    });
    socket.on("finished_race", function(data) {
        player.finishedRace = true;
        player.completedRaceTime = data;
        pauseStopWatch();
    })
    socket.on("round_over", function(data) {
        isRoundOngoing = false;
        timeUntilNextRound = 3;
        setTimeout(roundCountDown, 1000);
        pauseStopWatch();
    });
    socket.on("start_next_round", function(data) {
        generateMaze(JSON.parse(data).maze)
        document.getElementById("rounds").innerHTML = "Round " + ((numberOfRounds - JSON.parse(data).roundsLeft) + 1) + " of " + numberOfRounds;
        isRoundOngoing = true;
        timeUntilRoundEndForced = 150;
        clearTimeout(roundCountDownTimer);
        roundCountDownTimer = setTimeout(roundEndCountDown, 1000);
        var enemyPlayerList = JSON.parse(data).playerList;
        var completePlayerList = JSON.parse(data).completePlayerList;
        initializeEnemies(enemyPlayerList);
        resetStopWatch();
    });
    socket.on('game_won', function(data) {
        pauseStopWatch();
        winningPlayerName = data;
        setTimeout(function() {
            isGameStarted = false;
        }, 100);
        setTimeout(function() {
            document.location.href = "";
        }, 4000);
    })
    $(window).on('beforeunload', function() {
        socket.close();
    });
}