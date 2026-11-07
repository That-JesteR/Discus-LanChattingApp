import sqlite3
from fastapi import FastAPI,HTTPException,status,Header,WebSocket,WebSocketDisconnect,WebSocketException,Body,File,UploadFile,Form,Request
from fastapi.encoders import jsonable_encoder
import uvicorn
import secrets
import bcrypt  
import json
import requests
import traceback
import string
from datetime import datetime,timezone
import json

Directory = ""
#SQLite
database = sqlite3.connect(Directory + "Discus.db")
if database:
    print("Database created/opened")
else:
    print("Failed to create/open database")

cursor = database.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS Users(
            ID INTEGER PRIMARY KEY,
            Username TEXT NOT NULL,
            Password TEXT NOT NULL,
            AuthToken TEXT NOT NULL,
            EncryptedKey TEXT NOT NULL,
            EnvelopeKey TEXT NOT NULL,
            Salt TEXT NOT NULL,
            PublicKey TEXT NOT NULL)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS UserInfo(
            ID INTEGER PRIMARY KEY,
            Banner TEXT NOT NULL,
            Bio TEXT,
            Icon TEXT NOT NULL,
            Creation TEXT NOT NULL)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS Friends(
            User1 INTEGER NOT NULL,
            User2 INTEGER NOT NULL,
            Status TEXT NOT NULL)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS Active(
            UserID INTEGER NOT NULL,
            SessionToken TEXT NOT NULL)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS Messages(
            MessageID INTEGER PRIMARY KEY AUTOINCREMENT,
            Message TEXT NOT NULL,
            Time TEXT NOT NULL,
            SenderID INTEGER NOT NULL,
            RecipientID INTEGER NOT NULL,
            SenderKey TEXT NOT NULL,
            RecipientKey TEXT NOT NULL,
            Type TEXT NOT NULL)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS Unread(
                User1 INTEGER NOT NULL,
                User2 INTEGER NOT NULL,
                Timestamp TEXT NOT NULL,
                Messages INTEGER NOT NULL)""")

cursor.execute("DELETE FROM Active")

database.commit()
database.close()

#Active User Sockets
ActiveUsers = {}

#API
api = FastAPI(title="An API", description="API for my Discus app")

# Websocket---------------------------------------------------
@api.websocket("/Web")
async def WebSocket(Websocket: WebSocket, Token: str, Id: int):
    if not CheckSessionToken(int(Id),Token):
        await Websocket.close(code=1008)
        return

    await Websocket.accept()
    try:
        if ActiveUsers[Id]:
            ActiveUsers[Id].append(Websocket)
        else:
            ActiveUsers[Id] = [Websocket]
    except:
        ActiveUsers[Id] = [Websocket]
    print(ActiveUsers,flush=True)
    print(f"{len(ActiveUsers)} users connected")
    try:
        while True:
            data = await Websocket.receive_text()
            data = json.loads(data)
            #print(data,flush=True)
            print(f"whole is :{ActiveUsers}",flush=True)
            if data.get("Type") == "Message":
                if AreFriends(Id,data.get("Recipient")):
                    CurrentTime = datetime.now(timezone.utc)
                    CurrentTime = jsonable_encoder(CurrentTime)
                    try:
                        #SaveMessage(data.get("Sender"),data.get("Recipient"),data.get("Text"),data.get("Time"),data.get(""),data.get(""),data.get("Type"))
                        SaveMessage(data.get("Sender"),data.get("Recipient"),data.get("Text"),CurrentTime,data.get("SenderKey"),data.get("RecipientKey"),data.get("Type"))
                    except:
                        e = traceback.format_exc()
                        print(e,flush=True)

                    for client in ActiveUsers[Id]:
                        await client.send_json({"Sender":data.get("Sender"),"SenderName":RetrieveUserInfo(data.get("Sender")).get("Username"),
                                                "Recipient":data.get("Recipient"),"RecipientName":RetrieveUserInfo(data.get("Recipient")).get("Username"),
                                                "Time":CurrentTime,"Text":data.get("Text"),"Key":data.get("SenderKey"),"Type": "Message"})
                    try:
                        for client in ActiveUsers[int(data["Recipient"])]:
                            await client.send_json({"Sender":data.get("Sender"),"SenderName":RetrieveUserInfo(data.get("Sender")).get("Username"),
                                                    "Recipient":data.get("Recipient"),"RecipientName":RetrieveUserInfo(data.get("Recipient")).get("Username"),
                                                    "Time":CurrentTime,"Text":data.get("Text"),"Key":data.get("RecipientKey"),"Type": "Message"})
                    except:
                        print("User not online, message could not be sent",flush=True)
                        setUnread(int(data["Recipient"]),Id,CurrentTime) #causes a ASGI wtv error, maybe bc of async gotta fix it
                        #traceback.print_exc()
                        print(f"whole is :{ActiveUsers}",flush=True)
                else:
                    print("The Users arent friends",flush=True)
                    for client in ActiveUsers[Id]:
                        await client.send_json({"Sender":data.get("Sender"),"SenderName":RetrieveUserInfo(data.get("Sender")).get("Username"),
                                                "Recipient":data.get("Recipient"),"RecipientName":RetrieveUserInfo(data.get("Recipient")).get("Username"),
                                                "Time":data.get("Time"),"Text":data.get("Text"),"Type": "MessageCanceled"})

            elif data.get("Type") == "UpdateUnread":
                try:
                    print("i got the message")
                    setUnread(data.get("Sender"),data.get("Recipient"),data.get("Timestamp"),data.get("Number"))
                except:
                    raise Exception("Failed")

            elif data.get("Type") == "FriendRequest":
                try:
                    for client in ActiveUsers[Id]:
                        await client.send_json({"SenderId":data.get("SenderId"),"SenderName":data.get("SenderName"),"Recipient":Id,"Type": "FriendRequest"})
                    print(f"I SENT THE FRIEND REQUEST: {data.get("SenderId")},{data.get("SenderName")},{Id},{"FriendRequest"}",flush=True)
                except:
                    traceback.print_exc()

            elif data.get("Type") == "ClearUnread":
                if AreFriends(Id,data.get("Recipient")):
                    DeleteUnread(Id,data.get("Recipient"))

            elif data.get("Type") == "Disconnect":
                #print(data,flush=True)
                UUID = int(data.get("Sender"))
                print(f"the particular is :{ActiveUsers[UUID]}",flush=True)
                print(f"whole is :{ActiveUsers}",flush=True)
                if len(ActiveUsers[UUID]) == 1:
                    try:
                        database = sqlite3.connect(Directory + "Discus.db")
                        cursor = database.cursor()
                        cursor.execute("DELETE FROM Active WHERE UserID = ?",(UUID,))
                        database.commit()   
                        database.close()
                        print(f"I DELETED {UUID} on disconnect",flush=True)
                    except Exception as e:
                        print(e,flush=True)
                try:
                    ActiveUsers[UUID].close()
                    ActiveUsers[UUID].remove(Websocket)
                except:
                    print("didnt find websocket to remove",flush=True)
                if not ActiveUsers[UUID]:
                    del ActiveUsers[UUID]
                print(f"the particular is :{ActiveUsers[UUID]}",flush=True)
                print(f"whole is :{ActiveUsers}",flush=True)
                print(f"{len(ActiveUsers)} users connected")

    except WebSocketDisconnect:
        print(f"the particular is :{ActiveUsers[Id]}",flush=True)
        print(f"whole is :{ActiveUsers}",flush=True)
        if len(ActiveUsers[Id]) == 1:
            try:
                database = sqlite3.connect(Directory + "Discus.db")
                cursor = database.cursor()
                cursor.execute("DELETE FROM Active WHERE UserID = ?",(Id,))
                database.commit()
                database.close()
                print(f"I DELETED {Id} on websocket disconect",flush=True)
            except:
                database.rollback()
                database.close()
        try:
            ActiveUsers[Id].remove(Websocket)
        except:
            print("didnt find websocket to remove",flush=True)
        if not ActiveUsers[Id]:
            del ActiveUsers[Id]
        print(f"{len(ActiveUsers)} users connected")




# Retrieving and processing Friend Requests and Data-------------------

@api.post("/api/friends/requests")
async def FriendRequest(SenderId: int = Body(...),RecipientName: str = Body(...)):
    database = sqlite3.connect(Directory + "Discus.db")
    cursor = database.cursor()
    cursor.execute("SELECT ID FROM Users WHERE Username = ?",(RecipientName,))
    targetID = cursor.fetchone()
    #print(f"i got: {targetID}",flush=True)
    if targetID is None:
        database.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found")
    if targetID[0] == SenderId:
        database.close()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="You cant friend yourself")
    cursor.execute("SELECT Status FROM Friends WHERE (User1 = ? AND User2 = ?) OR (User1 = ? AND User2 = ?)",(SenderId,targetID[0],targetID[0],SenderId))
    target = cursor.fetchone()
    if target is not None:
        if target[0] == "Pending" or target[0] == "RePending":
            database.close()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="There is already an ongoing request")
        if target[0] == "Accepted":
            database.close()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="Already friends with the user")
    cursor.execute("SELECT Username FROM Users WHERE ID = ?",(SenderId,))
    SenderName = cursor.fetchone()
    cursor.execute("SELECT Icon FROM UserInfo WHERE ID = ?",(SenderId,))
    SenderIcon = cursor.fetchone()[0]
    cursor.execute("SELECT Icon FROM UserInfo WHERE ID = ?",(targetID[0],))
    TargetIcon = cursor.fetchone()[0]
    try:
        if WereFriends(SenderId,targetID[0]):
            cursor.execute("UPDATE FRIENDS SET User1 = ?, User2 = ?, Status = ? WHERE (User1 = ? AND User2 = ?) OR (User1 = ? AND User2 = ?)",(SenderId,targetID[0],"RePending",SenderId,targetID[0],targetID[0],SenderId))
            database.commit()
            database.close()
        else:
            cursor.execute("INSERT INTO Friends (User1,User2,Status) VALUES (?,?,?)",(SenderId,targetID[0],"Pending"))
            database.commit()
            database.close()
    except Exception as e:
        print(e,flush=True)
    try:
        for client in ActiveUsers[SenderId]:
            await client.send_json({"SenderId":SenderId,"SenderName":SenderName[0],"RecipientId":targetID[0],"RecipientName":RecipientName,"Icon":TargetIcon,"Type": "FriendRequest"}) 
    except:
        print("The user 1 is offline",flush=True)
    try:
        for client in ActiveUsers[targetID[0]]:
            await client.send_json({"SenderId":SenderId,"SenderName":SenderName[0],"RecipientId":targetID[0],"RecipientName":RecipientName,"Icon":SenderIcon,"Type": "FriendRequest"}) 
    except:
        print("The user 2 is offline",flush=True)

@api.post("/api/friends/requests/decline")
async def FriendRequestDecline(User1: int = Body(...),User2: int = Body(...),Name1: str = Body(...),Name2: str = Body(...)): 
    database = sqlite3.connect(Directory + "Discus.db")
    cursor = database.cursor()
    if not WereFriends(User1,User2):
        cursor.execute("DELETE FROM Friends WHERE (User1 = ? AND User2 = ?) OR (User1 = ? AND User2 = ?)",(User1,User2,User2,User1))
    else:
        cursor.execute("UPDATE FRIENDS SET Status = ? WHERE (User1 = ? AND User2 = ?) OR (User1 = ? AND User2 = ?)",("Deleted",User1,User2,User2,User1))
    database.commit()
    database.close()
    try:
        for client in ActiveUsers[User1]:
            await client.send_json({"Sender":User1,"Recipient":User2,"SenderName":Name1,"RecipientName":Name2,"Type": "FriendRequestDeclined"})
    except:
        print("User offline",flush=True)
    try:
        for client in ActiveUsers[User2]:
            await client.send_json({"Sender":User1,"Recipient":User2,"SenderName":Name1,"RecipientName":Name2,"Type": "FriendRequestDeclined"})
    except:
        print("User offline",flush=True)

@api.post("/api/friends/requests/accept")
async def FriendRequestAccept(User1: int = Body(...),User2: int = Body(...),Name1: str = Body(...),Name2: str = Body(...)): 
    database = sqlite3.connect(Directory + "Discus.db")
    cursor = database.cursor()
    cursor.execute("UPDATE FRIENDS SET Status = ? WHERE (User1 = ? AND User2 = ?) OR (User1 = ? AND User2 = ?)",("Accepted",User1,User2,User2,User1))
    database.commit()
    database.close()
    print(f"THE ID IS {User1,User2,Name1,Name2}",flush=True)
    temp1 = RetrieveUserInfo(User1)
    temp2 = RetrieveUserInfo(User2)
    try:
        for client in ActiveUsers[User1]:
            await client.send_json({"Sender":User1,"Recipient":User2,"Target":Name2,"Banner":temp2.get("Banner"),"Bio":temp2.get("Bio"),"Icon":temp2.get("Icon"),"PublicKey":temp2.get("publickey"),"Creation":temp2.get("Creation"),"Type": "FriendRequestAccepted"})
    except:
        print("User is offline",flush=True)
    try:
        for client in ActiveUsers[User2]:
            await client.send_json({"Sender":User1,"Recipient":User2,"Target":Name1,"Banner":temp1.get("Banner"),"Bio":temp1.get("Bio"),"Icon":temp1.get("Icon"),"PublicKey":temp1.get("publickey"),"Creation":temp1.get("Creation"),"Type": "FriendRequestAccepted"})
    except:
        print("User is offline",flush=True)


def AreFriends(id1,id2):
    database = sqlite3.connect(Directory + "Discus.db")
    cursor = database.cursor()
    try:
        cursor.execute("SELECT Status FROM Friends WHERE User1 = ? AND User2 = ? OR User1 = ? AND User2 = ?",(id1,id2,id2,id1))
        result =  cursor.fetchone()
        database.close()
        if result is not None and result[0] == "Accepted":
            return True
        else:
            return False
    except Exception as e:
        database.close()
        raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT,detail=f"{e}")

def WereFriends(id1,id2):
    database = sqlite3.connect(Directory + "Discus.db")
    cursor = database.cursor()
    try:
        cursor.execute("SELECT Status FROM Friends WHERE User1 = ? AND User2 = ? OR User1 = ? AND User2 = ?",(id1,id2,id2,id1))
        result =  cursor.fetchone()
        database.close()
        if (result is not None) and (result[0] == "Deleted" or result[0] == "RePending"):
            return True
        else:
            return False
    except Exception as e:
        database.close()
        raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT,detail=f"{e}")

    
# session token-------------------------------------------------
def SessionToken(Id):
    SessionToken = secrets.token_hex(16)
    database = sqlite3.connect(Directory + "Discus.db")
    cursor = database.cursor()
    try:
        cursor.execute("SELECT SessionToken FROM Active WHERE UserID = ?",(Id,))
        token =  cursor.fetchone()
        if token:
            cursor.execute("UPDATE Active SET SessionToken = ? ",(SessionToken,))
        else:
            cursor.execute("INSERT INTO Active (UserID,SessionToken) VALUES (?,?)",(Id,SessionToken))
        database.commit()
        database.close()
        return(SessionToken)
    except:
        database.rollback()
        database.close()
        raise Exception(ConnectionAbortedError)

def DeleteSessionToken(Id):
    database = sqlite3.connect(Directory + "Discus.db")
    cursor = database.cursor()
    try:
        cursor.execute("DELETE FROM Active WHERE UserID = ?",(Id,))
        database.commit()
        database.close()
    except:
        database.rollback()
        database.close()
        raise Exception(ConnectionAbortedError)

def CheckSessionToken(Id,Token):
    ST = None
    AT = None
    if "/" in Token:
        ST,AT = Token.split("/")
    else:
        ST = Token
    database = sqlite3.connect(Directory + "Discus.db")
    cursor = database.cursor()
    try:
        cursor.execute("SELECT SessionToken FROM Active WHERE UserID = ?",(int(Id),))
        token =  cursor.fetchone()
        if (token is not None) and (token[0] == ST):
            database.close()
            return(True)
        else:
            #print("token was wrong",flush=True)
            if AT is not None:
                cursor.execute("SELECT AuthToken FROM Users WHERE ID = ?",(int(Id),))
                token =  cursor.fetchone()
                #print(f"token[0] == AT: {token[0] == AT:} 1:{token[0]} 2:{AT}")
                if token[0] == AT:
                    try:
                        cursor.execute("INSERT INTO Active (UserID,SessionToken) VALUES (?,?)",(int(Id),ST))
                        database.commit()
                        database.close()
                        return(True)
                    except:
                        database.rollback()
                        database.close()
                else:
                    print("auth was wrong too",flush=True)
                    database.close()
                    return(False)
            else:
                return(False)
    except Exception as e:
        database.close()
        #print(f"session token: {e}",flush=True)

def AlrdInSession(Id):
    database = sqlite3.connect(Directory + "Discus.db")
    cursor = database.cursor()
    try:
        cursor.execute("SELECT SessionToken FROM Active WHERE UserID = ?",(int(Id),))
        token =  cursor.fetchone()
        database.close()
        if token is not None:
            return(token[0])
        else:
            return(False)
    except Exception as e:
        database.close()
        print(e,flush=True)


# Saving--------------------------------------------------------
def SaveMessage(SenderId:int,RecipientId:int,message,time,SenderKey,RecipientKey,type):
        database = sqlite3.connect(Directory + "Discus.db")
        cursor = database.cursor()
        cursor.execute("INSERT INTO Messages (Message,Time,SenderID,RecipientID, SenderKey, RecipientKey,Type) VALUES(?,?,?,?,?,?,?)",(message,time,SenderId,RecipientId,SenderKey,RecipientKey,type))
        database.commit()
        database.close()

@api.post("/api/users/unread")
async def SetUsersUnread(request: Request):
    UnreadChats = await request.json()
    for Unread in UnreadChats:
        #Unread = json.loads(Unread)
        setUnread(Unread.get("Sender"),Unread.get("Recipient"),Unread.get("Timestamp"),Unread.get("Number"))
    #print(f"i got the unread: {UnreadChats}",flush=True)

def setUnread(Id1,Id2,Timestamp,Num = None):
    #Id1 is for the recipient
    try:
        database = sqlite3.connect(Directory + "Discus.db")
        cursor = database.cursor()
        Unrd = RetrieveUnread(Id1,Id2)
        if Unrd is not None:
            num = int(Unrd[2])
            if Num is not None:
                num = Num
            else:
                num += 1
            cursor.execute("UPDATE Unread SET Messages = ? WHERE User1 = ? AND User2 = ?",(num,Id1,Id2))
        else:
            if Num is not None:
                cursor.execute("INSERT INTO Unread (User1,User2,Timestamp,Messages) VALUES (?,?,?,?)",(Id1,Id2,Timestamp,Num))
            else:
                cursor.execute("INSERT INTO Unread (User1,User2,Timestamp,Messages) VALUES (?,?,?,?)",(Id1,Id2,Timestamp,1))
        database.commit()
        database.close()
    except:
        database.rollback()
        database.close()
        e = traceback.format_exc()
        print(e,flush=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

def RetrieveUnread(Id1,Id2):
    #Id1 is for the one making the call(recipient of the unread msg) and Id2 for his friend
    database = sqlite3.connect(Directory + "Discus.db")
    cursor = database.cursor()
    cursor.execute("SELECT User2,Timestamp,Messages FROM Unread WHERE User1 = ? AND User2 = ?",(Id1,Id2))
    stuff = cursor.fetchone()
    if stuff is not None:
        #print(stuff,flush=True)
        return stuff
    database.close()

def DeleteUnread(Id1,Id2):
    try:
        database = sqlite3.connect(Directory + "Discus.db")
        cursor = database.cursor()
        cursor.execute("DELETE FROM Unread WHERE User1 = ? AND User2 = ?",(Id1,Id2))
        database.commit()
        database.close()
    except:
        database.rollback()
        database.close()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    
# Unfriending ------------------------------------------------------
@api.post("/api/friends/delete")
async def Unfriend(ID1: int = Body(...), ID2: int = Body(...)):
    database = sqlite3.connect(Directory + "Discus.db")
    cursor = database.cursor()
    try:
        if AreFriends(ID1,ID2):
            print("they are friends yes",flush=True)
            cursor.execute("UPDATE Friends SET Status = ? WHERE User1 = ? AND User2 = ? OR User1 = ? AND User2 = ?",("Deleted",ID1,ID2,ID2,ID1))
            database.commit()
            #print(f"Active Users: {ActiveUsers} aaa",flush=True)
            try:
                #print(f"ID1: {ID1}",flush=True)
                #print(f"ID2: {ID2}",flush=True)
                for client in ActiveUsers.get(ID1):
                    #print(f"The client is {ID1}",flush=True)
                    await client.send_json({"Id":ID2,"Type": "FriendDeleted"})
            except Exception as e:
                pass
                #print(f"1: {e}",flush=True)
            try:
                for client in ActiveUsers.get(ID2):
                    #print(f"The client is {ID2}",flush=True)
                    await client.send_json({"Id":ID1,"Type": "FriendDeleted"})
            except Exception as e:
                #print(f"2: {e}",flush=True)
                pass
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail=f"You are not friends with the user")
        database.close()
    except Exception as e:
        database.rollback()
        database.close()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail=f"{e}")

# Retrieving--------------------------------------------------------

#basic info of 1 user
def RetrieveUserInfo(ID):
    try:
        database = sqlite3.connect(Directory + "Discus.db")
        cursor = database.cursor()
        cursor.execute("SELECT Username,PublicKey FROM Users WHERE ID = ?",(ID,))
        Data = cursor.fetchone()
        Username = Data[0]
        PublicKey = Data[1]
        cursor.execute("SELECT Banner,Bio,Icon,Creation FROM UserInfo WHERE ID = ?",(ID,))
        Data = cursor.fetchone()
        Banner = Data[0]
        Bio = Data[1]
        Icon = Data[2]
        Creation = Data[3]
        database.close()
        return{
            "message": "Info Retrieved successfuly",
            "Username":Username,
            "publickey":PublicKey,
            "Banner":Banner,
            "Bio":Bio,
            "Icon":Icon,
            "Creation":Creation
        }
    except Exception as e:
        database.rollback()
        database.close()
        raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT,detail=f"{e}")

def RetrieveUserKeys(ID):
    try:
        database = sqlite3.connect(Directory + "Discus.db")
        cursor = database.cursor()
        cursor.execute("SELECT EncryptedKey,EnvelopeKey,Salt FROM Users WHERE ID = ?",(ID,))
        Data = cursor.fetchone()
        database.close()
        return{
            "message": "Keys Retrieved successfuly",
            "EncryptedKey":Data[0],
            "EnvelopeKey":Data[1],
            "Salt":Data[2]
        }
    except Exception as e:
        database.rollback()
        database.close()
        raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT,detail=f"{e}")

def RetrieveLastDate(Id1,Id2):
    database = sqlite3.connect(Directory + "Discus.db")
    cursor = database.cursor()
    cursor.execute("SELECT Time FROM Messages WHERE SenderID = ? and RecipientID = ? OR SenderID = ? and RecipientID = ? ORDER BY Time DESC LIMIT 1",(Id1,Id2,Id2,Id1))
    Time = cursor.fetchone()
    database.close()
    #raise Exception(Time)
    if Time is not None:
        return Time[0]
    return None

@api.get("/api/users/retrieve/messages") 
def RetrieveMessages(Id1:int = Header(...) ,Id2:int = Header(...)):
        ALLMessages = []
        CurrentMessage = {}
        database = sqlite3.connect(Directory + "Discus.db")
        cursor = database.cursor()
        cursor.execute("SELECT * FROM (SELECT * FROM Messages WHERE Type = ? AND ((SenderID = ? AND RecipientID = ?) OR (SenderID = ? AND RecipientID = ?)) ORDER BY Time DESC LIMIT 30) ORDER BY Time ASC",("Message",Id1,Id2,Id2,Id1))
        Result = cursor.fetchall()
        if Result:
            for x in Result:
                CurrentMessage = {"SenderID":x[3],
                                  "RecipientID":x[4],
                                  "SenderKey":x[5],
                                  "RecipientKey":x[6],
                                  "Text":x[1],
                                  "Time":x[2],
                                  "Type":x[7]}
                ALLMessages.append(CurrentMessage)
            return {"Messages":ALLMessages}
        return None

@api.get("/api/users/retrieve/oldmessages")
def RetrieveOldMessages(Id:int = Header(...),Friend:int = Header(...),AuthToken:str = Header(...),TimeStamp:str = Header(...)):
    PreviousMessages = []
    CurrentMessage = {}
    database = sqlite3.connect(Directory + "Discus.db")
    cursor = database.cursor()
    cursor.execute("SELECT * FROM Messages WHERE Type = ? AND Time < ? AND ((SenderID = ? AND RecipientID = ?) OR (SenderID = ? AND RecipientID = ?)) ORDER BY Time DESC LIMIT 30",("Message",TimeStamp,Id,Friend,Friend,Id))
    Result = cursor.fetchall()
    database.close()
    if Result:
        for x in Result:
            CurrentMessage = {"SenderID":x[3],
                            "RecipientID":x[4],
                            "SenderKey":x[5],
                            "RecipientKey":x[6],
                            "Text":x[1],
                            "Time":x[2],
                            "Type":x[7]}
            PreviousMessages.append(CurrentMessage)
        return {"Messages":PreviousMessages}
    return None

#get a users friends
@api.get("/api/users/retrieve/friends") 
def RetrieveFriends(ID: int = Header(...)):
    PendingSent = []
    PendingReceived = []
    Friends = []
    NonRead = []
    LastTimestamps = []
    try:
        database = sqlite3.connect(Directory + "Discus.db")
        cursor = database.cursor()
        cursor.execute("SELECT User1,User2,Status FROM Friends WHERE User1 = ? OR User2 = ?",(ID,ID))
        Data = cursor.fetchall()
        for friends in Data:
            if friends[2] == "Accepted" or friends[2] == "Deleted" or friends [2] == "RePending":
                temp1 = RetrieveUserInfo(friends[0])
                temp2 = RetrieveUserInfo(friends[1])
                Timestamp = RetrieveLastDate(friends[0],friends[1])
                if friends[0] == ID:
                    Friends.append(({"SenderId":friends[1],"SenderName":temp2.get("Username"),"RecipientId":friends[0],"RecipientName":temp1.get("Username"),
                                    "Banner":temp2.get("Banner"),"Bio":temp2.get("Bio"),"Icon":temp2.get("Icon"),"Creation":temp2.get("Creation"),"Status":friends[2],"PublicKey":temp2.get("publickey")}))
                    LastTimestamps.append((friends[1],Timestamp))
                elif friends[1] == ID:
                    Friends.append(({"SenderId":friends[0],"SenderName":temp1.get("Username"),"RecipientId":friends[1],"RecipientName":temp2.get("Username"),
                                     "Banner":temp1.get("Banner"),"Bio":temp1.get("Bio"),"Icon":temp1.get("Icon"),"Creation":temp1.get("Creation"),"Status":friends[2],"PublicKey":temp1.get("publickey")}))
                    LastTimestamps.append((friends[0],Timestamp))
            if friends [2] == "Pending" or friends [2] == "RePending":
                temp1 = RetrieveUserInfo(friends[0])
                temp2 = RetrieveUserInfo(friends[1])
                if friends[0] == ID:
                    PendingSent.append(({"SenderId":friends[0],"SenderName":temp1.get("Username"),"RecipientId":friends[1],"RecipientName":temp2.get("Username"),"Icon":temp2.get("Icon")}))
                elif friends[1] == ID:
                    PendingReceived.append(({"SenderId":friends[0],"SenderName":temp1.get("Username"),"RecipientId":friends[1],"RecipientName":temp2.get("Username"),"Icon":temp1.get("Icon")})) 
            if friends[0] == ID:
                Unread = RetrieveUnread(ID,friends[1])
            elif friends[1] == ID:
                Unread = RetrieveUnread(ID,friends[0])
            NonRead.append(Unread)
        database.close()
        return{
            "Friends":Friends,
            "PendingSent":PendingSent,
            "PendingReceived":PendingReceived,
            "NonRead":NonRead,
            "LastTimestamps":LastTimestamps
        }
    except Exception as e:
        database.close()
        a = traceback.format_exc()
        print(a,flush=True)
        raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT,detail=f"{e}")   

# get friend status
@api.post("/api/users/retrieve/status") 
def RetrieveStatus(Group: list = Body(...)):
    Group2 = {}
    try:
        database = sqlite3.connect(Directory + "Discus.db")
        cursor = database.cursor()
        for x in Group:
            cursor.execute("SELECT UserID FROM Active WHERE UserID = ?",(x,))
            Data = cursor.fetchone()
            if Data is not None:
                Group2[x] = "Online"
            else:
                Group2[x] = "Offline"
        try:
            database.close()
        except:
            pass
        return{"Group":Group2}
    except Exception as e:
        database.close()
        raise HTTPException(status.HTTP_408_REQUEST_TIMEOUT,detail=f"{e}")



# Check password
def CheckPassword(id,password):
    database = sqlite3.connect(Directory + "Discus.db")
    cursor = database.cursor()
    cursor.execute("SELECT Password FROM Users WHERE ID = ?",(id,))
    pswrd = cursor.fetchone()
    database.close()
    if pswrd is not None:
        pswrd = pswrd[0]
        if bcrypt.checkpw(password.encode("utf-8"),pswrd.encode("utf-8")):
            return True
        else:
            return False
    else:
        return False

# Changing User Info------------------------------------------------
Characters = string.ascii_letters + string.digits + "_."
def ValidChar(text):
    if not text:
        return False
    return all(char in Characters for char in text)

@api.post("/api/users/username")
def ChangeUsername(Id: int = Body(...), NewUser: str = Body(...), Password: str = Body(...), Token: str = Body(...)):
    if CheckSessionToken(Id,Token):
        if CheckPassword(Id,Password):
            if ValidChar(NewUser):
                if len(NewUser) <= 20:
                    try:
                        database = sqlite3.connect(Directory + "Discus.db")
                        cursor = database.cursor()
                        cursor.execute("UPDATE Users SET Username = ? WHERE ID = ?",(NewUser,Id))
                        database.commit()
                        database.close()
                        print(f"new user is {NewUser}",flush=True)
                        return{
                            "message":"Name changed successfuly",
                            "Name": NewUser
                        }
                    except:
                        database.rollback()
                        database.close()
                        raise HTTPException(status.HTTP_408_REQUEST_TIMEOUT,detail="An error occured")
                else:
                    raise HTTPException(status.HTTP_400_BAD_REQUEST,detail="Name is too long")   
            else:
                raise HTTPException(status.HTTP_400_BAD_REQUEST,detail="Unaccepted characters")
        else:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,detail="Wrong Password")
    else:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,detail="Authentication Failed")

@api.post("/api/users/password")
def ChangePassword(Id: int = Body(...), Password: str = Body(...), NewPassword: str = Body(...), Token: str = Body(...),EnvelopeKey:str = Body(...)):
    if CheckSessionToken(Id,Token):
        if CheckPassword(Id,Password):
            try:
                HashedPassword = bcrypt.hashpw(NewPassword.encode("utf-8"),salt=bcrypt.gensalt())
                database = sqlite3.connect(Directory + "Discus.db")
                cursor = database.cursor()
                cursor.execute("UPDATE Users SET Password = ? , EnvelopeKey = ? WHERE ID = ?",(HashedPassword.decode("utf-8"),EnvelopeKey,Id))
                database.commit()
                database.close()
                return{
                    "message":"Password changed successfuly"
                }
            except:
                database.rollback()
                database.close()
                e = traceback.format_exc()
                raise HTTPException(status.HTTP_408_REQUEST_TIMEOUT,detail=f"An error occured {e}")
        else:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,detail="Wrong Password")
    else:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,detail="Authentication Failed")

@api.post("/api/users/icon")
async def ChangeIcon(Id: int = Form(...), Image: UploadFile = File(...), Token: str = Form(...)):
    if CheckSessionToken(Id,Token):
        try:
            Bytes =  await Image.read()
            headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            #the most tiring thing i did bro
            response = requests.post("https://freeimage.host/api/1/upload",data={"key":"6d207e02198a847aa98d0a2a901485a5","action": "upload","format": "json"},files={"source": (Image.filename, Bytes,Image.content_type)})
            if response.status_code == 200:
                PublicUrl = response.json()["image"]["url"]
                try:
                    database = sqlite3.connect(Directory + "Discus.db")
                    cursor = database.cursor()
                    cursor.execute("UPDATE UserInfo SET Icon = ? WHERE ID = ?",(PublicUrl,Id))
                    database.commit()
                    database.close()
                    return{
                        "message":"Icon changed successfully",
                        "image": PublicUrl
                    }
                except:
                    database.rollback()
                    database.close()
                    raise HTTPException(status.HTTP_408_REQUEST_TIMEOUT,detail="An error occured")
            else:
                raise HTTPException(status.HTTP_408_REQUEST_TIMEOUT,detail="Upload Failed")
        except Exception as e:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT,detail=f"{e}")
    else:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,detail="Couldnt identify the user")

@api.post("/api/users/banner")
def ChangeBanner(Id: int = Body(...), Color: str = Body(...), Token: str = Body(...)):
    if CheckSessionToken(Id,Token):
        try:
            database = sqlite3.connect(Directory + "Discus.db")
            cursor = database.cursor()
            cursor.execute("UPDATE UserInfo SET Banner = ? WHERE ID = ?",(Color,Id))
            database.commit()
            database.close()
            return{
                "message":"Banner color changed",
                "color": Color
            }
        except:
            database.rollback()
            database.close()
            raise HTTPException(status.HTTP_408_REQUEST_TIMEOUT,detail="An error occured")
    else:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,detail="Couldnt identify the user")

@api.post("/api/users/bio")
def ChangeBio(Id: int = Body(...), Bio: str = Body(...), Token: str = Body(...)):
    if CheckSessionToken(Id,Token):
        try:
            database = sqlite3.connect(Directory + "Discus.db")
            cursor = database.cursor()
            cursor.execute("UPDATE UserInfo SET Bio = ? WHERE ID = ?",(Bio,Id))
            database.commit()
            database.close()
            return{
                "message":"User bio changed",
                "bio": Bio
            }
        except:
            database.rollback()
            database.close()
            raise HTTPException(status.HTTP_408_REQUEST_TIMEOUT,detail="An error occured")
    else:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,detail="Couldnt identify the user")



# Login and signup--------------------------------------------------
@api.get("/api/users/info") 
def GetUserInfo(Authentication: str = Header(...)):
    try:
        database = sqlite3.connect(Directory + "Discus.db")
        cursor = database.cursor()
        cursor.execute("SELECT Username,ID FROM Users WHERE AuthToken = ?",(Authentication,))
        User = cursor.fetchone()
        database.close()
        if User is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User Not Found")
        Data = RetrieveUserInfo(User[1])
        #Token = SessionToken(User[1])
        Token = AlrdInSession(User[1])
        if not Token:
            Token = SessionToken(User[1])
            print("I made a new session token")
        return{
            "username":User[0],
            "id":User[1],
            "message":"Auto Login successful",
            "token":Token,
            "banner":Data.get("Banner"),
            "bio":Data.get("Bio"),
            "icon":Data.get("Icon"),
            "Creation":Data.get("Creation"),
            "publickey":Data.get("publickey")
        }
    except Exception as e:
        database.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail= "Failed to Login")


@api.get("/api/signup")
def CreateUser(Username:str = Header(...), Password: str = Header(...),EncryptedKey: str = Header(...), EnvelopeKey:str = Header(...), Salt:str = Header(...),PublicKey:str = Header(...)):
    database = sqlite3.connect(Directory + "Discus.db")
    cursor = database.cursor()
    cursor.execute("SELECT Username FROM Users WHERE Username = ?",(Username,))
    exits  = cursor.fetchone()
    if exits:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="Username is taken")
    try:
        AuthToken = secrets.token_hex(32)
        HashedPassword = bcrypt.hashpw(Password.encode("utf-8"),salt=bcrypt.gensalt())
        cursor.execute("INSERT INTO Users (Username,Password,AuthToken,EncryptedKey,EnvelopeKey,Salt,PublicKey) VALUES (?,?,?,?,?,?,?)",(Username,HashedPassword.decode("utf-8"),AuthToken,EncryptedKey,EnvelopeKey,Salt,PublicKey))
        cursor.execute("SELECT ID FROM Users WHERE Username = ?",(Username,))
        ID = cursor.fetchone()[0]
        cursor.execute("INSERT INTO UserInfo (ID,Banner,Bio,Icon,Creation) VALUES (?,?,?,?,?)",(ID,"rgb(255,255,255)","Discus User","https://iili.io/nzAOFje.png",datetime.now().strftime("%d %B %Y")))
        database.commit()
        database.close()
        return {"message":"Account Created",
                "authtoken":AuthToken,
                "username":Username,
                "id":ID}
    except Exception as e:
        database.rollback()
        database.close()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail= f"Failed to create an account.Please try again later {e}")
    finally:
        AuthToken = None
        ID = None

        
@api.get("/api/login")
def LogIn(Username:str = Header(...), Password: str = Header(...)):
    if not Username.strip() or not Password.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and Password cannot be empty"
        )
    database = sqlite3.connect(Directory + "Discus.db")
    cursor = database.cursor()
    cursor.execute("SELECT Password,ID FROM Users WHERE Username = ?",(Username,))
    match = cursor.fetchone()
    if match is None:
        raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
    pswrd = match[0]
    ID = match[1]
    try:
        if bcrypt.checkpw(Password.encode("utf-8"),pswrd.encode("utf-8")):
            try:
                AuthToken = secrets.token_hex(32)
                cursor.execute("UPDATE Users SET AuthToken = ? WHERE Username = ?",(AuthToken,Username))
                database.commit()
                database.close()
                Data = RetrieveUserInfo(str(ID))
                Keys = RetrieveUserKeys(str(ID))
                #
                Token = AlrdInSession(str(ID))
                if not Token:
                    Token = SessionToken(str(ID))
                    print("I made a new session token")
                return {
                    "authtoken":AuthToken,
                    "username":Username,
                    "id": ID,
                    "message":"Successful login",
                    "token":Token,
                    "banner":Data.get("Banner"),
                    "bio":Data.get("Bio"),
                    "icon":Data.get("Icon"),
                    "Creation":Data.get("Creation"),
                    "encryptedkey":Keys.get("EncryptedKey"),
                    "envelopekey":Keys.get("EnvelopeKey"),
                    "salt":Keys.get("Salt"),
                    "publickey":Data.get("publickey")
                }
            except Exception as e:
                database.rollback()
                database.close()
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail= "Failed to Authorize")
            finally:
                AuthToken = None
                ID = None
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
    except Exception as e:
        print(e,flush=True)
        e = traceback.format_exc()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,detail="Invalid username or password")


@api.post("/api/logout")
def LogOut(Id: int = Body(...),SessionToken: str = Body(...)):
    if CheckSessionToken(Id,SessionToken):
        pass


uvicorn.run(api, host="0.0.0.0", port=8000)
