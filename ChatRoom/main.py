from flask import   Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random



app = Flask(__name__)
app.config["SECRET_KEY"] = "Goyan"
socketio = SocketIO(app)

rooms = {}

def generateCode():
    roomCode  = 0
    while (roomCode==0 or roomCode in rooms):
        roomCode = random.randint(1000, 9999)
    return str(roomCode)



@app.route('/', methods = ['POST', 'GET'])
def home():
    session.clear()
    

    if request.method == "POST":
        print(request.form)
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        if not name:
            return render_template("home.html", error="Please enter a name.", code=code, name=name)

        if join != False and not code:                      
            
            return render_template("home.html", error="Please enter a room code.", code=code, name=name)
        
        room = code
        if create != False:

            room = generateCode()
            print(room)
            rooms[room] = {"members": 0, "messages": []}
        

        
        elif room not in rooms:
            print(f"{code}-> ({type(code)}) -->{rooms} -> {type(next(iter(rooms)))}")
            return render_template("home.html", error="Room does not exist.", code=code, name=name)
        
        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))

    return render_template("home.html")




@app.route('/room')
def room():
    room = session.get('room')
    if room not in rooms or room == None or session.get('name') == None:
        return redirect(url_for('home'))
    
    return render_template('room.html',code=room, messages=rooms[room]["messages"])

@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in room: 
        return
    content = {
        "name" : session.get("name"),
        'message' : data["data"]

    }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} sent a message: {data['data']}")

     
@socketio.on("connect")
def connect(auth):
    print("Connected")
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return
    
    join_room(room)
    send({"name": name, "message": "has entered the room"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return
    
    leave_room(room)
    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]

    send({"name": name, "message": "has left the room"}, to=room)
    print(f"{name} left room {room}")   


if __name__ == "__main__":
    socketio.run(app, debug = True)