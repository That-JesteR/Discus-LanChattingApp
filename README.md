# Discus-LanChattingApp

A basic copy of discord i made using python, this project is for showcasing only.

The project makes use of:

- Sqlite3 as the database.
- Fast API and Requests for the api.
- Bcrypt and Cryptography for the hashing and Encryption.
- Pyside6 for all the window and GUI work.
- websockets for the real time communication between client server such as notification and friend messages.
- Qasync and Asyncio for making the code run asyncronously and prevent GUI freezing.
- Other libraries such as PIL,datetime,io,os,base64,string

For a more convinient set-up 2 .exe's are provided on the Release tab: https://github.com/That-JesteR/Discus-LanChattingApp/releases/tag/v1.0.0

How to use:

  - 1.The server "Discus - Server.exe" needs to be hosted somewhere,a device can be used to host the server on by running it.
  - 2.For the client "Discus - Client.exe" to connect to the server, the IP in the "config.json" file must corespond to the IP adress of the device that is hosting the server.
  - 3.Once everything is set correctly the app should work as intended,make sure that the "icons" folder is on the same directory or folder as the running .exe and the "config.json" or the icons wont show up.
  - 4.All good to go.
