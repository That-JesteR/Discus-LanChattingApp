import PySide6.QtWidgets as pyside
from PySide6.QtCore import Qt,QTime,QTimer,QPropertyAnimation,QSize,Signal,Property,QUrl,QSettings
from PySide6.QtGui import QIcon,QTextOption,QTextDocument,QTextOption,QPainter,QFont,QColor,QPalette,QPainterPath,QTextCursor,QPixmap,QPen
from PySide6.QtMultimedia import QSoundEffect
from qasync import QEventLoop
from random import randint
import sys
import requests
import keyring
import json
import asyncio
import websockets
import traceback
import string
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import load_pem_public_key,load_pem_private_key #okey this import was kinda stupid too lazy to change it
from datetime import datetime, timedelta
from fastapi.encoders import jsonable_encoder
from PIL import Image as Pillow
import io

#NOTES
#put websocket connection after friend retrieval

def UrlToData(url):
    try:
        Data = (requests.get(url).content)
        return Data
    except Exception as e:
        print(e)
        return None

def SortDictionary(Dictionary):
    return dict(sorted(Dictionary.items(), key=lambda item: item[1]))

class StampTimer():
    def __init__(self,label:str):
        self.Label = label
        self.StartTime = datetime.now()
    def Start(self,newlbl = None):
        if newlbl is not None:
            self.Label = newlbl
        self.StartTime = datetime.now()
    def Stop(self):
        self.StopTime = datetime.now()
        print("----------------------------------")
        print(f"{self.Label} took {self.StopTime - self.StartTime}")
        print("----------------------------------")
    
class CreateWindow(pyside.QMainWindow):
    PrivateMakerSignal = Signal(int,str,bool,str,str,str,str)
    def __init__(self):
        super().__init__()
        self.resize(1235,600)
        self.setWindowTitle("Discus")
        #
        self.PrivateMakerSignal.connect(self.TriggerPrivateChat)
        #
        self.Connections = {}
        self.User = {
            "ID": None,
            "Name":None,
            "Token":None,
            "Socket":None
        }
        # default pic is https://iili.io/nzAOFje.png
        self.Friends = [] #list for friends [id,name]
        self.FriendInfo = [] #list for friends info [id,banner,bio,icon,etc]
        self.FriendRequests = [] #list with the name of the one u sending the request to
        self.PendingRequests = [] 
        self.FriendRequestsWidgets = {} #list for friends requests received [Id:QWidget]
        self.PendingRequestWidgets = {} #list for friends requests sent [Id:QWidget]
        self.CurrentId = None #Id of the page u are in to use for the websocket
        self.FirstMesg = None#first msg
        self.LastMesg = None #last msg
        self.LastMesgs = {}
        self.PendingCounter = 0 #counter for pending people
        self.OnlineCounter = 0 #counter for online people
        self.RequestsCounter = 0 #counter for requests pending
        self.AllCounter = 0 #counter for online and offline people
        self.AllFriendsWidgets = {} #dictionary for friend widgets {id:widget}
        self.MessageHistory = {} #friend id:list with recent messages
        self.TempMessages = []
        self.PrivChats = {} #id:privmessages
        self.Timestamps = {} #id:timestamp
        self.RandomKeyCounter = 0
        self.CurrentRKey = None
        self.FriendRKey = None
        #
        self.R = 0
        self.G = 0
        self.B = 0
        self.RR = 0
        self.GG = 0
        self.BB = 255
        #
        self.TargetIP = "192.168.1.145"
        #self.TargetIP = "10.0.3.218"
        #self.IconFolder = "C:/Users/Frantzesk/Documents/Python/API ENDPOINT WITH DB/Icons/"
        self.IconFolder = "Icons/"
        #
        self.SoundPlayer = QSoundEffect()
        self.SoundPlayer.setSource(QUrl.fromLocalFile(self.IconFolder + "DC.wav"))
        self.SoundPlayer.setVolume(1)
        #5
        self.Settings = QSettings("Myself","Discus")
        #
        self.Loading = False
        self.SavedUSIB = True
        #
        # self.UnreadTimer = QTimer(self)
        # self.UnreadTimer.setInterval(10000)
        # self.UnreadTimer.setSingleShot(True)
        #
        self.Main = pyside.QWidget()
        self.Main.setStyleSheet("background-color: rgb(30,30,30); outline: none;")
        self.Layout = pyside.QGridLayout(self.Main)
        self.Layout.setSpacing(0)
        self.Layout.setContentsMargins(0,0,0,0)
        self.setCentralWidget(self.Main)
        # Tabwidget
        self.Pages = pyside.QTabWidget()
        self.Pages.setDocumentMode(True)
        self.Pages.setStyleSheet("border-none;")
        self.Pages.tabBar().hide()
        self.Layout.addWidget(self.Pages)
        # Log In Tab
        self.LogInTab = pyside.QWidget()
        self.LogInTab.setStyleSheet("background-color: rgb(30,30,30);")
        self.LogInTabLayout = pyside.QGridLayout(self.LogInTab)
        self.LogInTabLayout.setColumnStretch(0,3)
        self.LogInTabLayout.setColumnStretch(1,4)
        self.LogInTabLayout.setColumnStretch(2,3)
        self.LogInTabLayout.setRowStretch(0,1)
        self.LogInTabLayout.setRowStretch(1,2)
        self.LogInTabLayout.setRowStretch(2,1)
        # LogIn-SignUp PageTab
        self.AuthPage = pyside.QTabWidget()
        self.AuthPage.setDocumentMode(True)
        self.AuthPage.setStyleSheet("border-none; border-radius: 10px;")
        self.AuthPage.tabBar().hide()
        self.LogInTabLayout.addWidget(self.AuthPage,1,1)
        #-------------------------------------------------------
        # Connecting page
        self.ConnectingPage = pyside.QWidget()
        self.ConnectingPage.setStyleSheet("background-color: rgb(35,35,35); border-radius: 10px;")
        self.ConnectingLayout = pyside.QGridLayout(self.ConnectingPage)
        self.ConnectingLayout.setRowStretch(4,1)
        #
        self.ConnectingLabel = pyside.QLabel("Connection Interrupted")
        self.ConnectingLabel.setStyleSheet("font-size: 40px; color: white; margin: 50px; margin-bottom: 0px; border-radius: 0px; font-weight: 600;")
        self.ConnectingLayout.addWidget(self.ConnectingLabel,0,0,alignment=Qt.AlignmentFlag.AlignHCenter)
        #
        self.Con = pyside.QWidget()
        self.ConL = pyside.QGridLayout(self.Con)
        self.ConL.setColumnStretch(0,1)
        self.ConL.setColumnStretch(3,1)
        self.ConnectingLayout.addWidget(self.Con)
        #
        self.ConnectingLabel2 = pyside.QLabel("Connection lost.Trying to reconnect automatically...")
        self.ConnectingLabel2.setStyleSheet("font-size: 30px; color: white; margin: 50px; margin-top: 10px; margin-right: 10px; border-radius: 0px; margin-bottom: 5px;")
        self.ConL.addWidget(self.ConnectingLabel2,0,1,alignment=Qt.AlignmentFlag.AlignHCenter)
        #
        self.DiscImage = pyside.QLabel("")
        self.DiscImage.setFixedSize(QSize(300,300))
        self.DiscImage.setScaledContents(True)
        self.DiscPix = QPixmap(self.IconFolder + "DisconnectedFace.png")
        self.DiscImage.setPixmap(self.DiscPix)
        self.ConnectingLayout.addWidget(self.DiscImage,2,0,alignment=Qt.AlignmentFlag.AlignHCenter)
        #
        self.Box = pyside.QWidget()
        self.Box.setFixedSize(100,100)
        self.ConL.addWidget(self.Box,0,2,alignment=Qt.AlignmentFlag.AlignLeft)
        #
        self.SpinCircle = SimpleSpinner(self.Box)
        self.SpinCircle.move(0,25)
        #--------------------------------------------------------
        #loading page
        self.LoadingPage = pyside.QWidget()
        self.LoadingPage.setStyleSheet("background-color: rgb(35,35,35); border-radius: 10px;")
        self.LoadingLayout = pyside.QGridLayout(self.LoadingPage)
        self.LoadingLayout.setRowStretch(0,1)
        self.LoadingLayout.setRowStretch(1,1)
        self.LoadingLayout.setRowStretch(2,1)
        self.LoadingLayout.setRowStretch(3,1)
        self.LoadingLayout.setRowStretch(4,1)
        #
        self.AnimPix = QPixmap(self.IconFolder + "Test3.png")
        self.AnimLabel = pyside.QLabel("")
        #self.AnimPix = self.AnimPix.scaled(QSize(400,250),Qt.KeepAspectRatio,Qt.SmoothTransformation)
        self.AnimPix = self.AnimPix.scaled(QSize(500,350),Qt.KeepAspectRatio,Qt.SmoothTransformation)
        self.AnimLabel.setPixmap(self.AnimPix)
        self.AnimLabel.setStyleSheet("font-size: 50px; color: white; margin: 50px; margin-bottom: 0px; border-radius: 0px; font-weight: 600;")
        self.LoadingLayout.addWidget(self.AnimLabel,0,0,alignment=Qt.AlignmentFlag.AlignHCenter)
        #
        self.Con = pyside.QWidget()
        self.ConL = pyside.QGridLayout(self.Con)
        self.ConL.setColumnStretch(0,1)
        self.ConL.setColumnStretch(3,1)
        self.LoadingLayout.addWidget(self.Con)
        #
        self.PercentageLbl = pyside.QLabel("0%")
        self.PercentageLbl.setStyleSheet("font-size: 30px; color: white; margin: 50px; margin-bottom: 0px; border-radius: 0px; font-weight: 600;")
        self.LoadingLayout.addWidget(self.PercentageLbl,2,0,alignment=Qt.AlignmentFlag.AlignHCenter)
        #
        self.SpinCircle2 = SimpleSpinner()
        #self.LoadingLayout.addWidget(self.SpinCircle2,3,0,alignment=Qt.AlignmentFlag.AlignHCenter)
        #
        self.LoadingBar = LoadingBar()
        self.LoadingLayout.addWidget(self.LoadingBar,3,0,alignment=Qt.AlignmentFlag.AlignHCenter)
        #---------------------------------------------------------
        # LogIn Page
        self.LogInPage = pyside.QWidget()
        self.LogInPage.setStyleSheet("background-color: rgb(35,35,35); border-radius: 10px;")
        self.LogInLayout = pyside.QGridLayout(self.LogInPage)
        #
        self.LogInLabel = pyside.QLabel("Log In")
        self.LogInLabel.setStyleSheet("font-size: 40px; color: white; margin: 20px; margin-top: 10px; border-bottom: 1px solid white; border-radius: 0px;")
        self.LogInLayout.addWidget(self.LogInLabel,0,1,alignment=Qt.AlignmentFlag.AlignHCenter)
        #
        self.UserLabel = pyside.QLabel("Username")
        self.UserLabel.setStyleSheet("font-size: 30px; color: white; margin: 20px; margin-top: 0px; margin-bottom: 10px;")
        self.LogInLayout.addWidget(self.UserLabel,1,1)
        self.UserFeild = pyside.QLineEdit()
        #self.UserFeild.setText("why")
        self.UserFeild.setPlaceholderText("Enter username")
        self.UserFeild.setStyleSheet("background-color: rgb(45,45,45); color: white; font-size: 25px; padding: 5px; border-radius: 10px; margin: 20px; margin-top: 0px;")
        self.LogInLayout.addWidget(self.UserFeild,2,1)
        #
        self.PassLabel = pyside.QLabel("Password")
        self.PassLabel.setStyleSheet("font-size: 30px; color: white; margin: 20px; margin-top: 0px; margin-bottom: 10px;")
        self.LogInLayout.addWidget(self.PassLabel,3,1)
        self.PassFeild = pyside.QLineEdit()
        self.PassFeild.setEchoMode(pyside.QLineEdit.EchoMode.Password)
        #self.PassFeild.setText("12345")
        self.PassFeild.setPlaceholderText("Enter password")
        self.PassFeild.setStyleSheet("background-color: rgb(45,45,45); color: white; font-size: 25px; padding: 5px; border-radius: 10px; margin: 20px; margin-top: 0px; margin-bottom: 0px;")
        self.LogInLayout.addWidget(self.PassFeild,4,1)
        #
        self.toSignWidget = pyside.QWidget()
        self.toSignWidget.setStyleSheet("margin-left: 20px; margin-bottom: 5px;")
        self.toSignWidget.setSizePolicy(pyside.QSizePolicy.Policy.Maximum,pyside.QSizePolicy.Policy.Maximum)
        self.toSignLayout = pyside.QHBoxLayout(self.toSignWidget)
        self.LogInLayout.addWidget(self.toSignWidget,5,1)
        self.toSignLabel = pyside.QLabel("Dont have an account?")
        self.toSignLabel.setStyleSheet("font-size: 15px; color: white;")
        self.toSignLayout.addWidget(self.toSignLabel)
        self.toSignButton = pyside.QPushButton("Sign Up")
        self.toSignButton.setStyleSheet("""QPushButton{background-color: transparent; color: rgb(100,100,250); border: none; font-weight: 600; border-bottom: 1px solid rgb(100,100,250); margin-left: 0px;}
                                            QPushButton:hover{color: rgb(50,50,200); font-weight: 600;}""")
        self.toSignButton.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toSignButton.clicked.connect(lambda:self.toSignPage())
        self.toSignLayout.addWidget(self.toSignButton)
        #
        self.ErrorReport = pyside.QLabel("test")
        self.ErrorReport.setSizePolicy(pyside.QSizePolicy.Policy.Maximum,pyside.QSizePolicy.Policy.Maximum)
        self.ErrorReport.setStyleSheet("font-size: 15px; color: red; margin: 30px; margin-top: 0px; margin-bottom: 0px; font-weight: 600;")
        self.LogInLayout.addWidget(self.ErrorReport,6,1)
        self.ErrorReport.hide()
        #
        self.SubmitLogIn = pyside.QPushButton("Log In")
        self.SubmitLogIn.setMaximumWidth(300)
        self.SubmitLogIn.setMinimumWidth(200)
        self.SubmitLogIn.setStyleSheet("""QPushButton{background-color: rgb(50,50,50); color: white; border-radius: 10px; font-size: 27px; margin: 20px; margin-top: 10px;}
                                    QPushButton:hover{background-color: rgb(70,70,70);}""")
        self.SubmitLogIn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.SubmitLogIn.clicked.connect(lambda:asyncio.create_task(self.Login()))
        self.LogInLayout.addWidget(self.SubmitLogIn,7,1,alignment=Qt.AlignmentFlag.AlignHCenter)
        #-------------------------------------------------------
        # SignUp Page
        self.SignUpPage = pyside.QWidget()
        self.SignUpPage.setStyleSheet("background-color: rgb(35,35,35); border-radius: 10px;")
        self.SignUpLayout = pyside.QGridLayout(self.SignUpPage)
        #
        self.SignUpLabel = pyside.QLabel("Sign Up")
        self.SignUpLabel.setStyleSheet("font-size: 40px; color: white; margin: 20px; margin-top: 10px; border-bottom: 1px solid white; border-radius: 0px;")
        self.SignUpLayout.addWidget(self.SignUpLabel,0,1,alignment=Qt.AlignmentFlag.AlignHCenter)
        #
        self.UserLabel2 = pyside.QLabel("Username")
        self.UserLabel2.setStyleSheet("font-size: 30px; color: white; margin: 20px; margin-top: 0px; margin-bottom: 10px;")
        self.SignUpLayout.addWidget(self.UserLabel2,1,1)
        self.UserFeild2 = pyside.QLineEdit()
        self.UserFeild2.setPlaceholderText("Enter username")
        self.UserFeild2.setStyleSheet("background-color: rgb(45,45,45); color: white; font-size: 25px; padding: 5px; border-radius: 10px; margin: 20px; margin-top: 0px;")
        self.SignUpLayout.addWidget(self.UserFeild2,2,1)
        #
        self.PassLabel2 = pyside.QLabel("Password")
        self.PassLabel2.setStyleSheet("font-size: 30px; color: white; margin: 20px; margin-top: 0px; margin-bottom: 10px;")
        self.SignUpLayout.addWidget(self.PassLabel2,3,1)
        self.PassFeild2 = pyside.QLineEdit()
        self.PassFeild2.setEchoMode(pyside.QLineEdit.EchoMode.Password)
        self.PassFeild2.setPlaceholderText("Enter password")
        self.PassFeild2.setStyleSheet("background-color: rgb(45,45,45); color: white; font-size: 25px; padding: 5px; border-radius: 10px; margin: 20px; margin-top: 0px; margin-bottom: 0px;")
        self.SignUpLayout.addWidget(self.PassFeild2,4,1)
        #
        self.toLoginWidget = pyside.QWidget()
        self.toLoginWidget.setStyleSheet("margin-left: 20px;")
        self.toLoginWidget.setSizePolicy(pyside.QSizePolicy.Policy.Maximum,pyside.QSizePolicy.Policy.Maximum)
        self.toLoginLayout = pyside.QHBoxLayout(self.toLoginWidget)
        self.SignUpLayout.addWidget(self.toLoginWidget,5,1)
        self.toLoginLabel = pyside.QLabel("Already have an account?")
        self.toLoginLabel.setStyleSheet("font-size: 15px; color: white;")
        self.toLoginLayout.addWidget(self.toLoginLabel)
        self.toSignButton = pyside.QPushButton("Log In")
        self.toSignButton.setStyleSheet("""QPushButton{background-color: transparent; color: rgb(100,100,250); border: none; font-weight: 600; border-bottom: 1px solid rgb(100,100,250); margin-left: 0px;}
                                            QPushButton:hover{color: rgb(50,50,200); font-weight: 600;}""")
        self.toSignButton.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toSignButton.clicked.connect(lambda:self.toLogPage())
        self.toLoginLayout.addWidget(self.toSignButton)
        #
        self.ErrorReport2 = pyside.QLabel("test")
        self.ErrorReport2.setSizePolicy(pyside.QSizePolicy.Policy.Maximum,pyside.QSizePolicy.Policy.Maximum)
        self.ErrorReport2.setStyleSheet("font-size: 15px; color: red; margin: 30px; margin-top: 0px; margin-bottom: 0px; font-weight: 600;")
        self.SignUpLayout.addWidget(self.ErrorReport2,6,1)
        self.ErrorReport2.hide()
        #
        self.SubmitSignUp = pyside.QPushButton("Sign Up")
        self.SubmitSignUp.setMaximumWidth(300)
        self.SubmitSignUp.setMinimumWidth(200)
        self.SubmitSignUp.setStyleSheet("""QPushButton{background-color: rgb(50,50,50); color: white; border-radius: 10px; font-size: 27px; margin: 20px; margin-top: 10px;}
                                    QPushButton:hover{background-color: rgb(70,70,70);}""")
        self.SubmitSignUp.setCursor(Qt.CursorShape.PointingHandCursor)
        self.SubmitSignUp.clicked.connect(lambda:asyncio.create_task(self.SignUp()))
        self.SignUpLayout.addWidget(self.SubmitSignUp,7,1,alignment=Qt.AlignmentFlag.AlignHCenter)
        #-------------------------------------------------------
        # Main Page
        self.Interface = pyside.QWidget()
        self.Interface.setStyleSheet("background-color: rgb(30,30,30);")
        self.InterfaceLayout = pyside.QGridLayout(self.Interface)
        self.InterfaceLayout.setContentsMargins(0,0,0,0)
        self.InterfaceLayout.setSpacing(0)
        self.InterfaceLayout.setColumnStretch(0,2)
        self.InterfaceLayout.setColumnStretch(1,9)
        self.InterfaceLayout.setRowStretch(0,1)
        self.InterfaceLayout.setRowStretch(1,19)
        #split into parts
        #Half Upper bar
        self.HUpper = pyside.QWidget()
        self.HUpperLayout = pyside.QGridLayout(self.HUpper)
        self.HUpper.setStyleSheet("background-color: rgb(20,20,20); border: 1px solid rgb(100,100,100); border-right: none;")
        self.InterfaceLayout.addWidget(self.HUpper,0,0)
        #Upper bar
        self.Upper = pyside.QWidget()
        self.Upper.setMaximumHeight(63)
        self.UpperLayout = pyside.QGridLayout(self.Upper)
        self.UpperLayout.setSpacing(0)
        self.UpperLayout.setContentsMargins(0,0,0,0)
        self.Upper.setStyleSheet("background-color: rgb(30,30,30); border: 1px solid rgb(100,100,100); border-left: none;")
        self.InterfaceLayout.addWidget(self.Upper,0,1)
        #side bar
        self.Side = pyside.QWidget()
        self.SideLayout = pyside.QGridLayout(self.Side)
        self.SideLayout.setSpacing(0)
        self.SideLayout.setContentsMargins(0,0,0,0)
        self.Side.setStyleSheet("""QWidget{background-color: rgb(20,20,20); border: 1px solid rgb(100,100,100); border-top: none; border-right: none; border-bottom: none;}""")
        self.Side.setFixedWidth(225)
        self.InterfaceLayout.addWidget(self.Side,1,0)
        #texting area
        self.TextArea = pyside.QWidget()
        self.TextAreaLayout = pyside.QGridLayout(self.TextArea)
        self.TextAreaLayout.setSpacing(0)
        self.TextAreaLayout.setContentsMargins(0,0,0,0)
        self.TextArea.setStyleSheet("background-color: rgb(0,100,0);")
        self.InterfaceLayout.addWidget(self.TextArea,1,1,2,1)
        #chat area
        self.ChatArea = pyside.QWidget()
        self.ChatAreaLayout = pyside.QGridLayout(self.ChatArea)
        self.ChatAreaLayout.setSpacing(0)
        self.ChatAreaLayout.setContentsMargins(0,0,0,0)
        self.ChatArea.setStyleSheet("background-color: rgb(150,150,0);")
        self.TextAreaLayout.addWidget(self.ChatArea,0,0)
        #add friend area
        self.AddArea = pyside.QWidget()
        self.AddAreaLayout = pyside.QGridLayout(self.AddArea)
        self.AddAreaLayout.setSpacing(0)
        self.AddAreaLayout.setContentsMargins(0,0,0,0)
        self.AddArea.setStyleSheet("background-color: rgb(30,30,30);")
        #profile and stuff
        self.DetailsArea = pyside.QWidget()
        self.DetailsArea.setFixedWidth(300)
        self.DetailsAreaLayout = pyside.QGridLayout(self.DetailsArea)
        self.DetailsAreaLayout.setSpacing(0)
        self.DetailsAreaLayout.setContentsMargins(0,0,0,0)
        self.DetailsArea.setStyleSheet("background-color: rgb(30,30,30); border-right: 1px solid rgb(100,100,100); border-bottom: 1px solid rgb(100,100,100); border-top: none;")
        self.TextAreaLayout.addWidget(self.DetailsArea,0,1)
        #---------------------------------------------------------------------
        #Info Page
        self.InfoPage = pyside.QWidget()
        self.InfoPageLayout = pyside.QGridLayout(self.InfoPage)
        self.InfoPageLayout.setSpacing(0)
        self.InfoPageLayout.setContentsMargins(0,0,0,0)
        self.InfoPage.setStyleSheet("background-color: rgb(30,30,30);")
        #
        self.InfoScroll = pyside.QScrollArea()
        self.InfoScroll.setStyleSheet("background-color: transparent; border: none;")
        self.InfoScroll.verticalScrollBar().setStyleSheet("""
                    QScrollBar:vertical {
                        border: none;
                        background: rgb(30, 30, 30);
                        width: 10px;
                        margin: 0px;
                    }
                    QScrollBar::handle:vertical {
                        background: #444444;
                        min-height: 20px;
                        border-radius: 5px;
                    }
                    QScrollBar::handle:vertical:hover {
                        background: #666666;
                        
                    }
                    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                        border: none;
                        background: none;
                        height: 0px;
                        width: 0px;
                        image: none;
                    }
                    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                        background: none;
                    }
                """)
        self.InfoScroll.horizontalScrollBar().setStyleSheet("""
            QScrollBar:horizontal {
                border: none;
                background: rgb(30, 30, 30);
                height: 10px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #444444;
                min-width: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #666666;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
                height: 0px;
                width: 0px;
                image: none;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)
        self.InfoScroll.setWidgetResizable(True)
        self.Info = pyside.QWidget()
        self.Info.setStyleSheet("background-color: transparent;")
        self.InfoLayout = pyside.QVBoxLayout(self.Info)
        self.InfoScroll.setWidget(self.Info)
        self.InfoPageLayout.addWidget(self.InfoScroll)
        #
        self.InfoText = pyside.QLabel("• This project is heavily inspired and coppied by Discord. (A very simple version of it)\n\n" \
                                    "• The idea and making of this project was to challenge myself and put everything i have learned into 1 big and ''impresive'' desktop application \n\n" \
                                    "• It is not meant to be taken seriously and its only for showcasing \n\n" \
                                    "• The project includes: GUIs,Database,APIs,Keyring,Hashing,Asyncronous Code,WebSockets,Cryptography")
        self.InfoText.setWordWrap(True)
        self.InfoText.setStyleSheet("color: rgb(200,200,200); font-size: 15px; margin: 10px;")
        self.InfoLayout.addWidget(self.InfoText)
        #
        self.Float = pyside.QSpacerItem(20,20,pyside.QSizePolicy.Policy.Maximum,pyside.QSizePolicy.Policy.Expanding)
        self.InfoLayout.addItem(self.Float)
        #Online Friends Page
        self.OnlinePage = pyside.QWidget()
        self.OnlinePageLayout = pyside.QGridLayout(self.OnlinePage)
        self.OnlinePageLayout.setSpacing(0)
        self.OnlinePageLayout.setContentsMargins(0,0,0,0)
        self.OnlinePage.setStyleSheet("background-color: rgb(30,30,30);")
        #
        self.OnlineScroll = pyside.QScrollArea()
        self.OnlineScroll.setStyleSheet("background-color: transparent; border: none;")
        self.OnlineScroll.verticalScrollBar().setStyleSheet("""
            QScrollBar:vertical {
                border: none;
                background: rgb(30, 30, 30);
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #444444;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #666666;
                
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
                width: 0px;
                image: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        self.OnlineScroll.horizontalScrollBar().setStyleSheet("""
            QScrollBar:horizontal {
                border: none;
                background: rgb(30, 30, 30);
                height: 10px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #444444;
                min-width: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #666666;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
                height: 0px;
                width: 0px;
                image: none;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)
        self.OnlineScroll.setWidgetResizable(True)
        self.Online = pyside.QWidget()
        self.Online.setStyleSheet("background-color: transparent;")
        self.OnlineLayout = pyside.QVBoxLayout(self.Online)
        self.OnlineScroll.setWidget(self.Online)
        self.OnlinePageLayout.addWidget(self.OnlineScroll)
        #
        # Online people
        self.OnlineLbl = pyside.QLabel(" • Online - 0")
        self.OnlineLbl.setStyleSheet("background-color: transparent; color: rgb(190,190,190); font-size: 17px; border: none; padding: 4px;")
        self.OnlineLayout.addWidget(self.OnlineLbl)
        #
        self.OnlineCon = pyside.QWidget()
        self.OnlineConLayout = pyside.QVBoxLayout(self.OnlineCon)
        self.OnlineConLayout.setContentsMargins(0,0,0,0)
        self.OnlineConLayout.setSpacing(0)
        self.OnlineCon.setStyleSheet("background-color: transparent;")
        self.OnlineLayout.addWidget(self.OnlineCon)
        #icon
        self.NoFriends = pyside.QLabel("")
        self.NoFriends.setStyleSheet("background-color: transparent;")
        self.NoFriends.setFixedSize(QSize(450,350))
        self.NoFriends.setScaledContents(True)
        self.NoFriendsPix = QPixmap(self.IconFolder + "NoFriendsOnline.png")
        self.NoFriends.setPixmap(self.NoFriendsPix)
        self.OnlineLayout.addWidget(self.NoFriends,alignment=Qt.AlignmentFlag.AlignCenter)
        #
        self.Squize = pyside.QSpacerItem(20,20,pyside.QSizePolicy.Policy.Maximum,pyside.QSizePolicy.Policy.Expanding)
        self.OnlineLayout.addItem(self.Squize)
        #---------------------------------------------------------
        #All Friends Page
        self.AllPage = pyside.QWidget()
        self.AllPageLayout = pyside.QGridLayout(self.AllPage)
        self.AllPageLayout.setSpacing(0)
        self.AllPageLayout.setContentsMargins(0,0,0,0)
        self.AllPage.setStyleSheet("background-color: rgb(30,30,30);")
        #
        self.AllScroll = pyside.QScrollArea()
        self.AllScroll.setStyleSheet("background-color: transparent; border: none;")
        self.AllScroll.verticalScrollBar().setStyleSheet("""
            QScrollBar:vertical {
                border: none;
                background: rgb(30, 30, 30);
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #444444;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #666666;
                
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
                width: 0px;
                image: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        self.AllScroll.horizontalScrollBar().setStyleSheet("""
            QScrollBar:horizontal {
                border: none;
                background: rgb(30, 30, 30);
                height: 10px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #444444;
                min-width: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #666666;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
                height: 0px;
                width: 0px;
                image: none;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)
        self.AllScroll.setWidgetResizable(True)
        self.All = pyside.QWidget()
        self.All.setStyleSheet("background-color: transparent;")
        self.AllLayout = pyside.QVBoxLayout(self.All)
        self.AllScroll.setWidget(self.All)
        self.AllPageLayout.addWidget(self.AllScroll)
        #
        self.FriendLbl = pyside.QLabel(" • Friends - 0")
        self.FriendLbl.setStyleSheet("background-color: transparent; color: rgb(190,190,190); font-size: 17px; border: none; padding: 4px;")
        self.AllLayout.addWidget(self.FriendLbl)
        #icon
        self.ZeroFriends = pyside.QLabel("")
        self.ZeroFriends.setStyleSheet("background-color: transparent;")
        self.ZeroFriends.setFixedSize(QSize(450,350))
        self.ZeroFriends.setScaledContents(True)
        self.ZeroFriendsPix = QPixmap(self.IconFolder + "NoFriends.png")
        self.ZeroFriends.setPixmap(self.ZeroFriendsPix)
        self.AllLayout.addWidget(self.ZeroFriends,alignment=Qt.AlignmentFlag.AlignCenter)
        #
        self.Press = pyside.QSpacerItem(20,20,pyside.QSizePolicy.Policy.Maximum,pyside.QSizePolicy.Policy.Expanding)
        self.AllLayout.addItem(self.Press)
        #Pending Page
        self.PendingPage = pyside.QWidget()
        self.PendingPageLayout = pyside.QVBoxLayout(self.PendingPage)
        self.PendingPageLayout.setSpacing(0)
        self.PendingPageLayout.setContentsMargins(0,0,0,0)
        self.PendingPage.setStyleSheet("background-color: rgb(30,30,30);")
        # friend requests
        self.FriendReqLbl = pyside.QLabel(" • Friend Requests Received - 0")
        self.FriendReqLbl.setStyleSheet("background-color: transparent; color: rgb(190,190,190); font-size: 17px; border: none; padding: 4px;")
        self.PendingPageLayout.addWidget(self.FriendReqLbl)
        self.FriendReqLbl.hide()
        #
        self.FriendReqCon = pyside.QWidget()
        self.FriendReqLayout = pyside.QVBoxLayout(self.FriendReqCon)
        self.FriendReqCon.setStyleSheet("background-color: rgb(30,30,30);")
        self.PendingPageLayout.addWidget(self.FriendReqCon)
        self.FriendReqCon.hide()
        #--------------------------------------------------------
        #chat area stuff
        #pages container
        self.MainTabWidget = pyside.QTabWidget()
        self.MainTabWidget.setDocumentMode(True)
        self.MainTabWidget.setStyleSheet("border-none;")
        self.MainTabWidget.tabBar().hide()
        self.ChatAreaLayout.addWidget(self.MainTabWidget,0,0)
        #container holding the chat and the send part
        self.MainChat = pyside.QWidget()
        self.MainChat.setStyleSheet("background-color: rgb(30,30,30); border-bottom: 1px solid rgb(100,100,100);")
        self.MainChatLayout = pyside.QGridLayout(self.MainChat)
        self.MainChatLayout.setSpacing(0)
        self.MainChatLayout.setContentsMargins(0,0,0,0)
        self.MainChatLayout.setRowStretch(0,1)
        self.MainChatLayout.setRowStretch(1,0)
        # chat part
        self.Space = pyside.QSpacerItem(20,20,pyside.QSizePolicy.Policy.Expanding,pyside.QSizePolicy.Policy.Expanding)
        self.ChatPanel = pyside.QWidget()
        #self.ChatPanel.setStyleSheet("background-color: red;")
        self.ChatPanel.setStyleSheet("background-color: rgb(30,30,30);")
        self.ChatPanel.setSizePolicy(pyside.QSizePolicy.Policy.Preferred,pyside.QSizePolicy.Policy.Maximum)
        self.ChatPanelLayout = pyside.QVBoxLayout(self.ChatPanel)
        self.ChatPanelLayout.setSpacing(0)
        self.ChatPanelLayout.setContentsMargins(0,0,0,0)
        self.ScrollBar = pyside.QScrollArea()
        self.ScrollBar.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.Vscroll = self.ScrollBar.verticalScrollBar()
        self.Vscroll.valueChanged.connect(lambda:self.LoadExtraMessages(self.Vscroll.value()))
        self.Vscroll.rangeChanged.connect(lambda min_val, max_val: self.Vscroll.setValue(max_val))
        self.ScrollBar.setFrameShape(pyside.QFrame.Shape.NoFrame)
        self.ScrollBar.verticalScrollBar().setStyleSheet("""
            QScrollBar:vertical {
                border: none;
                background: rgb(30, 30, 30);
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #444444;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #666666;
                
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
                width: 0px;
                image: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        self.ScrollBar.horizontalScrollBar().setStyleSheet("""
            QScrollBar:horizontal {
                border: none;
                background: rgb(30, 30, 30);
                height: 10px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #444444;
                min-width: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #666666;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
                height: 0px;
                width: 0px;
                image: none;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)
        self.ScrollBar.setWidgetResizable(True)
        self.ScrollBar.setStyleSheet("background-color: rgb(30,30,30); border: none;")
        self.ScrollBar.setWidget(self.ChatPanel)
        self.MainChatLayout.addWidget(self.ScrollBar,0,0)
        self.ChatPanelLayout.addItem(self.Space)
        # send part
        self.TextHolder = pyside.QWidget()
        self.TextHolder.setStyleSheet("background-color: rgb(60,60,60); margin: 10px; border-radius: 8px; border: none;")
        self.TextHolder.setMinimumHeight(70)
        self.TextHolderLayout = pyside.QHBoxLayout(self.TextHolder)
        self.TextHolderLayout.setSpacing(0)
        self.TextHolderLayout.setContentsMargins(0,0,0,0)
        self.MainChatLayout.addWidget(self.TextHolder,1,0)
        #
        self.TypingBar = TypeInput()
        self.TypingBar.setPlaceholderText("Type A Message...")
        self.TypingBar.setMinimumHeight(52)
        self.TypingBar.setMaximumHeight(55)
        self.TypingBar.EnterSignal.connect(lambda:self.Send(self.TypingBar.toPlainText()))
        self.TextHolderLayout.addWidget(self.TypingBar)
        #
        self.SendBtn = pyside.QPushButton("  ↵  ")
        self.SendBtn.setMinimumHeight(50)
        self.SendBtn.setStyleSheet("""QPushButton{background-color: rgb(60,60,60); font-size: 30px; border-radius: 9px; margin-left: 2px; margin-right: 30px; color: rgb(150,150,150); border: none;}
                                    QPushButton:hover{background-color: rgb(80,80,80);}""")
        self.SendBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.SendBtn.clicked.connect(lambda:self.Send(self.TypingBar.toPlainText()))
        self.TextHolderLayout.addWidget(self.SendBtn)
        #add the pages
        self.MainTabWidget.addTab(self.MainChat,"Chatting Page")
        self.MainTabWidget.addTab(self.OnlinePage,"Online Page")
        self.MainTabWidget.addTab(self.AllPage,"All Page")
        self.MainTabWidget.addTab(self.PendingPage,"Pending Page")
        self.MainTabWidget.addTab(self.AddArea,"Add Friend Page")
        self.MainTabWidget.addTab(self.InfoPage,"Info Page")
        self.MainTabWidget.setCurrentWidget(self.OnlinePage)
        #--------------------------------------------------------
        #side area stuff
        #friends btn
        self.FriendPix = QIcon(self.IconFolder + "Friends.png")
        self.FriendsBtn = pyside.QPushButton(" Friends  ")
        self.FriendsBtn.setIcon(self.FriendPix)
        self.FriendsBtn.setIconSize(QSize(20,30))
        self.FriendsBtn.setCheckable(True)
        self.FriendsBtn.setStyleSheet("""QPushButton{background-color: rgb(20,20,20); color: rgb(200,200,200); font-size: 20px; border-radius: 6px; padding: 4px; margin: 10px; margin-bottom: 0px; border: none;}
                                        QPushButton:hover{background-color: rgb(40,40,40);}
                                        QPushButton:checked{background-color: rgb(70,70,70);}""")
        self.FriendsBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.NotifCircle = CircleIcon(self.FriendsBtn)
        self.NotifCircle.ChangeColor((250,70,70))
        self.NotifCircle.move(160,23)
        self.NotifCircle.setFixedSize(QSize(15,15))
        self.NotifCircle.raise_()
        self.NotifCircle.hide()
        self.FriendsBtn.clicked.connect(lambda:self.toOnilneFriends())
        self.SideLayout.addWidget(self.FriendsBtn,0,0)
        #Info btn
        self.InfoPix = QIcon(self.IconFolder + "Info.png")
        self.InfoBtn = pyside.QPushButton(" Info  ")
        self.InfoBtn.setIcon(self.InfoPix)
        self.InfoBtn.setIconSize(QSize(23,23))
        self.InfoBtn.setCheckable(True)
        self.InfoBtn.setStyleSheet("""QPushButton{background-color: rgb(20,20,20); color: rgb(200,200,200); font-size: 20px; border-radius: 6px; padding: 4px; margin: 10px; border: none;}
                                        QPushButton:hover{background-color: rgb(40,40,40);}
                                        QPushButton:checked{background-color: rgb(70,70,70);}""")
        self.InfoBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.InfoBtn.clicked.connect(lambda:self.toInfoPage())
        self.SideLayout.addWidget(self.InfoBtn,1,0)
        #messages label
        self.FriendsLabel = pyside.QLabel(" Friend Messages")
        self.FriendsLabel.setStyleSheet("background-color: transparent; color: rgb(100,100,100); font-size: 15px; border: none; border-top: 1px solid rgb(100,100,100); padding: 4px; margin: 10px; margin-top: 0px;")
        self.SideLayout.addWidget(self.FriendsLabel,2,0)
        #saved friends
        self.FriendsWidget = pyside.QWidget()
        self.FriendsWidget.setStyleSheet("background-color: transparent;")
        self.FriendsLayout = pyside.QVBoxLayout(self.FriendsWidget)
        #
        self.FriendsScroll = pyside.QScrollArea()
        self.FriendsScroll.setStyleSheet("background-color: transparent; border: none;")
        self.FriendsScroll.verticalScrollBar().setStyleSheet("""
            QScrollBar:vertical {
                border: none;
                background: rgb(30, 30, 30);
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #444444;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #666666;
                
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
                width: 0px;
                image: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        self.FriendsScroll.horizontalScrollBar().setStyleSheet("""
            QScrollBar:horizontal {
                border: none;
                background: rgb(30, 30, 30);
                height: 10px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #444444;
                min-width: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #666666;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
                height: 0px;
                width: 0px;
                image: none;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)
        self.FriendsScroll.setWidgetResizable(True)
        self.FriendsScroll.setWidget(self.FriendsWidget)
        self.SideLayout.addWidget(self.FriendsScroll,3,0)
        #room maker
        self.RoomMaker = pyside.QSpacerItem(20,20,pyside.QSizePolicy.Policy.Maximum,pyside.QSizePolicy.Policy.Expanding)

        #profile view
        self.ViewWidget = pyside.QWidget()
        self.ViewWidget.setFixedHeight(60)
        self.ViewWidget.setStyleSheet("background-color: rgb(20,20,20); border-bottom: 1px solid rgb(100,100,100); border-left: 1px solid rgb(100,100,100);")
        self.ViewWidgetLayout = pyside.QGridLayout(self.ViewWidget)
        self.ViewWidgetLayout.setSpacing(0)
        self.ViewWidgetLayout.setContentsMargins(2,2,2,2)
        self.InterfaceLayout.addWidget(self.ViewWidget,2,0)
        #
        self.ProfileView = SelfProfile("name",self.IconFolder + "Default.png",self.IconFolder + "Gear.png")
        self.ViewWidgetLayout.addWidget(self.ProfileView)
        #Button Group
        self.SideGroup = pyside.QButtonGroup()
        self.SideGroup.addButton(self.FriendsBtn)
        self.SideGroup.addButton(self.InfoBtn)
        #self.SideGroup.addButton(self.Test.RaisedBtn)
        #--------------------------------------------------------
        #HUpper stuff
        #add friends button
        self.AddFriendsBtn = pyside.QPushButton("Add Friends")
        self.AddFriendsBtn.setCheckable(True)
        self.AddFriendsBtn.setStyleSheet("""QPushButton{background-color: rgb(40,40,170); color: rgb(200,200,200); font-size: 23px; border-radius: 6px; padding: 2px; margin: 5px; border: none;}
                                        QPushButton:hover{background-color: rgb(40,40,120); color: rgb(200,200,200);}
                                        QPushButton:checked{background-color: rgb(40,40,120); color: rgb(100,100,200);}""")
        self.AddFriendsBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.AddFriendsBtn.clicked.connect(lambda:self.toAddFriends())
        self.HUpperLayout.addWidget(self.AddFriendsBtn,0,0)
        self.SideGroup.addButton(self.AddFriendsBtn)

        #--------------------------------------------------------
        #Upper stuff
        #User bar
        self.UserBar = pyside.QWidget()
        self.UserBar.setStyleSheet("background-color: rgb(30,30,30); border: none; border-right: 1px solid rgb(100,100,100); border-bottom: 1px solid rgb(100,100,100);")
        self.UserBarLayout = pyside.QHBoxLayout(self.UserBar)
        #
        self.BarIcon = CircularImage(Path= self.IconFolder + "Default.png",size=30)
        self.UserBarLayout.addWidget(self.BarIcon)
        #
        self.BarName = pyside.QLabel(" ")
        self.BarName.setStyleSheet("background-color: transparent; font-size: 17px; color: rgb(200,200,200); border: none; font-weight: 600;")
        self.UserBarLayout.addWidget(self.BarName)
        #
        self.Spaaaaa = pyside.QSpacerItem(20,20,pyside.QSizePolicy.Policy.Expanding,pyside.QSizePolicy.Policy.Maximum)
        self.UserBarLayout.addItem(self.Spaaaaa)
        #
        self.HideUSIB = pyside.QPushButton("")
        self.USIBIcon = QIcon(self.IconFolder + "SideWhite.png")
        self.USIBIcon2 = QIcon(self.IconFolder + "SideGray.png")
        self.HideUSIB.setToolTip("Hide User Bar")
        self.HideUSIB.setIcon(self.USIBIcon)
        self.HideUSIB.setIconSize(QSize(35,35))
        self.HideUSIB.setSizePolicy(pyside.QSizePolicy.Policy.Maximum,pyside.QSizePolicy.Policy.Maximum)
        self.HideUSIB.setCursor(Qt.CursorShape.PointingHandCursor)
        self.HideUSIB.setMinimumSize(QSize(30,30))
        self.HideUSIB.setStyleSheet("""QPushButton{background-color: transparent; font-size: 30px; border-radius: 10px; border: none; color: white; margin-right: 10px;}
                                        QPushButton:hover{background-color: rgb(40,40,40);}
                                        QToolTip{background-color: white;}""")
        self.HideUSIB.setCursor(Qt.CursorShape.PointingHandCursor)
        self.HideUSIB.clicked.connect(lambda:self.CloseUSIB())
        self.UserBarLayout.addWidget(self.HideUSIB)
        #Normal bar
        self.NormalBar = pyside.QWidget()
        self.NormalBar.setStyleSheet("background-color: rgb(30,30,30); border: none; border-right: 1px solid rgb(100,100,100); border-bottom: 1px solid rgb(100,100,100);")
        self.NormalBarLayout = pyside.QGridLayout(self.NormalBar)
        #
        self.InfoBar = pyside.QWidget()
        self.InfoBar.setStyleSheet("background-color: rgb(30,30,30); border: none; border-right: 1px solid rgb(100,100,100); border-bottom: 1px solid rgb(100,100,100);")
        self.InfoBarLayout = pyside.QGridLayout(self.InfoBar)
        #
        self.InfoLabel = pyside.QLabel("• Information about the project")
        self.InfoLabel.setStyleSheet("color: rgb(200,200,200); font-size: 20px; border: none; margin-left: 7px; font-weight: 600;")
        self.InfoBarLayout.addWidget(self.InfoLabel)
        #Upper tab widget
        self.UpperTab = pyside.QTabWidget()
        self.UpperTab.tabBar().hide()
        self.UpperTab.setStyleSheet("border: none;")
        self.UpperTab.setDocumentMode(True)
        self.UpperLayout.addWidget(self.UpperTab,0,0)
        self.UpperTab.addTab(self.NormalBar,"Normal Bar")
        self.UpperTab.addTab(self.InfoBar,"Info Bar")
        self.UpperTab.addTab(self.UserBar,"User Bar")
        #Upper Btn Group
        self.UpperGroup = pyside.QButtonGroup()
        #Friends label
        self.FriendsUpper = pyside.QPushButton(" Friends  •")
        self.FriendsUpper.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.FriendsUpper.setIcon(self.FriendPix)
        self.FriendsUpper.setIconSize(QSize(20,30))
        self.FriendsUpper.setStyleSheet("background-color: transparent; color: rgb(200,200,200); font-size: 20px; border: none; padding: 2px; margin: 5px; font-weight: 600;")
        self.NormalBarLayout.addWidget(self.FriendsUpper,0,0)
        #online friends btn
        self.OnlineBtn = pyside.QPushButton(" Online ")
        self.OnlineBtn.setCheckable(True)
        self.OnlineBtn.setStyleSheet("""QPushButton{background-color: transparent; color: rgb(200,200,200); font-size: 20px; border-radius: 6px; padding: 2px; margin: 5px; border: none;}
                                        QPushButton:hover{background-color: rgb(45,45,45);}
                                        QPushButton:checked{background-color: rgb(60,60,60);}""")
        self.OnlineBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.OnlineBtn.clicked.connect(lambda:self.toOnilneFriends())
        self.NormalBarLayout.addWidget(self.OnlineBtn,0,1)
        #all friends btn
        self.AllBtn = pyside.QPushButton(" All Friends ")
        self.AllBtn.setCheckable(True)
        self.AllBtn.setStyleSheet("""QPushButton{background-color: transparent; color: rgb(200,200,200); font-size: 20px; border-radius: 6px; padding: 2px; margin: 5px; border: none;}
                                        QPushButton:hover{background-color: rgb(45,45,45);}
                                        QPushButton:checked{background-color: rgb(60,60,60);}""")
        self.AllBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.AllBtn.clicked.connect(lambda:self.toAllFriends())
        self.NormalBarLayout.addWidget(self.AllBtn,0,2)
        #pending requests btn
        self.PendingBtn = pyside.QPushButton(" Pending Requests ")
        self.PendingBtn.setCheckable(True)
        self.PendingBtn.setStyleSheet("""QPushButton{background-color: transparent; color: rgb(200,200,200); font-size: 20px; border-radius: 6px; padding: 2px; margin: 5px; border: none;}
                                        QPushButton:hover{background-color: rgb(45,45,45);}
                                        QPushButton:checked{background-color: rgb(60,60,60);}""")
        self.PendingBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        #self.PendingBtn.setText(" Pending Requests      ")
        self.NotifCircle2 = CircleIcon(self.PendingBtn)
        self.NotifCircle2.ChangeColor((250,70,70))
        self.NotifCircle2.move(178,13)
        self.NotifCircle2.setFixedSize(QSize(15,15))
        self.NotifCircle2.raise_()
        self.NotifCircle2.hide()
        self.PendingBtn.clicked.connect(lambda:self.toPending())
        self.NormalBarLayout.addWidget(self.PendingBtn,0,3)
        self.Printbtn = pyside.QPushButton("Print")
        self.Printbtn.setStyleSheet("""QPushButton{background-color: transparent; color: rgb(200,200,200); font-size: 20px; border-radius: 6px; padding: 2px; margin: 5px; border: none;}
                                        QPushButton:hover{background-color: rgb(45,45,45);}
                                        QPushButton:checked{background-color: rgb(60,60,60);}""")
        self.Printbtn.clicked.connect(lambda:self.ShowAllInfo())
        #self.NormalBarLayout.addWidget(self.Printbtn,0,4)
        #
        self.UpperSpacer = pyside.QSpacerItem(20,20,pyside.QSizePolicy.Policy.Expanding,pyside.QSizePolicy.Policy.Maximum)
        self.NormalBarLayout.addItem(self.UpperSpacer,0,5)
        #add the buttons
        #self.UpperGroup.addButton(self.AddFriendsBtn)
        self.UpperGroup.addButton(self.OnlineBtn)
        self.UpperGroup.addButton(self.AllBtn)
        self.UpperGroup.addButton(self.PendingBtn)
        #--------------------------------------------------------
        #Add Friends Page
        #Label
        self.AddLabel = pyside.QLabel("Add Friends")
        self.AddLabel.setStyleSheet("background-color: transparent; font-size: 30px; color: rgb(200,200,200); padding: 3px; border-radius: 6px; margin: 10px; margin-bottom: 0px;")
        self.AddAreaLayout.addWidget(self.AddLabel,0,0)
        #Label2
        self.AddLabel2 = pyside.QLabel(" Add friends using their username to chat with them")
        self.AddLabel2.setStyleSheet("background-color: transparent; font-size: 20px; color: rgb(200,200,200); padding: 3px; border-radius: 6px; margin: 10px; margin-bottom: 0px; margin-top: 0px;")
        self.AddAreaLayout.addWidget(self.AddLabel2,1,0)
        #Search bar
        self.AddSearch = pyside.QLineEdit()
        self.AddSearch.setPlaceholderText("Enter username...")
        self.AddSearch.setStyleSheet("""QLineEdit{background-color: rgb(20,20,20); font-size: 20px; color: rgb(200,200,200); padding: 7px; border-radius: 6px; margin: 10px; border: none;}
                                        QLineEdit:focus{border: 1px solid rgb(50,50,150);}""")
        self.AddAreaLayout.addWidget(self.AddSearch,2,0)
        #Search button
        self.SearchFriendBtn = pyside.QPushButton(" Send Request ")
        self.SearchFriendBtn.setStyleSheet("""QPushButton{background-color: rgb(30,30,150); font-size: 23px; color: rgb(200,200,200); padding: 4px; border-radius: 6px; margin: 10px;}
                                            QPushButton:hover{background-color: rgb(30,30,100);}""")
        self.SearchFriendBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.SearchFriendBtn.clicked.connect(lambda:asyncio.create_task(self.SendFriendRequest()))
        self.AddAreaLayout.addWidget(self.SearchFriendBtn,2,1)
        #Error label
        self.FriendError = pyside.QLabel("Enter a valid username")
        self.FriendError.setStyleSheet("background-color: transparent; font-size: 15px; color: rgb(255,100,100); padding: 3px; border-radius: 6px; margin: 10px; margin-top: 0px;")
        self.AddAreaLayout.addWidget(self.FriendError,3,0)
        self.FriendError.hide()
        #spacer
        self.FriendSpacer = pyside.QSpacerItem(20,20,pyside.QSizePolicy.Policy.Maximum,pyside.QSizePolicy.Policy.Expanding)
        self.AddAreaLayout.addItem(self.FriendSpacer,4,0)
        #------------------------------------------------------------------
        #Pending Page
        self.PendingLbl = pyside.QLabel(f" • Pending Requests Sent - ")
        self.PendingLbl.setStyleSheet("background-color: transparent; color: rgb(190,190,190); font-size: 17px; border: none; padding: 4px; margin-top:10px; margin-bottom: 10px;")
        self.PendingPageLayout.addWidget(self.PendingLbl)
        #
        self.Force = pyside.QSpacerItem(20,20,pyside.QSizePolicy.Policy.Maximum,pyside.QSizePolicy.Policy.Expanding)
        self.PendingPageLayout.addItem(self.Force)
        #-------------------------------------------------------------------
        #Details area for profile and stuff
        #blank area
        self.BlankWidget = pyside.QWidget()
        self.BlankWidget.setStyleSheet("background-color: rgb(30,30,30); border: 1px solid rgb(100,100,100); border-top: none;")
        #Actuall profile widget
        self.SideProfile = pyside.QWidget()
        self.SideProfile.setStyleSheet("background-color: rgb(40,40,40); border: 1px solid rgb(100,100,100); border-radius: 10px;")
        self.SideProfileLayout = pyside.QGridLayout(self.SideProfile)
        self.SideProfileLayout.setContentsMargins(3,3,3,3)
        # banner
        self.Banner = pyside.QWidget()
        self.BannerL = pyside.QHBoxLayout(self.Banner)
        self.Banner.setFixedHeight(110)
        self.Banner.setSizePolicy(pyside.QSizePolicy.Policy.Expanding,pyside.QSizePolicy.Policy.Maximum)
        self.Banner.setStyleSheet("background-color: rgb(100,150,70); border:none; border-radius: 0px; border-top-left-radius: 10px; border-top-right-radius: 10px;")
        self.SideProfileLayout.addWidget(self.Banner,0,0)
        # bunner buttons
        self.Spacer = pyside.QSpacerItem(20,20,pyside.QSizePolicy.Policy.Expanding,pyside.QSizePolicy.Policy.Maximum)
        self.BannerL.addItem(self.Spacer)
        #
        self.FriendBtn = pyside.QPushButton("")
        self.FriendPix2 = QIcon(self.IconFolder + "Friend.png")
        self.FriendPix3 = QIcon(self.IconFolder + "Add.png")
        self.FriendPix4 = QIcon(self.IconFolder + "Pending.png")
        self.FriendBtn.setIcon(self.FriendPix2)
        self.FriendBtn.setIconSize(QSize(20,20))
        self.FriendBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.FriendBtn.setFixedSize(QSize(34,34))
        self.FriendBtn.setStyleSheet("""QPushButton{background-color: rgba(50,50,50,0.8); border-none; border-radius: 15px; font-size: 20px; font-weight: 600; color: rgb(200,200,200);}
                                        QPushButton:hover{background-color: rgba(20,20,20,0.9);}""")
        self.FriendBtn.clicked.connect(lambda:asyncio.create_task(self.TriggerUnfriend()))
        self.BannerL.addWidget(self.FriendBtn,alignment=Qt.AlignmentFlag.AlignTop)
        #
        self.MoreBtn = pyside.QPushButton("···")
        self.MoreBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.MoreBtn.setFixedSize(QSize(34,34))
        self.MoreBtn.setStyleSheet("""QPushButton{background-color: rgba(50,50,50,0.8); border-none; border-radius: 15px; font-size: 20px; font-weight: 600; color: rgb(200,200,200);}
                                        QPushButton:hover{background-color: rgba(20,20,20,0.9);}""")
        self.BannerL.addWidget(self.MoreBtn,alignment=Qt.AlignmentFlag.AlignTop)
        #
        self.IconBackground = CircleIcon(self.SideProfile)
        self.IconBackground.move(15,55)
        self.IconBackground.ChangeColor((40,40,40))
        self.IconBackground.setFixedSize(QSize(94,94))
        self.IconBackground.raise_()
        #
        self.UserIcon = CircularImage(parent=self.SideProfile,Path= self.IconFolder + "Default.png")
        self.UserIcon.move(22,62)
        self.UserIcon.raise_()
        #
        self.ProfileLabel = pyside.QLabel("User")
        self.ProfileLabel.setStyleSheet("color: rgb(200,200,200); font-size: 25px; margin: 10px; margin-top: 30px; border: none; font-weight: 600;")
        self.SideProfileLayout.addWidget(self.ProfileLabel,1,0)
        #
        self.BioLbl = pyside.QLabel("Bio")
        self.BioLbl.setStyleSheet("color: rgb(200,200,200); font-size: 15px; margin: 10px; margin-top: 5px; margin-bottom: 1px; border: none; font-weight: 700;")
        self.SideProfileLayout.addWidget(self.BioLbl,2,0)
        #
        #self.BioTxt = pyside.QLabel("a very cool bio")
        self.BioTxt = FastWrapLabel("a very cool bio",FontSize= 14)
        self.BioTxt.setFixedWidth(270)
        self.SideProfileLayout.addWidget(self.BioTxt,3,0,alignment=Qt.AlignmentFlag.AlignHCenter)
        #
        self.MemberLabel = pyside.QLabel("Member Since")
        self.MemberLabel.setStyleSheet("color: rgb(200,200,200); font-size: 14px; margin: 10px; margin-top: 2px; margin-bottom: 2px; border: none; font-weight: 700;")
        self.SideProfileLayout.addWidget(self.MemberLabel,4,0)
        #
        self.JoinedLabel = pyside.QLabel("??/??/????")
        self.JoinedLabel.setStyleSheet("color: rgb(200,200,200); font-size: 12px; margin: 10px; margin-top: 0px; border: none; font-weight: 600;")
        self.SideProfileLayout.addWidget(self.JoinedLabel,5,0)
        #elevator
        self.elevator = pyside.QSpacerItem(20,20,pyside.QSizePolicy.Policy.Maximum,pyside.QSizePolicy.Policy.Expanding)
        self.SideProfileLayout.addItem(self.elevator,6,0)
        #tab widget
        self.DetailsTab = pyside.QTabWidget()
        self.DetailsTab.tabBar().hide()
        self.DetailsTab.setStyleSheet("border: none; margin-bottom: 3px; margin-right: 3px;")
        self.DetailsTab.setDocumentMode(True)
        self.DetailsAreaLayout.addWidget(self.DetailsTab,0,0)
        self.DetailsTab.addTab(self.BlankWidget,"Blank")
        self.DetailsTab.addTab(self.SideProfile,"Profile")
        #-------------------------------------------------------------------
        #Registration and main interface
        self.Pages.addTab(self.LogInTab,"Log In-Sign Up")
        self.Pages.addTab(self.Interface,"Main Page")
        self.Pages.addTab(self.ConnectingPage,"Connecting Page")
        self.Pages.addTab(self.LoadingPage,"Loading Page")
        #Add LogIn and SignUp pages
        self.AuthPage.addTab(self.LogInPage,"Log In")
        self.AuthPage.addTab(self.SignUpPage,"Sign Up")
        #self.AuthPage.addTab(self.ConnectingPage,"Connecting Page")
        #

    #convert - decrypt -encrypt
    def ReadableTime(self,time):
        Time = datetime.fromisoformat(time).astimezone()
        date = Time.date()
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        Day = Time.strftime("%d %b %Y") + Time.strftime("%H:%M")
        if date == today:
            Time = Time.strftime("%H:%M")
        elif date == yesterday:
            Time = "Yesterday at " + Time.strftime("%H:%M")
        else:
            Time = Time.strftime("%d %b %Y") + " at " + Time.strftime("%H:%M")
        return Time,Day

    def EncryptMessage(self,message):
        if self.RandomKeyCounter < 15 and self.CurrentRKey is not None:
            self.RandomKeyCounter += 1
            ThrowKey = self.CurrentRKey
        else:
            self.RandomKeyCounter = 0
            self.CurrentRKey = Fernet.generate_key()
            ThrowKey = self.CurrentRKey

        Message = message.encode("utf-8")
        EncryptedMessage = Fernet(ThrowKey).encrypt(Message)
        EncryptedSenderKey = self.User["PublicKey"].encrypt(
                            ThrowKey,
                            padding.OAEP(
                                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                algorithm=hashes.SHA256(),
                                label=None
                                )
                            )
        for x in self.Friends:
            if x.get("Id") == self.CurrentId:
                EncryptedRecipientKey = x.get("PublicKey").encrypt(
                                    ThrowKey,
                                    padding.OAEP(
                                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                        algorithm=hashes.SHA256(),
                                        label=None
                                        )
                                    )
                break
        return(jsonable_encoder(EncryptedMessage),base64.b64encode(EncryptedSenderKey).decode("utf-8"),base64.b64encode(EncryptedRecipientKey).decode("utf-8"))


    def DecryptMessage(self,message,key):
        try:
            DecryptedMessage = Fernet(self.CurrentRKey).decrypt(message.encode('utf-8')).decode("utf-8")
            return DecryptedMessage
        except:
            try:
                DecryptedMessage = Fernet(self.FriendRKey).decrypt(message.encode('utf-8')).decode("utf-8")
                return DecryptedMessage
            except:
                KeyUsed = base64.b64decode(key.encode("utf-8"))
                PrivKey = load_pem_private_key(self.User["Key"].encode('utf-8'), password=None)
                EncryptionKey = PrivKey.decrypt(
                                KeyUsed,
                                padding.OAEP(
                                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                    algorithm=hashes.SHA256(),
                                    label=None
                                    )
                                )
                self.FriendRKey = EncryptionKey
                DecryptedMessage = Fernet(EncryptionKey).decrypt(message.encode('utf-8')).decode("utf-8")
                return DecryptedMessage

    # to pages --------------------------------------
    def toConnectingPage(self):
        self.Pages.setCurrentWidget(self.ConnectingPage)

    def toLoadingPage(self):
        self.Pages.setCurrentWidget(self.LoadingPage)

    def toSignPage(self):
        self.AuthPage.setCurrentWidget(self.SignUpPage)
        self.ErrorReport2.hide()
    
    def toLogPage(self):
        self.AuthPage.setCurrentWidget(self.LogInPage)
        self.ErrorReport.hide()

    def toMainTab(self):
        self.Pages.setCurrentWidget(self.Interface)

    def toLogTab(self):
        self.Pages.setCurrentWidget(self.LogInTab)

    def toAddFriends(self):
        self.DetailsArea.show()
        self.toBlank()
        self.toNormalBar()
        self.MainTabWidget.setCurrentWidget(self.AddArea)

    def toInfoPage(self):
        self.DetailsArea.hide()
        self.MainTabWidget.setCurrentWidget(self.InfoPage)
        self.toBlank()
        self.toInfoBar()

    def toOnilneFriends(self):
        self.DetailsArea.show()
        self.OnlineBtn.setChecked(True)
        self.OnlineBtn.setText(" Online ")
        asyncio.create_task(self.RetrieveStatus())
        self.MakeOnline()
        self.MainTabWidget.setCurrentWidget(self.OnlinePage)
        self.toBlank()
        self.toNormalBar()

    def toAllFriends(self):
        self.MainTabWidget.setCurrentWidget(self.AllPage)
        asyncio.create_task(self.RetrieveStatus())

    def toPending(self):
        self.PendingBtn.setText(" Pending Requests ")
        self.NotifCircle.hide()
        self.NotifCircle2.hide()
        self.MainTabWidget.setCurrentWidget(self.PendingPage)

    async def toChat(self,id,name,icon,bio,color2,button,creation):
        if self.MainTabWidget.currentWidget() != self.MainChat or self.CurrentId != id:
            self.Vscroll.blockSignals(True) #block signals from scroll bar
            #change pages
            self.MainTabWidget.setCurrentWidget(self.MainChat)
            self.CurrentId = id
            self.toSideProfile()
            self.toUserTab()
            if self.SavedUSIB:
                self.DetailsArea.show()
            else:
                self.DetailsArea.hide()
            #set banner and bar changes
            self.SetBarChanges(name,icon)
            self.UserIcon.setImage(icon)
            self.BioTxt.setText(f"{ bio}")
            self.Banner.setStyleSheet(f"background-color: rgb({color2[0]},{color2[1]},{color2[2]}); border:none; border-radius: 0px; border-top-left-radius: 10px; border-top-right-radius: 10px;")
            self.ProfileLabel.setText(f"{name}")
            self.JoinedLabel.setText(creation)
            try:
                self.FriendBtn.clicked.disconnect()
            except:
                pass
            if self.isFriends(id):
                self.FriendBtn.setIcon(self.FriendPix2)
                self.FriendBtn.clicked.connect(lambda:asyncio.create_task(self.TriggerUnfriend()))
            elif self.isPending(id):
                self.FriendBtn.setIcon(self.FriendPix4)
                self.FriendBtn.clicked.disconnect()
            else:
                self.FriendBtn.setIcon(self.FriendPix3)
                self.FriendBtn.clicked.connect(lambda:self.QuickFriendRequest(name))
            #clear messages
            self.ClearChatMessages()
            self.FirstMesg = None
            #load messages
            if self.MessageHistory.get(id) is not None:
                self.LoadFromMemory(id)
            else:
                header = {
                    "Id1":self.User["ID"],
                    "Id2":str(id),
                }
                response = await asyncio.to_thread(lambda:requests.get("http://" + self.TargetIP + ":8000/api/users/retrieve/messages",headers=header,timeout=4))
                check = datetime.now()
                if response.status_code == 200:
                    Details = response.json()
                    if Details is not None:
                        self.ScrollBar.setUpdatesEnabled(False)
                        All = Details.get("Messages")
                        for x in All:
                            if x.get("SenderID") == int(self.User["ID"]):
                                savedId = x.get("RecipientID")
                                Theusername = self.User["Name"]
                                Theicon = self.User["ID"]
                                KeyUsed = x.get("SenderKey")
                            else:
                                for y in self.FriendInfo:
                                    if y.get("Id") == int(x.get("SenderID")):
                                        savedId = y.get("Id")
                                        Theusername = y.get("Name")
                                        Theicon = y.get("Id")
                                        KeyUsed = x.get("RecipientKey")
                                        break
                            self.ShowMessage(self.DecryptMessage(x.get("Text"),KeyUsed),x.get("Time"),Theusername,Theicon,savedId) #bottleneck
                        self.ScrollBar.setUpdatesEnabled(True)
                    print(f"estimated time took is {datetime.now()-check}")
            self.Vscroll.blockSignals(False)
            print("Messages loaded succesfully")
            if button.UnRead > 0:
                try:
                    asyncio.create_task(self.SendMessage(self.User["ID"],self.CurrentId,"text","ClearUnread")) 
                    print("Sent Clear Message")
                except:
                    e = traceback.format_exc()
                    print(e)
            else:
                print("didnt send clear message")
            print(button.UnRead)
            #set button changes
            button.UnRead = 0
            button.UnReadLbl.hide()
            button.Notif.hide()
            button.UnreadTimestamp = None
            try:
                button.LastMsg = self.MessageHistory[savedId][-1]
            except:
                pass
                

    def toSideProfile(self):
        self.DetailsTab.setCurrentWidget(self.SideProfile)

    def toBlank(self):
        self.DetailsTab.setCurrentWidget(self.BlankWidget)

    def toNormalBar(self):
        self.UpperTab.setCurrentWidget(self.NormalBar)
        self.DetailsTab.setStyleSheet("border: none;")

    def toInfoBar(self):
        self.UpperTab.setCurrentWidget(self.InfoBar)


    def toUserTab(self):
        self.UpperTab.setCurrentWidget(self.UserBar)
        self.DetailsTab.setStyleSheet("border: none; margin-bottom: 3px; margin-right: 3px;")

    #-----------------------------------------------
    #Friend Error
    def CloseError1(self):
        self.FriendError.hide()

    #Set changes------------------------------------
    def SetBarChanges(self,username,icon):
        self.BarIcon.setImage(icon)
        self.BarName.setText(f" {username}")

    def CloseUSIB(self):
        self.SavedUSIB = not self.SavedUSIB
        if self.DetailsArea.isVisible():
            self.DetailsArea.hide()
            self.HideUSIB.setIcon(self.USIBIcon2)
        else:
            self.DetailsArea.show()
            self.HideUSIB.setIcon(self.USIBIcon)

    #Friend Requests--------------------------------
    async def SendFriendRequest(self):
        if self.AddSearch.text().strip():
            header = {
                "SenderId":self.User["ID"],
                "RecipientName":self.AddSearch.text(),
            }
            try:
                response = await asyncio.to_thread(lambda:requests.post("http://" + self.TargetIP + ":8000/api/friends/requests",json=header,timeout=4))
                #response = requests.post("http://" + self.TargetIP + ":8000/api/friends/requests",json=header)
                if response.status_code == 200:
                    self.FriendError.setText("Request sent successfully")
                    self.FriendRequests.append(self.AddSearch.text())
                    self.FriendError.setStyleSheet("background-color: transparent; font-size: 15px; color: rgb(100,255,100); padding: 3px; border-radius: 6px; margin: 10px; margin-top: 0px;")
                else:
                    Details = response.json()
                    self.FriendError.setText(f"{Details.get("detail")}")
                    self.FriendError.setStyleSheet("background-color: transparent; font-size: 15px; color: rgb(255,100,100); padding: 3px; border-radius: 6px; margin: 10px; margin-top: 0px;")

            except Exception as e:
                print(e)
        else:
            self.FriendError.setText("Enter a valid username")
            self.FriendError.setStyleSheet("background-color: transparent; font-size: 15px; color: rgb(255,100,100); padding: 3px; border-radius: 6px; margin: 10px; margin-top: 0px;")
        self.FriendError.show()
        QTimer.singleShot(2000,lambda:self.CloseError1())

    def QuickFriendRequest(self,name):
        self.ReFriend = Refriend(self.User["ID"],name)
        self.Choice = self.ReFriend.exec()
        if self.Choice:
            asyncio.create_task(self.SendQuickFriendReq(name))
        else:
            print("invalid username")

    async def SendQuickFriendReq(self,name):
            header = {
                "SenderId":self.User["ID"],
                "RecipientName":name,
            }
            try:
                response = await asyncio.to_thread(lambda:requests.post("http://" + self.TargetIP + ":8000/api/friends/requests",json=header,timeout=4))
                #response = requests.post("http://" + self.TargetIP + ":8000/api/friends/requests",json=header)
                if response.status_code == 200:
                    print("Request sent successfully")
                    self.FriendBtn.setIcon(self.FriendPix4)
                    self.FriendBtn.clicked.disconnect()
                else:
                    Details = response.json()
                    Notice = FeedBack(Details.get("detail"),(255,70,70),self)
                    Notice.exec()

            except Exception as e:
                print(e)


    #make the notif and friend request widget
    def ShowFriendRequests(self,message):
        Friend = FriendRequestWidget(message.get("SenderId"),message.get("SenderName"),message.get("RecipientId"),UrlToData(message.get("Icon")))
        self.FriendRequests.append({"Id":message.get("SenderId"),"Name":message.get("SenderName")})
        self.FriendRequestsWidgets[message.get("SenderId")] = Friend
        self.FriendReqLbl.show()
        self.FriendReqCon.show()
        self.RequestsCounter = len(self.FriendRequests)
        self.FriendReqLbl.setText(f" • Friend Requests Received - {self.RequestsCounter}")
        self.FriendReqLayout.addWidget(Friend)

    def ShowPendingRequests(self,message):
        Pending = PendingRequestWidget(message.get("RecipientId"),message.get("RecipientName"),UrlToData(message.get("Icon")))
        self.PendingRequests.append({"Id":message.get("RecipientId"),"Name":message.get("RecipientName")})
        self.PendingRequestWidgets[message.get("RecipientId")] = Pending
        self.PendingPageLayout.removeItem(self.Force)
        self.PendingPageLayout.addWidget(Pending)
        self.PendingPageLayout.addItem(self.Force)

    # make the friend widgets
    def MakeFriends(self,id,name,status):
        self.ZeroFriends.hide()
        for friends in self.FriendInfo:
            if friends.get("Id") == id:
                pic = friends.get("Icon")
        for q in self.Friends:
            if q.get("Id") == id and q.get("Status") == "Accepted":
                self.AllLayout.removeItem(self.Press)
                self.Friend = FriendsWidget(id,name,status,pic)
                self.AllFriendsWidgets[id] = self.Friend
                self.AllLayout.addWidget(self.Friend)
                self.AllLayout.addItem(self.Press)
        self.CountFriends()

    def MakeOnline(self):
        #reset everything
        self.NoFriends.hide()
        self.OnlineCounter = 0
        while self.OnlineConLayout.count():
            item = self.OnlineConLayout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        #put the widgets
        if self.AllFriendsWidgets:
            for x in self.AllFriendsWidgets.values():
                if x.Status == "Online":
                    self.OnlineCounter += 1
                    self.Online = FriendsWidget(x.Id,x.Name,"Online",x.IconPath)
                    self.OnlineConLayout.addWidget(self.Online)
            self.OnlineLbl.setText(f" • Online - {self.OnlineCounter}")
        if self.OnlineCounter == 0:
            self.NoFriends.show()

    #priv chat related
    # makes the priv chat on the side
    def MakePrivateChat(self,Id,Name,ClickIt:bool,banner,bio,icon,creation):
        print("Triggered")
        self.PrivMsg = PrivateMessage(Id,Name,banner,bio,icon,creation)
        self.PrivChats[Id] = self.PrivMsg
        self.FriendsLayout.addWidget(self.PrivMsg)
        self.FriendsLayout.removeItem(self.RoomMaker)
        self.FriendsLayout.addItem(self.RoomMaker)
        self.SideGroup.addButton(self.PrivMsg.RaisedBtn)
        if ClickIt:
            self.PrivMsg.RaisedBtn.click()
            self.FriendBtn.setIcon(self.FriendPix2)
            self.FriendBtn.clicked.connect(lambda:asyncio.create_task(self.TriggerUnfriend()))
        #
        try:
            self.FriendReqLayout.removeWidget(self.PrivMsg)
        except:
            print("couldnt remove privmsg")
        if self.FriendRequestsWidgets:
            friend = self.FriendRequestsWidgets[Id]
            if friend is not None:
                self.FriendRequestsWidgets.remove(friend)
        else: 
            print("made a new friend request widget")
            self.FriendRequestsWidgets = {}

    #asyncio version
    def TriggerPrivateChat(self,Id,Name,click,Banner,Bio,Icon,creation):
        self.MakePrivateChat(Id,Name,click,Banner,Bio,UrlToData(Icon),creation)

    def isOnTop(self,id):
        if self.FriendsLayout is not None:
            item = self.FriendsLayout.itemAt(0)
            widget = item.widget()
            if widget.Id == id:
                return True
            return False

    def OnTop(self,id):
        target = self.PrivChats[id]
        self.FriendsLayout.insertWidget(0,target)
        target = None

    def SortPrivByStamp(self):
        for id in self.Timestamps.keys():
            if not self.isOnTop(id):
                self.OnTop(id)

    def ShowAllInfo(self):
        print(f"Friends: {self.Friends}")
        print(f"the size of your image is: {len(self.User["Icon"])}")

    #Web Socket-------------------------------------
    async def CreateSocket(self,Token,Id):
        try:
            self.url = "ws://" + self.TargetIP + f":8000/Web?Token={Token}&Id={Id}"
            self.User["Socket"] = await websockets.connect(self.url)
            print("Connected to WebSocket server!")

            self.Listening = asyncio.create_task(self.Listen())

            if self.Pages.currentWidget() == self.ConnectingPage:
                self.Pages.setCurrentWidget(self.Interface)
                self.SpinCircle.anim.stop()
        except:
            print("Couldnt Reconnect")
            QTimer.singleShot(3000, self.ReconnectSocket)

    def ReconnectSocket(self):
        Key = keyring.get_credential("Discus","user")
        if Key:
            Token = Key.password
            asyncio.create_task(self.CreateSocket(f"{self.User["Token"]}/{Token}",self.User["ID"]))

    async def Listen(self):
        try:
            async for message in self.User["Socket"]:
                message = json.loads(message)

                # For When a request is sent
                if message.get("Type") == "FriendRequest":
                    try:
                        print(f"Received a friend request from {message.get("SenderName")}")
                        if message.get("RecipientId") == int(self.User["ID"]):
                            if self.MainTabWidget.currentWidget() != self.PendingPage:
                                #self.PendingBtn.setText("🔹 Pending Requests ")
                                self.PendingBtn.setText(" Pending Requests      ")
                                self.NotifCircle.show()
                                self.NotifCircle2.show()
                            self.ShowFriendRequests(message)
                            #change status
                            for x in self.Friends:
                                if int(x.get("Id")) == int(message.get("SenderId")):
                                    if self.wereFriends(int(message.get("SenderId"))):
                                        x["Status"] = "RePending"
                                        print("Status changed")
                        elif message.get("SenderId") == int(self.User["ID"]):
                            if self.MainTabWidget.currentWidget() != self.PendingPage:
                                self.PendingCounter += 1
                                self.PendingLbl.setText(f" • Pending Requests Sent - {self.PendingCounter} ")
                                #self.PendingBtn.setText(" Pending Requests ")
                                self.PendingBtn.setText(" Pending Requests      ")
                                self.NotifCircle.show()
                                self.NotifCircle2.show()
                            self.ShowPendingRequests(message)
                            #change status
                            for x in self.Friends:
                                if int(x.get("Id")) == int(message.get("RecipientId")):
                                    if self.wereFriends(int(message.get("RecipientId"))):
                                        x["Status"] = "RePending"
                                        print("Status changed")
                        self.PendingBtn.show()
                    except Exception as e:
                        print(f"THE 'FriendRequest' ERROR IS: {e}")

                # For When the request is accepted
                elif message.get("Type") == "FriendRequestAccepted":
                    # for the one that the request was sent to
                    try:
                        if message.get("Recipient") == int(self.User["ID"]):
                            print("im in")
                            widget = self.FriendRequestsWidgets.get(message.get("Sender"))
                            if widget is not None:
                                print("widget found")
                                #make the priv chat
                                if not self.wereFriends(widget.Id):
                                    self.PrivateMakerSignal.emit(widget.Id,widget.Name,True,message.get("Banner"),message.get("Bio"),message.get("Icon"),message.get("Creation"))
                                    print("made private chat")
                                else:
                                    print(f"DIDNT MAKE PRIVATE CHAT BC {self.isFriends(widget.Id)} with {widget.Id}")
                                #update stats
                                if not self.wereFriends(widget.Id):
                                    print("we werent friends")
                                    self.Friends.append({"Id":widget.Id,
                                                        "Name":widget.Name,
                                                        "Status":"Accepted",
                                                        "PublicKey":load_pem_public_key(base64.b64decode(message.get("PublicKey")))})
                                    self.FriendInfo.append({"Id":widget.Id,
                                                            "Name":widget.Name,
                                                            "Banner":message.get("Banner"),
                                                            "Bio":message.get("Bio"),
                                                            "Icon":UrlToData(message.get("Icon")),
                                                            "Creation":message.get("Creation")})
                                else:
                                    print("we were friends")
                                for x in self.Friends:
                                    print(f"{int(x.get("Id")) == int(widget.Id)}")
                                    if int(x.get("Id")) == int(widget.Id):
                                        x["Status"] = "Accepted"
                                        print("Status changed")
                                if not self.madeFriends(int(widget.Id)):
                                    print("gonna make friend")
                                    self.MakeFriends(widget.Id,widget.Name,"Online")
                                    print("made friend")
                                # remove the user from the FriendRequests list
                                for user in self.FriendRequests:
                                    if user.get("Name") == message.get("Sender"):
                                        self.FriendRequests.remove(user)
                                        print("removed the friend request")
                                widget.Clean()
                                widget.deleteLater()
                            else:
                                print(f"WIDGET WAS NONE : {message.get("Sender")}")
                            self.hidePending(exception=True)
                        # for the one that sent the request
                        elif int(message.get("Sender")) == int(self.User["ID"]):
                            print("Im not in")
                            #make the priv chat
                            if not self.wereFriends(message.get("Recipient")):
                                self.PrivateMakerSignal.emit(message.get("Recipient"),message.get("Target"),False,message.get("Banner"),message.get("Bio"),message.get("Icon"),message.get("Creation"))
                                print("made the priv chat")
                            else:
                                print(f"DIDNT MAKE PRIVATE CHAT BC {self.isFriends(message.get("Recipient"))} with {message.get("Recipient")}")
                            #updating stats
                            if not self.isFriends(message.get("Recipient")):
                                self.Friends.append({"Id":message.get("Recipient"),
                                                    "Name":message.get("Target"),
                                                    "Status":"Accepted",
                                                    "PublicKey":load_pem_public_key(base64.b64decode(message.get("PublicKey")))})
                                self.FriendInfo.append({"Id":message.get("Recipient"),
                                                        "Name":message.get("Target"),
                                                        "Banner":message.get("Banner"),
                                                        "bio":message.get("Bio"),
                                                        "Icon":UrlToData(message.get("Icon")),
                                                        "Creation":message.get("Creation")})
                            else:
                                for x in self.Friends:
                                    if int(x.get("Id")) == int(message.get("Recipient")):
                                        x["Status"] = "Accepted"
                                        print("changed status")

                            if not self.madeFriends(int(message.get("Recipient"))):
                                print("gonna make friend")
                                self.MakeFriends(message.get("Recipient"),message.get("Target"),"Online")
                                print("made friend")
                            # remove the user from the FriendRequests list
                            if message.get("Target") in self.FriendRequests:
                                self.FriendRequests.remove(message.get("Target"))
                            widget = self.PendingRequestWidgets.get(message.get("Recipient"))
                            if widget is not None:
                                self.PendingPageLayout.removeWidget(widget)
                                del self.PendingRequestWidgets[message.get("Recipient")]
                                widget.Clean()
                                print("removed the widget")
                            else:
                                print(f"WIDGET WAS NONE : {message.get("Recipient")}")
                            for pend in self.PendingRequests:
                                if pend.get("Id") == message.get("Recipient"):
                                    self.PendingRequests.remove(pend)

                            self.PendingCounter = len(self.PendingRequestWidgets)
                            self.PendingLbl.setText(f" • Pending Requests Sent - {self.PendingCounter} ")

                            self.hidePending()
                        print("wth dude")
                    except BaseException as e:
                        print(f"THE 'FriendRequestAccepted' ERROR IS : {e}")
                        traceback.print_exc()



                elif message.get("Type") == "FriendRequestDeclined":
                    try:
                        # remove the widgets from the clients
                        if int(message.get("Recipient")) == int(self.User["ID"]):
                            print("im the recipient so aa")
                            #change status
                            for x in self.Friends:
                                if int(x.get("Id")) == message.get("Sender"):
                                    x["Status"] = "Deleted"
                                    print("Status changed")
                            # remove from friend requests
                            for user in self.FriendRequests:
                                if user.get("Name") == message.get("SenderName"):
                                    self.FriendRequests.remove(user)
                                    self.RequestsCounter = len(self.FriendRequests)
                                    print("I removed the user from friend requests")
                            self.PendingLbl.setText(f" • Pending Requests Sent - {self.PendingCounter} ")
                            #delete the widget
                            widget = self.FriendRequestsWidgets.get(message.get("Sender"))
                            if widget is not None:
                                self.FriendReqLayout.removeWidget(widget)
                                del self.FriendRequestsWidgets[message.get("Sender")]
                                if not self.FriendRequestsWidgets:
                                    self.FriendRequestsWidgets = {}
                                self.FriendReqLbl.setText(f" • Friend Requests Received - {self.RequestsCounter}")
                                widget.Clean()
                                widget.deleteLater()
                                print("widget deleted")
                            else:
                                print("Widget not found")
                                    
                        elif int(message.get("Sender")) == int(self.User["ID"]):
                            print("Im the sender so aa")
                            #change status
                            for x in self.Friends:
                                if int(x.get("Id")) == message.get("Recipient"):
                                    x["Status"] = "Deleted"
                                    print("Status changed")
                            #remove from friend requests
                            for friend in self.FriendRequests:
                                if friend == message.get("RecipientName"):
                                    self.FriendRequests.remove(friend)
                                    print("i removed friend")
                            #remove from pending
                            for user in self.PendingRequests:
                                if user.get("Name") == message.get("RecipientName"):
                                    self.PendingRequests.remove(user)
                                    self.PendingCounter -= 1
                                    print("I removed the user from friend requests")
                            self.PendingLbl.setText(f" • Pending Requests Sent - {self.PendingCounter} ")
                            #delete widget
                            widget = self.PendingRequestWidgets.get(message.get("Recipient"))
                            if widget is not None:
                                self.PendingPageLayout.removeWidget(widget)
                                del self.PendingRequestWidgets[message.get("Recipient")]
                                widget.Clean()
                                print("widget deleted")
                            else:
                                print("Widget not found")
                        self.hidePending()
                    except BaseException:
                        traceback.print_exc()


                elif message.get("Type") == "FriendDeleted":
                    try:
                        #mark friend as deleted
                        for y in self.Friends:
                            if int(y.get("Id")) == int(message.get("Id")):
                                y["Status"] = "Deleted"
                        self.CountFriends()
                        for x in self.AllFriendsWidgets.keys():
                            if int(x) == int(message.get("Id")):
                                self.AllLayout.removeWidget(self.AllFriendsWidgets.get(x))
                                self.AllFriendsWidgets.get(x).deleteLater()
                                obj = x
                        del self.AllFriendsWidgets[obj]
                        if self.CurrentId == message.get("Id"):
                            self.FriendBtn.setIcon(self.FriendPix3)
                    except Exception as e:
                        print(f"THE 'FriendDeleted' ERROR IS {e}")


                elif message.get("Type") == "MessageCanceled":
                    try:
                        self.ShowFaultyMessage(message.get("Text"),message.get("Time"),message.get("SenderName"),message.get("Sender"))
                    except Exception as e:
                        print(f"THE 'messageCanceled' ERROR IS {e}")


                # For When a message is sent
                else:
                    try:
                        print(f"Received: {message}")
                        if message.get("Sender") == int(self.User["ID"]):
                            savingId = message.get("Recipient")
                        elif message.get("Recipient") == int(self.User["ID"]):
                            savingId = message.get("Sender")
                        else:
                            print("Cant Find the the id")
                        self.SoundPlayer.play()
                        self.ShowMessage(self.DecryptMessage(message.get("Text"),message.get("Key")),message.get("Time"),message.get("SenderName"),str(message.get("Sender")),savingId,"new")
                        if not self.isOnTop(savingId):
                            self.OnTop(savingId)
                    except Exception as e:
                        print(f"THE 'message' ERROR IS {e}")
                        traceback.print_exc()
 
        except websockets.ConnectionClosed:
            print("disconnected from the websocket")
            self.Listening.cancel()
            if self.User["Socket"] is not None:
                await self.User["Socket"].close()
            self.SpinCircle.anim.start()
            self.toConnectingPage()
            QTimer.singleShot(3000, self.ReconnectSocket)
    
    # message related ---------------------------------------
    async def SendMessage(self,senderid,recid,text,type):
        if type != "Disconnect":
            if self.isFriends(recid):
                if self.User["Socket"] is not None:
                    Text,SenderKey,RecipientKey = self.EncryptMessage(text)
                    load = {
                        "Sender": int(senderid),
                        "Recipient": int(recid),
                        "Time":QTime.currentTime().toString("hh:mm"),
                        "Text":Text,
                        "SenderKey":SenderKey,
                        "RecipientKey":RecipientKey,
                        "Type":type
                    }
                    load = json.dumps(load)
                    await self.User["Socket"].send(load)
            else:
                self.ShowFaultyMessage(text,QTime.currentTime().toString("hh:mm"),self.User["Name"],self.User["ID"])

        elif type == "ClearUnread":
            if self.isFriends(recid):
                load = {
                    "Sender": int(senderid),
                    "Recipient": int(recid),
                    "Type":type
                }
                load = json.dumps(load)
                await self.User["Socket"].send(load)
        else:
            if self.User["Socket"] is not None:
                load = {
                    "Sender": int(senderid),
                    "Recipient": int(recid),
                    "Time":QTime.currentTime().toString("hh:mm"),
                    "Text":text,
                    "Type":type
                }
                load = json.dumps(load)
                await self.User["Socket"].send(load)

    def ShowMessage(self,msg,time,username,icon,id,Mode = "old"):
        chat = self.PrivChats[id]
        if Mode == "new":
            #notif
            if self.MainTabWidget.currentWidget() != self.MainChat:
                print("triggered 1")
                if chat.UnreadTimestamp is None:
                    chat.UnreadTimestamp = time
                chat.UnRead += 1
                chat.UnReadLbl.setText(f"{chat.UnRead}")
                chat.UnReadLbl.show()
                chat.Notif.show()

                if not chat.UnreadTimer.isActive():
                    chat.UnreadTimer.start()
            elif self.MainTabWidget.currentWidget() == self.MainChat and self.CurrentId != id:
                print("triggered 2")
                if chat.UnreadTimestamp is None:
                    chat.UnreadTimestamp = time
                chat.UnRead += 1
                chat.UnReadLbl.setText(f"{chat.UnRead}")
                chat.UnReadLbl.show()
                chat.Notif.show()
        self.ChatPanelLayout.removeItem(self.Space)
        #add the "new" lbl
        if time == chat.UnreadTimestamp and self.CurrentId == id and Mode == "old":
            new = NewLbl()
            self.ChatPanelLayout.addWidget(new)
            chat.UnreadTimestamp = None       
        #add the msg
        self.msg = MessageBox(msg,time,username,icon,id)
        if self.MessageHistory.get(id) is None and Mode == "new":
            pass
        elif self.MessageHistory.get(id) is not None:
            self.MessageHistory[id].append(self.msg)
        else:
            self.MessageHistory[id] = [self.msg]
        self.KeepCachedLimit()
        if self.CurrentId == id:
            #self.LastMesg = self.msg
            chat.LastMsg = self.msg
            self.ChatPanelLayout.addWidget(self.msg)
            print("I ADDED THE WIDGET (normal)")
        else:
            print("I STORED THE WIDGET")
        self.ChatPanelLayout.addItem(self.Space)

    def ShowOldMessage(self,msg,time,username,icon,id,LoadingMode = False):
        self.ChatPanelLayout.removeItem(self.Space)
        self.msg = MessageBox(msg,time,username,icon,id,LoadingMode=LoadingMode)
        self.PrivChats[id].LastMsg = self.msg
        self.FirstMesg = self.msg
        self.TempMessages.insert(-1,self.msg)
        self.ChatPanelLayout.insertWidget(0,self.msg)
        if len(self.MessageHistory.get(id)) < 50:
            self.MessageHistory[id].insert(0,self.msg)
        print("I ADDED THE WIDGET (old)")
        self.ChatPanelLayout.addItem(self.Space)

    def ShowFaultyMessage(self,msg,time,username,icon):
        self.ChatPanelLayout.removeItem(self.Space)
        self.msg = FaultyMessageBox(msg,time,username,icon,self.IconFolder + "Info2.png")
        self.ChatPanelLayout.addWidget(self.msg)
        self.ChatPanelLayout.addItem(self.Space)

    def LoadFromMemory(self,id):
        self.ChatPanelLayout.removeItem(self.Space)
        for item in self.MessageHistory[id]:
            if item.TheTime == self.PrivChats[id].UnreadTimestamp:
                new = NewLbl()
                self.ChatPanelLayout.addWidget(new)
                self.PrivChats[id].UnreadTimestamp = None
            self.msg = item
            self.ChatPanelLayout.addWidget(self.msg)
            self.msg.show()
        self.PrivChats[id].LastMsg = self.msg
        self.ChatPanelLayout.addItem(self.Space)

    def LoadExtraMessages(self,Position):
        if Position == self.Vscroll.minimum() and not self.Loading:
            print("Reached the top")
            self.Loading = True
            #
            self.OldMax = self.Vscroll.maximum()
            #
            if self.FirstMesg is None:
                self.FirstMesg = self.MessageHistory[self.CurrentId][0]
            self.Timestamp = self.FirstMesg.TheTime
            #---
            self.EmptyWidget = pyside.QWidget()
            self.EmptyWidget.setMinimumHeight(60)
            self.EWLayout = pyside.QGridLayout(self.EmptyWidget)
            self.SpinCircle = SimpleSpinner()
            self.SpinCircle.anim.start()
            self.EWLayout.addWidget(self.SpinCircle)
            self.ChatPanelLayout.insertWidget(0,self.EmptyWidget)
            #
            QTimer.singleShot(0,lambda:self.ScrollPositionCalc())
            QTimer.singleShot(2000, lambda: setattr(self, 'Loading', False))
            #
            asyncio.create_task(self.FetchOldMessages(self.Timestamp))

    def ScrollPositionCalc(self):
        self.ScrollBar.widget().adjustSize()
        self.Vscroll.setValue((self.Vscroll.maximum() - self.OldMax))

    def setMessageStyle(self):
        self.Counter = 0
        for z in self.TempMessages:
            self.Counter += 1
            if self.Counter < len(self.TempMessages) - 1 and z.User == self.TempMessages[self.Counter].User:
                z.HideName()
                z.TimeOnSide()
            else:
                z.ApplyNameStyle()
                z.TimeOnHeader()
        self.TempMessages.clear()

    def KeepCachedLimit(self):
        while len(self.MessageHistory) > 50:
            self.MessageHistory.pop(0)

    async def FetchOldMessages(self,TimeStamp):
        timed = StampTimer("api call")
        #actual request
        headers = {
            "Id":self.User["ID"],
            "Friend": str(self.CurrentId),
            "AuthToken":self.User["Token"],
            "TimeStamp":self.Timestamp
        }
        response = await asyncio.to_thread(lambda:requests.get("http://" + self.TargetIP + ":8000/api/users/retrieve/oldmessages",headers=headers,timeout=4))
        timed.Stop()
        timed.Start("old messages")
        if response.status_code == 200:
            Details = response.json()
            print("old message retrieval was successful")
            self.OldMax = self.Vscroll.maximum()
            #start putting the messages
            #self.Vscroll.setEnabled(False)
            self.Vscroll.blockSignals(True)
            if Details is not None:
                Old = Details.get("Messages")
                for x in Old:
                    if x.get("SenderID") == int(self.User["ID"]):
                        savedId = x.get("RecipientID")
                        Theusername = self.User["Name"]
                        Theicon = self.User["ID"]
                        KeyUsed = x.get("SenderKey")
                    else:
                        for y in self.FriendInfo:
                            if y.get("Id") == int(x.get("SenderID")):
                                savedId = y.get("Id")
                                Theusername = y.get("Name")
                                Theicon = y.get("Id")
                                KeyUsed = x.get("RecipientKey")
                                break
                    self.ShowOldMessage(self.DecryptMessage(x.get("Text"),KeyUsed),x.get("Time"),Theusername,Theicon,savedId,True) # bottleneck
                    #self.ShowOldMessage(x.get("Text"),x.get("Time"),Theusername,Theicon,savedId,True)
                    QTimer.singleShot(0,lambda:self.ScrollPositionCalc())
                    #await asyncio.sleep(0.05) # note: DO NOT USE THIS
                self.setMessageStyle()
            self.Vscroll.blockSignals(False)
            self.SpinCircle.anim.stop()
            self.EmptyWidget.deleteLater()
            self.SpinCircle.deleteLater()
            self.ChatPanel.update()
            QTimer.singleShot(0,lambda:self.ScrollPositionCalc()) 
            timed.Stop()
        else:
            print("old message retrieval failed")

    def UpdBeforeClose(self):
        header = []
        for chats in self.PrivChats.values():
            if chats.UnRead > 0:
                if chats.UnreadTimer.isActive():
                    chats.UnreadTimer.stop()
                    load = {
                        "Sender": self.User["ID"],
                        "Recipient": chats.Id,
                        "Timestamp": chats.UnreadTimestamp,
                        "Number": chats.UnRead,
                        "Type": "UpdateUnread"
                    }
                    header.append(load)
        requests.post("http://" + self.TargetIP + ":8000/api/users/unread",json=header,timeout=4)
        print("done, close now")

    # send mesg
    def Send(self,text):
        try:
            if text.strip():
                self.TypingBar.clear()
                asyncio.create_task(self.SendMessage(self.User["ID"],self.CurrentId,text,"Message"))   
        except Exception as e:
            print(e)     

    #Password derived encryption key
    def PasswordEncryptionKey(self,password:str, salt: bytes):
        Pkey = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600000
        )
        return base64.urlsafe_b64encode(Pkey.derive(password.encode()))

    #Logins and signups-----------------------------
  
    async def SignUp(self):
        self.ErrorReport2.hide()
        self.SubmitSignUp.blockSignals(True)

        if self.PassFeild2.text().strip():
            #Encryption------------------------------------------
            #making the Message Encryption Key
            RSA = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            MEKey = RSA.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
            ).decode('utf-8')
            PubKey = RSA.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            #making Storage Key
            SKey = Fernet.generate_key()
            StorageObj = Fernet(SKey)
            #making Encrypted Message Encryption Key
            EncKey = StorageObj.encrypt(MEKey.encode("utf-8"))
            #making Password based priv key
            TheSalt = os.urandom(16)
            PKey = self.PasswordEncryptionKey((self.PassFeild2.text()), TheSalt)
            Pcipher = Fernet(PKey)
            #making Wrapped key
            EnvKey = Pcipher.encrypt(SKey)
        header = {
                    "Username": self.UserFeild2.text(),
                    "Password": self.PassFeild2.text(),
                    "EncryptedKey":EncKey.decode("utf-8"),
                    "EnvelopeKey":EnvKey.decode("utf-8"),
                    "Salt":base64.b64encode(TheSalt).decode("utf-8"),
                    "PublicKey":base64.b64encode(PubKey).decode('utf-8')
                }
        MEKey = None
        RSA = None
        SKey = None
        PKey = None
        try:
            response = await asyncio.to_thread(lambda:requests.get("http://" + self.TargetIP + ":8000/api/signup",headers=header))
            #response = requests.get("http://" + self.TargetIP + ":8000/api/signup",headers=header)
            Details = response.json()
            if response.status_code == 200:
                #keyring.set_password("Discus",str(Details.get("id")),Details.get("authtoken"))
                self.UserFeild2.clear()
                self.PassFeild2.clear()
                self.UserFeild.clear()
                self.PassFeild.clear()
                self.toLogPage()
                self.ErrorReport.setStyleSheet("font-size: 15px; color: green; margin: 30px; margin-top: 0px; margin-bottom: 0px; font-weight: 600;")
                self.ErrorReport.show()
                self.ErrorReport.setText("Account created.Please login")
            else:
                self.ErrorReport2.setStyleSheet("font-size: 15px; color: red; margin: 30px; margin-top: 0px; margin-bottom: 0px; font-weight: 600;")
                self.ErrorReport2.show()
                self.ErrorReport2.setText(Details.get("detail"))
                print(Details.get("detail"))
        except:
            print("Could not Sign Up")
            traceback.print_exc()
            #print(Details.get("detail"))
            self.ErrorReport2.setStyleSheet("font-size: 15px; color: red; margin: 30px; margin-top: 0px; margin-bottom: 0px; font-weight: 600;")
            self.ErrorReport2.show()
            self.ErrorReport2.setText("An error occured,please try again later")
        finally:
            self.SubmitSignUp.blockSignals(False)

    async def Login(self):
        header = {
            "Username": self.UserFeild.text(),
            "Password": self.PassFeild.text()
        }
        self.ErrorReport.hide()
        self.SubmitLogIn.blockSignals(True)
        try:
            self.toLoadingPage()
            #self.SpinCircle2.anim.start()
            self.PercentageLbl.setText("0%")
            response = await asyncio.to_thread(lambda: requests.get("http://" + self.TargetIP + ":8000/api/login",headers=header,timeout=4))
            self.LoadingBar.setPercentage(25)
            self.PercentageLbl.setText("25%")
            await asyncio.sleep(0.05)
            #response = requests.get("http://" + self.TargetIP + ":8000/api/login",headers=header)
            Details = response.json()
            if response.status_code == 200:
                #self.FriendsBtn.click()
                self.User["ID"] = str(Details.get("id"))
                self.User["Name"] = Details.get("username")
                self.setWindowTitle(f"Discus - {self.User["Name"]}")
                self.User["Token"] = Details.get("token")
                self.User["Banner"] = Details.get("banner")
                self.User["Bio"] = Details.get("bio")
                self.User["Icon"] = UrlToData(Details.get("icon"))
                self.User["PublicKey"] = load_pem_public_key(base64.b64decode(Details.get("publickey")))
                try:
                    keyring.delete_password("Discus","user")
                except:
                    pass
                keyring.set_password("Discus","user",Details.get("authtoken"))
                #--------
                EncKey = Details.get("encryptedkey").encode("utf-8")
                EnvKey = Details.get("envelopekey").encode("utf-8")
                Salt = base64.b64decode(Details.get("salt"))
                try:
                    PKey = self.PasswordEncryptionKey(self.PassFeild.text(),Salt)
                    Pcipher = Fernet(PKey)
                    SKey = Pcipher.decrypt(EnvKey)
                    Scipher = Fernet(SKey)

                    Key = Scipher.decrypt(EncKey).decode("utf-8")
                    self.User["Key"] = Key
                    self.User["SKey"] = SKey.decode("utf-8")
                    self.User["Salt"] = Details.get("salt")
                    try:
                        keyring.delete_password("Discus:Key1","user")
                        keyring.delete_password("Discus:Key2","user")
                        keyring.delete_password("Discus:Key3","user")
                        keyring.delete_password("Discus:Key4","user")
                        keyring.delete_password("Discus:SKey","user")
                        keyring.delete_password("Discus:Salt","user")
                    except:
                        pass
                    Part1 = Key[:426]
                    Part2 = Key[426:852]
                    Part3 = Key[852:1278]
                    Part4 = Key[1278:]
                    keyring.set_password("Discus:Key1","user",Part1)
                    keyring.set_password("Discus:Key2","user",Part2)
                    keyring.set_password("Discus:Key3","user",Part3)
                    keyring.set_password("Discus:Key4","user",Part4)
                    keyring.set_password("Discus:SKey","user",SKey.decode("utf-8"))
                    keyring.set_password("Discus:Salt","user",Details.get("salt"))
                except:
                    traceback.print_exc()
                #--------
                self.UserFeild.clear()
                self.PassFeild.clear()
                asyncio.create_task(self.CreateSocket(self.User["Token"],self.User["ID"]))
                self.PercentageLbl.setText("50%")
                self.LoadingBar.setPercentage(50)
                await asyncio.sleep(0)
                self.ProfileView.ChangeInfo(self.User["Name"],self.User["Icon"])
                await self.RetrieveFriends(self.User["ID"])
                await asyncio.sleep(0)
                self.PercentageLbl.setText("75%")
                self.LoadingBar.setPercentage(75)
                await asyncio.sleep(0.05)
                self.toOnilneFriends()
                self.PercentageLbl.setText("100%")
                self.LoadingBar.setPercentage(100)
                await asyncio.sleep(0)
                self.ErrorReport.hide()
                self.toMainTab()
            else:
                print("Could not LogIn")
                print(Details.get("detail"))
                self.toLogTab()
                self.toLogPage()
                self.ErrorReport.setStyleSheet("font-size: 15px; color: red; margin: 30px; margin-top: 0px; margin-bottom: 0px; font-weight: 600;")
                self.ErrorReport.show()
                self.ErrorReport.setText(f"{Details.get("detail")}")
        except:
            print("Could not LogIn")
            traceback.print_exc()
            self.toLogTab()
            self.toLogPage()
            self.ErrorReport.setStyleSheet("font-size: 15px; color: red; margin: 30px; margin-top: 0px; margin-bottom: 0px; font-weight: 600;")
            self.ErrorReport.show()
            self.ErrorReport.setText("An error occured,please try again later")
        finally:
            self.SubmitLogIn.blockSignals(False)

    def removeError(self):
        self.ErrorReport.hide()

    async def AutoLogin(self):
        try:
            Auth = keyring.get_credential("Discus","user")
            Encry1 = keyring.get_credential("Discus:Key1","user")
            Encry2 = keyring.get_credential("Discus:Key2","user")
            Encry3 = keyring.get_credential("Discus:Key3","user")
            Encry4 = keyring.get_credential("Discus:Key4","user")
            S = keyring.get_credential("Discus:SKey","user")
            slt = keyring.get_credential("Discus:Salt","user")
            if Auth and Encry1 and Encry2 and Encry3 and Encry4 and S and slt:
                Token = Auth.password
                print(f"Found Token: {Token}")
                Part1 = Encry1.password
                Part2 = Encry2.password
                Part3 = Encry3.password
                Part4 = Encry4.password
                Key = Part1+Part2+Part3+Part4
                header = {
                    "Authentication": Token
                }
                SKey = S.password
                Salt = slt.password
                try:
                    self.toLoadingPage()
                    self.PercentageLbl.setText("0%")
                    self.LoadingBar.setPercentage(0)
                    response = await asyncio.to_thread(lambda:requests.get("http://" + self.TargetIP + ":8000/api/users/info",headers=header,timeout=3))
                    self.PercentageLbl.setText("25%")
                    self.LoadingBar.setPercentage(25)
                    await asyncio.sleep(0.05)
                    if response.status_code == 200:
                        Details = response.json()
                        print("AutoLogIn successfull",QTime.currentTime().toString("hh:mm:ss"))
                        self.User["ID"] = str(Details.get("id"))
                        self.User["Name"] = Details.get("username")
                        self.setWindowTitle(f"Discus - {self.User["Name"]}")
                        self.User["Token"] = Details.get("token")
                        self.User["Banner"] = Details.get("banner")
                        self.User["Bio"] = Details.get("bio")
                        self.User["Icon"] = UrlToData(Details.get("icon"))
                        self.User["Key"] = Key
                        self.User["PublicKey"] = load_pem_public_key(base64.b64decode(Details.get("publickey")))
                        self.PercentageLbl.setText("35%")
                        self.User["SKey"] = SKey
                        self.User["Salt"] = Salt
                        print("creating websocket",QTime.currentTime().toString("hh:mm:ss"))
                        asyncio.create_task(self.CreateSocket(self.User["Token"],self.User["ID"]))
                        self.PercentageLbl.setText("50%")
                        self.LoadingBar.setPercentage(50)
                        await asyncio.sleep(0)
                        print("websocket created",QTime.currentTime().toString("hh:mm:ss"))
                        self.ProfileView.ChangeInfo(self.User["Name"],self.User["Icon"])
                        print("retrieving friends",QTime.currentTime().toString("hh:mm:ss"))
                        self.measure = StampTimer("friend retrieval")
                        await self.RetrieveFriends(self.User["ID"])
                        self.measure.Stop()
                        del self.measure
                        self.PercentageLbl.setText("75%")
                        self.LoadingBar.setPercentage(75)
                        await asyncio.sleep(0.05)
                        print("friends retrieved",QTime.currentTime().toString("hh:mm:ss"))
                        print("making friends",QTime.currentTime().toString("hh:mm:ss"))
                        self.toOnilneFriends()
                        print("made friends",QTime.currentTime().toString("hh:mm:ss"))
                        self.PercentageLbl.setText("100%")
                        self.LoadingBar.setPercentage(100)
                        await asyncio.sleep(0.05)
                        self.toMainTab()
                    else:
                        Details = response.json()
                        print(Details.get("detail"))
                        self.toLogTab()
                        self.toLogPage()
                except:
                    self.toLogTab()
                    self.toLogPage()
                    traceback.print_exc()
            else:
                print(f"No token found")
        except():
            pass

    # Retrieving Info----------------------
    async def RetrieveFriends(self,Id):
        try:
            response = await asyncio.to_thread(lambda:requests.get("http://" + self.TargetIP + ":8000/api/users/retrieve/friends",headers={"ID":Id},timeout=4))
            await asyncio.sleep(0.05)
            #response = requests.get("http://" + self.TargetIP + ":8000/api/users/retrieve/friends",headers={"ID":Id})
            if response.status_code == 200:
                Details = response.json()
                #step % for loading screen
                looped = 0
                step = (len(Details.get("Friends")) + len(Details.get("PendingSent")) + len(Details.get("PendingReceived")))
                # for friends
                for people in Details.get("Friends"):
                    looped += 1
                    self.PercentageLbl.setText(f"{50 + (looped*step)}%")
                    self.LoadingBar.setPercentage(50 + (looped*step))
                    await asyncio.sleep(0)
                    print(f"percentage is {f"{50 + (looped*step)}%"}")
                    self.MakePrivateChat(people.get("SenderId"),people.get("SenderName"),False,people.get("Banner"),people.get("Bio"),UrlToData(people.get("Icon")),people.get("Creation"))
                    self.Friends.append({"Id":people.get("SenderId"),"Name":people.get("SenderName"),"Status":people.get("Status"),"PublicKey":load_pem_public_key(base64.b64decode(people.get("PublicKey")))})
                    self.FriendInfo.append({"Id":people.get("SenderId"),"Name":people.get("SenderName"),"Banner":people.get("Banner"),"Bio":people.get("Bio"),"Icon":UrlToData(people.get("Icon")),"Creation":people.get("Creation")},)
                    self.MakeFriends(people.get("SenderId"),people.get("SenderName"),"Offline")
                    await asyncio.sleep(0)
                self.CountFriends()
                # for pending sent
                for pending in Details.get("PendingSent"):
                    looped += 1
                    self.PercentageLbl.setText(f"{50 + (looped*step)}%")
                    self.LoadingBar.setPercentage(50 + (looped*step))
                    await asyncio.sleep(0)
                    print(f"i got {Details.get("PendingSent")}")
                    self.PendingCounter += 1
                    self.ShowPendingRequests({"RecipientId":pending.get("RecipientId"),"RecipientName":pending.get("RecipientName"),"Icon":pending.get("Icon")})
                    await asyncio.sleep(0)
                self.PendingLbl.setText(f" • Pending Requests Sent - {self.PendingCounter} ")
                # for pending received
                for request in Details.get("PendingReceived"):
                    looped += 1
                    self.PercentageLbl.setText(f"{50 + (looped*step)}%")
                    self.LoadingBar.setPercentage(50 + (looped*step))
                    await asyncio.sleep(0)
                    self.ShowFriendRequests({"SenderId":request.get("SenderId"),"SenderName":request.get("SenderName"),"RecipientId":request.get("RecipientId"),"Icon":request.get("Icon")})
                    await asyncio.sleep(0)
                self.hidePending()
                print("Friend retrieval succeded")
                for unrd in Details.get("NonRead"):
                    if unrd is not None:
                        selected = self.PrivChats[unrd[0]]
                        #selected.setStyleSheet("background-color: red;")
                        selected.UnreadTimestamp = unrd[1]
                        selected.UnRead = unrd[2]
                        selected.Notif.show()
                        selected.UnReadLbl.setText(f"{unrd[2]}") 
                        selected.UnReadLbl.show()
                if Details.get("LastTimestamps") is not None:
                    for stamps in Details.get("LastTimestamps"):
                        self.Timestamps[stamps[0]] = stamps[1]
                    self.Timestamps = SortDictionary(self.Timestamps)
                    self.SortPrivByStamp()
        except Exception as e:
            print(f"Friend retrieval failed bc of {e}")
            traceback.print_exc()

    async def RetrieveStatus(self):
        Group = []
        for x in self.Friends:
            if self.isFriends(x.get("Id")):
                Group.append(x.get("Id"))
        try:
            response = await asyncio.to_thread(lambda:requests.post("http://" + self.TargetIP + ":8000/api/users/retrieve/status",json=Group,timeout=4))
            if response.status_code == 200:
                Details = response.json()
                report = Details.get("Group")
                for y in report.keys():
                    self.AllFriendsWidgets[int(y)].Status = report[y]
                    self.AllFriendsWidgets[int(y)].setStatus()
                
        except:
            print("Friend status retrieval failed")

    def isFriends(self,id):
        for z in self.Friends:
            if int(z.get("Id")) == id and z.get("Status") == "Accepted":
                return True
        return False

    def isPending(self,id):
        for z in self.Friends:
            if int(z.get("Id")) == id and z.get("Status") == "RePending":
                return True
        return False

    def wereFriends(self,id):
        for z in self.Friends:
            if int(z.get("Id")) == id and (z.get("Status") == "Deleted" or z.get("Status") == "RePending"):
                return True
        return False

    def madeFriends(self,id):
        if self.AllFriendsWidgets.get(id) is not None:
            return True
        return False

    def CountFriends(self):
        count = 0
        for people in self.Friends:
            if people.get("Status") == "Accepted":
                count += 1
        self.FriendLbl.setText(f" • Friends - {count}")
        if count > 0:
            self.ZeroFriends.hide()
        else:
            self.ZeroFriends.show()

    def hidePending(self,exception = False):
        if (not self.PendingRequests) and (not self.FriendRequests):
            self.PendingBtn.setText(" Pending Requests ")
            self.PendingBtn.hide()
            self.NotifCircle.hide()
            self.NotifCircle2.hide()
            if not exception:
                self.OnlineBtn.click()
        else:
            #self.PendingBtn.setText(" Pending Requests      ")
            self.PendingBtn.show()
            #self.NotifCircle.show()
            #self.NotifCircle2.show()
            
    # Unfriend
    async def TriggerUnfriend(self):
        id = self.CurrentId
        for friends in self.Friends:
            if int(friends.get("Id")) == int(id):
                name = friends.get("Name")
        self.DelFriend = Unfriend(id,name)
        self.Choice = self.DelFriend.exec()
        if self.Choice:
            print("You accepted")
            headers = {
                "ID1":self.User["ID"],
                "ID2":id
            }
            try:
                response = await asyncio.to_thread(lambda:requests.post("http://" + self.TargetIP + ":8000/api/friends/delete",json=headers))
                #response = requests.post("http://" + self.TargetIP + ":8000/api/friends/delete",json=headers)
                if response.status_code == 200:
                    print("did it")
                    try:
                        self.FriendBtn.clicked.disconnect()
                    except:
                        pass
                    self.FriendBtn.setIcon(self.FriendPix3)
                    self.FriendBtn.clicked.connect(lambda:self.QuickFriendRequest(name))
                else:
                    Details = response.json()
                    print(Details.get("detail"))
                    
            except Exception as e:
                print(f"Friend Removal failed bc of: {e}")

    #clear layouts
    def ClearPriv(self):
        if self.FriendsLayout is not None:
            while self.FriendsLayout.count():
                item = self.FriendsLayout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

    def ClearFriendWidgets(self):
        if self.AllLayout is not None:
            while self.AllLayout.count() > 2:
                item = self.AllLayout.takeAt(2)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
            self.Press = pyside.QSpacerItem(20,20,pyside.QSizePolicy.Policy.Maximum,pyside.QSizePolicy.Policy.Expanding)
            self.AllLayout.addItem(self.Press)

    def ClearFriendReqWidgets(self):
        if self.FriendReqLayout is not None:
            while self.FriendReqLayout.count() > 1:
                item = self.FriendReqLayout.takeAt(1)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
    
    def ClearPendingReqWidgets(self):
        if self.PendingPageLayout is not None:
            while self.PendingPageLayout.count() > 1:
                item = self.PendingPageLayout.takeAt(1)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
            #reconstruct 
            window.FriendReqLbl = pyside.QLabel(" • Friend Requests Received - 0")
            window.FriendReqLbl.setStyleSheet("background-color: transparent; color: rgb(190,190,190); font-size: 17px; border: none; padding: 4px;")
            window.PendingPageLayout.addWidget(self.FriendReqLbl)
            window.FriendReqLbl.hide()
            #
            window.FriendReqCon = pyside.QWidget()
            window.FriendReqLayout = pyside.QVBoxLayout(self.FriendReqCon)
            window.FriendReqCon.setStyleSheet("background-color: rgb(30,30,30);")
            window.PendingPageLayout.addWidget(self.FriendReqCon)
            window.FriendReqCon.hide()
            window.PendingLbl = pyside.QLabel(f" • Pending Requests Sent - ")
            window.PendingLbl.setStyleSheet("background-color: transparent; color: rgb(190,190,190); font-size: 17px; border: none; padding: 4px; margin-top:10px; margin-bottom: 10px;")
            window.PendingPageLayout.addWidget(self.PendingLbl)
            #
            window.Force = pyside.QSpacerItem(20,20,pyside.QSizePolicy.Policy.Maximum,pyside.QSizePolicy.Policy.Expanding)
            window.PendingPageLayout.addItem(self.Force)

    def ClearChatMessages(self):
        if self.ChatPanelLayout is not None:
            while self.ChatPanelLayout.count():
                item = self.ChatPanelLayout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.hide()
                #     widget.deleteLater()
            self.LastMesg = None



#classes ------------------------------------------------

class TypeInput(pyside.QTextEdit):
    EnterSignal = Signal()
    def __init__(self):
        super().__init__()
        self.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        self.setTabChangesFocus(True)
        self.setStyleSheet("""QTextEdit{background-color: rgb(60,60,60); border-radius: 7px; font-size: 20px; margin-right: 0px;
                            margin-left: 20px; padding-top: 5px; color: white; border: none;}""")
        self.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        #this is tiring... let gemini do it
        self.document().setDocumentMargin(4)
        self.textChanged.connect(self.adjust_height)
        self.adjust_height()

    def adjust_height(self):
        # 1. Force the document layout to evaluate against current view width
        self.document().setTextWidth(self.viewport().width())
        
        # 2. Grab the exact content height calculated by Qt's layout engine
        doc_height = int(self.document().documentLayout().documentSize().height())
        
        # 3. If content height fits comfortably within 1 line (~30px raw), lock at 42px
        if doc_height <= 60:
            self.setFixedHeight(65)
            return

        # 4. For 2+ wrapped lines, clamp smoothly between 42px and 120px
        new_height = max(42, min(doc_height + 10, 160))
        self.setFixedHeight(new_height)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_height()

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key.Key_Return,Qt.Key.Key_Enter):
            if not (e.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                self.EnterSignal.emit()
                e.accept()
                return

        super().keyPressEvent(e)

class FriendRequestWidget(pyside.QFrame):
    def __init__(self,id,name,target,icon):
        super().__init__()
        self.Id = id
        self.Name = name
        self.Target = target
        self.IconPath = icon
        self.setStyleSheet("""QFrame{background-color: rgb(30,30,30); border-radius: 0px; border-top: 1px solid rgb(50,50,50); border-top: 1px solid rgb(50,50,50); border-bottom: 1px solid rgb(50,50,50);}
                            QFrame:hover{background-color: rgb(50,50,50); border-radius: 7px; border: none; }""")
        self.Layout = pyside.QHBoxLayout(self)
        self.Layout.setContentsMargins(10,5,10,5)
        self.setMaximumHeight(70)
        #
        self.InfoContainer = pyside.QWidget()
        self.InfoContainer.setStyleSheet("background-color: transparent; border:none;")
        self.InfoContainerLayout = pyside.QGridLayout(self.InfoContainer)
        #
        self.Icon = CircularImage(Path = self.IconPath,size=30)
        self.InfoContainerLayout.addWidget(self.Icon,0,0,2,1)
        #
        self.Namelbl = pyside.QLabel(f"{name}")
        self.Namelbl.setStyleSheet("background-color: transparent; font-size: 17px; color: rgb(200,200,200); border: none; font-weight: 600;")
        self.InfoContainerLayout.addWidget(self.Namelbl,0,1)
        #
        self.Description = pyside.QLabel("This user wants to be friends with you")
        self.Description.setStyleSheet("background-color: transparent; font-size: 17px; color: rgb(200,200,200); border: none;")
        self.InfoContainerLayout.addWidget(self.Description,1,1)
        self.Layout.addWidget(self.InfoContainer)
        #
        self.AcceptBtn = pyside.QPushButton("✔")
        self.AcceptBtn.setFixedHeight(36)
        self.AcceptBtn.setFixedWidth(36)
        self.AcceptBtn.setStyleSheet("""QPushButton{background-color: rgb(40,40,40); font-size: 20px; border-radius: 18px; color: green; border: none;}
                                        QPushButton:hover{background-color: rgb(20,20,20)}""")
        self.AcceptBtn.clicked.connect(lambda:asyncio.create_task(self.Accept()))
        self.Layout.addWidget(self.AcceptBtn)
        #
        self.DeclineBtn = pyside.QPushButton("✖")
        self.DeclineBtn.setFixedHeight(40)
        self.DeclineBtn.setFixedWidth(40)
        self.DeclineBtn.setStyleSheet("""QPushButton{background-color: rgb(40,40,40); font-size: 20px; border-radius: 18px; color: red; border: none;}
                                        QPushButton:hover{background-color: rgb(20,20,20)}""")
        self.DeclineBtn.clicked.connect(lambda:asyncio.create_task(self.Decline()))
        self.Layout.addWidget(self.DeclineBtn)

    async def Accept(self):
        header = {
            "User1":self.Id,
            "User2":self.Target,
            "Name1":self.Name,
            "Name2":window.User["Name"]
        }
        try:
            response = await asyncio.to_thread(lambda:requests.post("http://" + window.TargetIP + ":8000/api/friends/requests/accept",json=header))
            #response = requests.post("http://" + window.TargetIP + ":8000/api/friends/requests/accept",json=header)
            if response.status_code == 200:
                print("Accepted")
        except Exception as e:
            print(e)


    async def Decline(self):
        header = {
            "User1":self.Id,
            "User2":self.Target,
            "Name1":self.Name,
            "Name2":window.User["Name"]
        }
        try:
            response = await asyncio.to_thread(lambda:requests.post("http://" + window.TargetIP + ":8000/api/friends/requests/decline",json=header))
            #response = requests.post("http://" + window.TargetIP + ":8000/api/friends/requests/decline",json=header)
            if response.status_code == 200:
                print("Declined")
        except Exception as e:
            print(e)

    def Clean(self):
        for user in window.FriendRequests:
            if user.get("Id") == self.Id:
                window.FriendRequests.remove(user)
        if not window.FriendRequests:
            window.FriendReqLbl.hide()
            window.FriendReqCon.hide()

class FriendsWidget(pyside.QFrame):
    def __init__(self,id,name,status,icon):
        super().__init__()
        self.Id = id
        self.Name = name
        self.Status = status
        self.IconPath = icon
        self.setStyleSheet("""QFrame{background-color: rgb(30,30,30); border-radius: 0px; border-top: 1px solid rgb(50,50,50); border-top: 1px solid rgb(50,50,50); border-bottom: 1px solid rgb(50,50,50);}
                            QFrame:hover{background-color: rgb(50,50,50); border-radius: 7px; border: none; }""")
        self.Layout = pyside.QHBoxLayout(self)
        self.Layout.setContentsMargins(0,0,0,0)
        self.setMaximumHeight(70)
        #
        self.InfoContainer = pyside.QWidget()
        self.InfoContainer.setStyleSheet("background-color: transparent; border:none;")
        self.InfoContainerLayout = pyside.QGridLayout(self.InfoContainer)
        #
        self.Icon = CircularImage(Path=self.IconPath,size=30)
        self.InfoContainerLayout.addWidget(self.Icon,0,0,2,1)
        #
        self.Namelbl = pyside.QLabel(f"{name}")
        self.Namelbl.setStyleSheet("background-color: transparent; font-size: 17px; color: rgb(200,200,200); border: none; font-weight: 600; margin-left: 5px;")
        self.InfoContainerLayout.addWidget(self.Namelbl,0,1)
        #
        self.Description = pyside.QLabel(f"{status}")
        if self.Status == "Online":
            self.Description.setStyleSheet("background-color: transparent; font-size: 17px; color: rgb(100,250,100); border: none; margin-left: 5px;")
        else:
            self.Description.setStyleSheet("background-color: transparent; font-size: 17px; color: rgb(200,200,200); border: none; margin-left: 5px;")
        self.InfoContainerLayout.addWidget(self.Description,1,1)
        self.Layout.addWidget(self.InfoContainer)
        #
        self.toPriv = pyside.QPushButton("")
        self.toPriv.setStyleSheet("""QPushButton{background-color: transparent; color: rgb(200,200,200); border: none; border-radius: 10px; font-size: 30px; margin-right:20px;}
                                    QPushButton:hover{background-color: rgb(60,60,60);}""")
        self.PrivIcon = QIcon(window.IconFolder + "Chat2.png")
        self.toPriv.setIcon(self.PrivIcon)
        self.toPriv.setIconSize(QSize(35,35))
        self.toPriv.setSizePolicy(pyside.QSizePolicy.Policy.Maximum,pyside.QSizePolicy.Policy.Maximum)
        self.toPriv.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toPriv.clicked.connect(lambda:window.PrivChats[self.Id].RaisedBtn.click())
        self.Layout.addWidget(self.toPriv)
        
    def setStatus(self):
        self.Description.setText(f"{self.Status}")
        if self.Status == "Online":
            self.Description.setStyleSheet("background-color: transparent; font-size: 17px; color: rgb(100,250,100); border: none; margin-left: 5px;")
        else:
            self.Description.setStyleSheet("background-color: transparent; font-size: 17px; color: rgb(200,200,200); border: none; margin-left: 5px;")

class PrivateMessage(pyside.QFrame):
    def __init__(self,id,name,banner,bio,icon,creation):
        super().__init__()
        self.Id = id
        self.Name = name
        self.Banner = banner
        self.Bio = bio
        self.IconPath = icon
        self.UnRead = 0
        self.UnreadTimestamp = None
        self.LastMsg = None
        # convert
        bits = self.Banner[4:-1]
        r,g,b = bits.split(",")
        self.Color2 = (int(r),int(g),int(b))
        #
        self.setStyleSheet("""QFrame{background-color: transparent; border-radius: 0px; border-radius: 7px;}
                            QFrame:hover{background-color: rgb(40,40,40);}""")
        self.Layout = pyside.QHBoxLayout(self)
        self.Layout.setContentsMargins(10,5,10,5)
        self.setMaximumHeight(44)
        #timer
        self.UnreadTimer = QTimer(self)
        self.UnreadTimer.setInterval(10000)
        self.UnreadTimer.setSingleShot(True)
        self.UnreadTimer.timeout.connect(lambda:self.LiveUnread(id))
        #self.UnreadTimer.start()
        #notification
        self.Notif = CircleIcon(self)
        self.Notif.move(5,25)
        self.Notif.ChangeColor((230,70,70))
        self.Notif.setFixedSize(QSize(18,18))
        self.Notif.hide()
        #
        self.UnReadLbl = pyside.QLabel(f"{self.UnRead}",self)
        self.UnReadLbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.UnReadLbl.setFixedSize(QSize(23,15))
        self.UnReadLbl.setStyleSheet("background-color: transparent; font-size: 11px; color: white; border: none; font-weight: 700;")
        self.UnReadLbl.move(3,26)
        self.UnReadLbl.hide()
        #
        self.Icon = CircularImage(Path=self.IconPath,size=30)
        self.Layout.addWidget(self.Icon)
        #
        self.NameLbl = pyside.QLabel(f"{ name}")
        self.NameLbl.setStyleSheet("background-color: transparent; font-size: 17px; color: rgb(200,200,200); border: none; font-weight: 600;")
        self.Layout.addWidget(self.NameLbl)
        #
        self.Close = pyside.QPushButton("×")
        self.Close.setStyleSheet("""QPushButton{background-color: transparent; color: rgb(20,20,20); font-size: 30px; font-weight: 600; border-radius: 10px;}
                                    QPushButton:hover{color: rgb(200,200,200)}""")
        self.Layout.addWidget(self.Close,alignment=Qt.AlignmentFlag.AlignRight)
        #
        self.RaisedBtn = pyside.QPushButton("haaa",self)
        self.RaisedBtn.setCheckable(True)
        #window.SideGroup.addButton(self.RaisedBtn)
        self.RaisedBtn.setStyleSheet("""QPushButton{background-color: transparent; color: transparent; border-radius: 7px;}
                                        QPushButton:checked{background-color: rgba(200,200,200,0.2)}""")
        self.RaisedBtn.setSizePolicy(pyside.QSizePolicy.Policy.Expanding,pyside.QSizePolicy.Policy.Expanding)
        self.RaisedBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.RaisedBtn.clicked.connect(lambda:asyncio.create_task(window.toChat(self.Id,self.Name,self.IconPath,self.Bio,self.Color2,self,creation)))
        self.RaisedBtn.raise_()
        self.Notif.raise_()
        self.UnReadLbl.raise_()

    def LiveUnread(self,id):
        asyncio.create_task(self.UpdateUnread(window.User["ID"],id,self.UnreadTimestamp,self.UnRead))

    async def UpdateUnread(self,Id1,Id2,Timestamp,Number):
        if Number > 0:
            load = {
                "Sender": Id1,
                "Recipient": Id2,
                "Timestamp": Timestamp,
                "Number": Number,
                "Type": "UpdateUnread"
            }
            load = json.dumps(load)
            await window.User["Socket"].send(load)
        else:
            print("updating canceled")




    def resizeEvent(self, event):
        self.RaisedBtn.resize(self.size())
        super().resizeEvent(event)

    def enterEvent(self, event):
        self.Close.setStyleSheet("""QPushButton{background-color: transparent; color: rgb(200,200,200); font-size: 30px; font-weight: 600; border-radius: 10px;}
                                    QPushButton:hover{color: rgb(200,200,200)}""")
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.Close.setStyleSheet("""QPushButton{background-color: transparent; color: transparent; font-size: 30px; font-weight: 600; border-radius: 10px;}
                                    QPushButton:hover{color: rgb(200,200,200)}""")
        super().leaveEvent(event)

class MessageBox(pyside.QFrame):
    def __init__(self,message,time,username,icon,friend,LoadingMode = False):
        self.Id = int(icon)
        self.Message = message
        self.TheTime = time
        self.User = username
        self.OnSide = False
        self.FormatedTime,self.ExactDate = window.ReadableTime(time)
        self.FriendId = friend
        self.LastMsg = window.PrivChats[friend].LastMsg
        for user in window.FriendInfo:
            if user.get("Id") == message:
                self.User = user.get("Name")
                break

        super().__init__()
        if icon != window.User["ID"]:
            for user in window.FriendInfo:
                if int(user.get("Id")) == int(icon):
                    print("I GOT THE ICON")
                    self.IconPath = user.get("Icon")
            print("I DIDNT GET THE ICON")
        else:
            self.IconPath = window.User["Icon"]
        self.setSizePolicy(pyside.QSizePolicy.Policy.Preferred,pyside.QSizePolicy.Policy.Minimum)
        self.setMinimumWidth(0)
        self.setStyleSheet("""QFrame{background-color: rgb(30,30,30); margin: 5px; border-radius: 3px;}
                            QFrame:hover{background-color: rgb(50,50,50);}""")
        self.Layout = pyside.QGridLayout(self)
        self.Layout.setContentsMargins(0,0,0,0)
        self.Layout.setSpacing(0)
        #
        self.Icon = pyside.QWidget()
        self.Icon.setStyleSheet(f"background-color: transparent; border-radius: 15px; margin-left: 5px; margin-right: 5px;")
        self.Icon.setFixedSize(QSize(58,50))
        self.Layout.addWidget(self.Icon,0,0,2,1)
        #
        self.UserIcon = CircularImage(parent=self.Icon,size=45,Path= window.IconFolder + "Default.png")
        self.UserIcon.move(5,2)
        self.UserIcon.raise_()
        self.UserIcon.setImage(self.IconPath)
        # Just the message
        self.Text = FastWrapLabel(message)
        self.Layout.addWidget(self.Text,1,1) 
        # Header
        self.Header = pyside.QWidget()
        self.Header.setStyleSheet("""QWidget{background-color: transparent; margin: 0px;}
                                    QWidget:hover{background-color: transparent;}""")
        self.HeaderLayout = pyside.QHBoxLayout(self.Header)
        self.HeaderLayout.setSpacing(0)
        self.HeaderLayout.setContentsMargins(0,0,0,0)
        self.Layout.addWidget(self.Header,0,1)
        #
        self.NameLbl = pyside.QLabel(f"{self.User}")
        self.Time = pyside.QLabel(self.FormatedTime)

        self.NameLbl.setStyleSheet("""QLabel{background-color: transparent; color: white; font-size: 15px; margin: 0px; margin-top: 1px;}
                                QLabel:hover{background-color: transparent;}""")
        self.HeaderLayout.addWidget(self.NameLbl)
        if not LoadingMode:
            print("i used the constractor styling")
            if self.LastMsg is not None and self.LastMsg.User == self.User:
                self.HideName()
            elif self.LastMsg is not None:
                self.ApplyNameStyle()
            #
            if self.LastMsg is not None and self.LastMsg.User == self.User:
                self.TimeOnSide()
            else:
                self.TimeOnHeader()
        #
        self.Space = pyside.QSpacerItem(20,0,pyside.QSizePolicy.Policy.Expanding,pyside.QSizePolicy.Policy.Ignored)
        self.HeaderLayout.addItem(self.Space)

    def enterEvent(self, event):
        if self.OnSide:
            self.Time.setStyleSheet("""QLabel{background-color: transparent; color: rgb(150,150,150); font-size: 10px; margin: 0px; margin-top: 1px; font-weight: 600;}
                                    QLabel:hover{background-color: transparent;}""")
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.OnSide:
            self.Time.setStyleSheet("""QLabel{background-color: transparent; color: transparent; font-size: 10px; margin: 0px; margin-top: 1px; font-weight: 600;}
                                    QLabel:hover{background-color: transparent;}""")
        super().leaveEvent(event)

    def HideName(self):
        self.NameLbl.hide()
        self.UserIcon.hide()
        self.Icon.setFixedSize(QSize(58,20))
        self.setStyleSheet("""QFrame{background-color: rgb(30,30,30); margin: 5px; margin-top: 0px; margin-bottom: 0px; border-radius: 3px;}
                            QFrame:hover{background-color: rgb(50,50,50);}""")
        self.LastMsg.setStyleSheet("""QFrame{background-color: rgb(30,30,30); margin: 5px; margin-top: 0px; margin-bottom: 0px; border-radius: 3px;}
                                        QFrame:hover{background-color: rgb(50,50,50);}""")
    def ApplyNameStyle(self):
        self.LastMsg.setStyleSheet("""QFrame{background-color: rgb(30,30,30); margin: 5px; margin-top: 0px; border-radius: 3px;}
                                        QFrame:hover{background-color: rgb(50,50,50);}""")
    def TimeOnSide(self):
        self.OnSide = True
        self.Time.setFixedSize(QSize(58,30))
        self.Layout.removeWidget(self.Icon)
        self.Icon.deleteLater()
        self.Layout.addWidget(self.Time,0,0,2,1)
        self.Time.setText("    " + self.FormatedTime[-5:])
        self.Time.setStyleSheet("""QLabel{background-color: transparent; color: transparent; font-size: 10px; margin: 0px; margin-top: 1px; font-weight: 600;}
                                 QLabel:hover{background-color: transparent;}""")
        
    def TimeOnHeader(self):
        self.Time.setStyleSheet("""QLabel{background-color: transparent; color: rgb(150,150,150); font-size: 10px; margin: 0px; margin-top: 1px; font-weight: 600;}
                                QLabel:hover{background-color: transparent;}""")
        self.HeaderLayout.addWidget(self.Time)
        try:
            self.HeaderLayout.removeItem(self.Space)
            self.HeaderLayout.addItem(self.Space)
        except:
            self.Space = pyside.QSpacerItem(20,0,pyside.QSizePolicy.Policy.Expanding,pyside.QSizePolicy.Policy.Ignored)
            self.HeaderLayout.addItem(self.Space)

class FaultyMessageBox(pyside.QFrame):
    def __init__(self,message,time,username,icon,path):
        self.Message = message
        self.TheTime = time
        self.User = username
        self.IconPath = window.User["Icon"]
        for user in window.FriendInfo:
            if user.get("Id") == message:
                self.User = user.get("Name")
        super().__init__()
        self.setSizePolicy(pyside.QSizePolicy.Policy.Preferred,pyside.QSizePolicy.Policy.Minimum)
        self.setMinimumWidth(0)
        self.setStyleSheet("""QFrame{background-color: rgb(30,30,30); margin: 5px; border-radius: 3px;}
                            QFrame:hover{background-color: rgb(50,50,50);}""")
        self.Layout = pyside.QGridLayout(self)
        self.Layout.setContentsMargins(0,0,0,0)
        self.Layout.setSpacing(0)
        #
        self.Icon = pyside.QWidget()
        self.Icon.setStyleSheet(f"background-color: transparent; border-radius: 15px; margin-left: 5px; margin-right: 5px;")
        self.Icon.setFixedSize(QSize(58,50))
        self.Layout.addWidget(self.Icon,0,0,2,1)
        #
        self.UserIcon = CircularImage(parent=self.Icon,size=45,Path= window.IconFolder + "Default.png")
        self.UserIcon.move(5,2)
        self.UserIcon.raise_()
        self.UserIcon.setImage(self.IconPath)
        # Just the message
        self.Text = FastWrapLabel2(message)
        self.Layout.addWidget(self.Text,1,1) 
        #
        self.Error = pyside.QPushButton(" Message could not be sent")
        self.Pix = QIcon(path)
        self.Error.setIcon(self.Pix)
        self.Error.setIconSize(QSize(13,13))
        self.Error.setSizePolicy(pyside.QSizePolicy.Policy.Maximum,pyside.QSizePolicy.Policy.Maximum)
        self.Error.setStyleSheet("color: red; font-size: 12px; background-color: transparent;")
        self.Layout.addWidget(self.Error,2,1)
        # Header
        self.Header = pyside.QWidget()
        self.Header.setStyleSheet("""QWidget{background-color: transparent; margin: 0px;}
                                    QWidget:hover{background-color: transparent;}""")
        self.HeaderLayout = pyside.QHBoxLayout(self.Header)
        self.HeaderLayout.setSpacing(0)
        self.HeaderLayout.setContentsMargins(0,0,0,0)
        self.Layout.addWidget(self.Header,0,1)
        #
        self.Name = pyside.QLabel(f"{self.User}")
        self.Time = pyside.QLabel(f"{time}")

        if window.LastMesg is not None and window.LastMesg.User == self.User:
            self.Name.hide()
            #self.Time.hide()
            self.UserIcon.hide()
            self.Icon.setFixedSize(QSize(58,20))
            self.setStyleSheet("""QFrame{background-color: rgb(30,30,30); margin: 5px; margin-top: 0px; margin-bottom: 0px; border-radius: 3px;}
                                    QFrame:hover{background-color: rgb(50,50,50);}""")
            window.LastMesg.setStyleSheet("""QFrame{background-color: rgb(30,30,30); margin: 5px; margin-top: 0px; margin-bottom: 0px; border-radius: 3px;}
                                    QFrame:hover{background-color: rgb(50,50,50);}""")
        elif window.LastMesg is not None:
            window.LastMesg.setStyleSheet("""QFrame{background-color: rgb(30,30,30); margin: 5px; margin-top: 0px; border-radius: 3px;}
                                    QFrame:hover{background-color: rgb(50,50,50);}""")
           
        self.Name.setStyleSheet("""QLabel{background-color: transparent; color: white; font-size: 15px; margin: 0px; margin-top: 1px;}
                                QLabel:hover{background-color: transparent;}""")
        self.HeaderLayout.addWidget(self.Name)
        #
        if window.LastMesg is not None and window.LastMesg.User == self.User:
            self.Time.setStyleSheet("""QLabel{background-color: transparent; color: rgb(150,150,150); font-size: 10px; margin: 0px; margin-top: 1px; font-weight: 600;}
                                        QLabel:hover{background-color: transparent;}""")
            self.Layout.addWidget(self.Time,1,2,alignment=Qt.AlignmentFlag.AlignLeft) 
        else:
            self.Time.setStyleSheet("""QLabel{background-color: transparent; color: rgb(150,150,150); font-size: 10px; margin: 0px; margin-top: 1px; font-weight: 600;}
                                    QLabel:hover{background-color: transparent;}""")
            self.HeaderLayout.addWidget(self.Time)

        #
        self.Space = pyside.QSpacerItem(20,0,pyside.QSizePolicy.Policy.Expanding,pyside.QSizePolicy.Policy.Ignored)
        self.HeaderLayout.addItem(self.Space)

class NewLbl(pyside.QFrame):
    def __init__(self):
        super().__init__()
        self.setSizePolicy(pyside.QSizePolicy.Policy.Preferred,pyside.QSizePolicy.Policy.Minimum)
        self.setMinimumWidth(0)
        self.setStyleSheet("""QFrame{background-color: rgb(30,30,30); margin: 0px; margin-left: 10px; margin-right: 10px; border-radius: 0px;}""")
        self.Layout = pyside.QGridLayout(self)
        self.Layout.setContentsMargins(0,0,0,0)
        self.Layout.setSpacing(0)
        self.Layout.setRowStretch(0,1)
        self.Layout.setRowStretch(1,1)
        self.Layout.setColumnStretch(0,1)
        #
        self.Text = pyside.QLabel("New")
        self.Text.setStyleSheet("""border:none; color: white; font-size: 12px; background-color: red; border-top-left-radius: 3px; border-bottom-left-radius: 3px; 
                                    border-top-right-radius: 1px; border-bottom-right-radius: 0px; margin-left: 1px;""")
        self.Layout.addWidget(self.Text,0,1,2,1) 
        #
        self.bs = pyside.QWidget()
        self.bs.setStyleSheet("background-color: transparent; border-bottom: 1px solid red; margin-right: 0px; margin-left: 10px;")
        self.Layout.addWidget(self.bs,0,0)

class FastWrapLabel(pyside.QWidget):
    #NOT MY CLASS, ITS FROM GEMINI
    def __init__(self, text="", parent=None,FontSize = 20):
        super().__init__(parent)
        self._text = text
        self.doc = QTextDocument(self)

        # 1. SET FONT & SIZE DIRECTLY (20px white text)
        font = QFont()
        font.setPixelSize(FontSize)
        self.doc.setDefaultFont(font)

        # 2. SET DEFAULT TEXT COLOR (White)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Text, QColor("white"))
        # Also set HTML default text color fallback
        self.doc.setDefaultStyleSheet("body { color: white; }")

        # Configure native wrapping rules
        option = QTextOption()
        option.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere) 
        self.doc.setDefaultTextOption(option)
        
        self.setText(self._text)

    def setText(self, text):
        self._text = text
        # Wrap text in a block with inline margin/padding styling
        self.doc.setHtml(
            f"<div style='color: white; margin-bottom: 1px; padding-bottom: 3px;'>{text}</div>"
        )
        self.doc.setTextWidth(self.width())
        self.updateGeometry()
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.doc.setTextWidth(self.width())
        self.updateGeometry()

    def sizeHint(self):
        return QSize(int(self.doc.idealWidth()), int(self.doc.size().height()))

    def minimumSizeHint(self):
        return QSize(50, int(self.doc.size().height()))

    def paintEvent(self, event):
        painter = QPainter(self)
        self.doc.drawContents(painter)

class FastWrapLabel2(pyside.QWidget):
    #NOT MY CLASS, ITS FROM GEMINI
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self._text = text
        self.doc = QTextDocument(self)

        # 1. SET FONT & SIZE DIRECTLY (20px white text)
        font = QFont()
        font.setPixelSize(20)
        self.doc.setDefaultFont(font)

        # 2. SET DEFAULT TEXT COLOR (White)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Text, QColor("red"))
        # Also set HTML default text color fallback
        self.doc.setDefaultStyleSheet("body { color: red; }")

        # Configure native wrapping rules
        option = QTextOption()
        option.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere) 
        self.doc.setDefaultTextOption(option)
        
        self.setText(self._text)

    def setText(self, text):
        self._text = text
        # Wrap text in a block with inline margin/padding styling
        self.doc.setHtml(
            f"<div style='color: red; margin-bottom: 1px; padding-bottom: 3px;'>{text}</div>"
        )
        self.doc.setTextWidth(self.width())
        self.updateGeometry()
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.doc.setTextWidth(self.width())
        self.updateGeometry()

    def sizeHint(self):
        return QSize(int(self.doc.idealWidth()), int(self.doc.size().height()))

    def minimumSizeHint(self):
        return QSize(50, int(self.doc.size().height()))

    def paintEvent(self, event):
        painter = QPainter(self)
        self.doc.drawContents(painter)

class PendingRequestWidget(pyside.QFrame):
    def __init__(self,id,name,icon):
        super().__init__()
        self.User1 = id
        self.Name = name
        self.IconPath = icon
        self.setStyleSheet("""QFrame{background-color: rgb(30,30,30); border-radius: 0px; border-top: 1px solid rgb(50,50,50); border-top: 1px solid rgb(50,50,50); border-bottom: 1px solid rgb(50,50,50); margin-left: 7px; margin-right: 7px;}
                            QFrame:hover{background-color: rgb(50,50,50); border-radius: 7px; border: none; }""")
        self.Layout = pyside.QHBoxLayout(self)
        self.Layout.setContentsMargins(5,0,5,0)
        self.setMaximumHeight(70)
        #
        self.InfoContainer = pyside.QWidget()
        self.InfoContainer.setStyleSheet("background-color: transparent; border:none;")
        self.InfoContainerLayout = pyside.QGridLayout(self.InfoContainer)
        #
        self.Icon = CircularImage(Path=self.IconPath,size=30)
        self.InfoContainerLayout.addWidget(self.Icon,0,0,2,1)
        #
        self.Namelbl = pyside.QLabel(f"{name}")
        self.Namelbl.setStyleSheet("background-color: transparent; font-size: 17px; color: rgb(200,200,200); border: none; font-weight: 600; margin-left: 2px;")
        self.InfoContainerLayout.addWidget(self.Namelbl,0,1)
        #
        self.Description = pyside.QLabel("You sent a friend request to this user")
        self.Description.setStyleSheet("background-color: transparent; font-size: 17px; color: rgb(200,200,200); border: none; margin-left: 2px;")
        self.InfoContainerLayout.addWidget(self.Description,1,1)
        self.Layout.addWidget(self.InfoContainer)
        #
        self.DeclineBtn = pyside.QPushButton("✖")
        self.DeclineBtn.setFixedHeight(40)
        self.DeclineBtn.setFixedWidth(40)
        self.DeclineBtn.setStyleSheet("""QPushButton{background-color: rgb(40,40,40); font-size: 20px; border-radius: 18px; color: red; border: none;}
                                        QPushButton:hover{background-color: rgb(20,20,20)}""")
        self.DeclineBtn.clicked.connect(lambda:asyncio.create_task(self.Decline()))
        self.Layout.addWidget(self.DeclineBtn)


    async def Decline(self):
        header = {
            "User1":window.User["ID"],
            "User2":self.User1,
            "Name1":window.User["Name"],
            "Name2":self.Name
        }
        try:
            response = await asyncio.to_thread(lambda:requests.post("http://" + window.TargetIP + ":8000/api/friends/requests/decline",json=header))
            if response.status_code == 200:
                print("Declined")
        except Exception as e:
            print(e)

    def Clean(self):
        self.deleteLater()

class CircleIcon(pyside.QWidget):
    Color = None
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        if self.Color is None:
            p.setBrush(QColor(randint(0,255),randint(0,255),randint(0,255)))
        else:
            p.setBrush(QColor(self.Color[0],self.Color[1],self.Color[2]))
        p.drawEllipse(self.rect())

    def ChangeColor(self,color):
        self.Color = color
        self.update()

class SelfProfile(pyside.QFrame):
    def __init__(self,name,icon,path):
        super().__init__()
        self.Name = name
        self.IconPath = icon
        self.setStyleSheet("""QFrame{background-color: rgb(40,40,40); border-radius: 0px; border-radius: 7px; border:none; margin: 3px; margin-bottom: 5px;}
                            QFrame:hover{background-color: rgb(45,45,45);}""")
        self.Layout = pyside.QHBoxLayout(self)
        self.Layout.setContentsMargins(10,5,10,5)
        #
        self.Icon = CircularImage(Path=self.IconPath,size=30)
        self.Layout.addWidget(self.Icon)
        #
        self.NameLbl = pyside.QLabel(f"{ name}")
        self.NameLbl.setStyleSheet("background-color: transparent; font-size: 17px; color: rgb(200,200,200); border: none; font-weight: 600;")
        self.Layout.addWidget(self.NameLbl)
        #
        self.Pix = QIcon(path)
        self.SettingsBtn = pyside.QPushButton("")
        self.SettingsBtn.setIcon(self.Pix)
        self.SettingsBtn.setIconSize(QSize(30,30))
        self.SettingsBtn.setToolTip("Settings")
        self.SettingsBtn.setStyleSheet("""QPushButton{background-color: rgba(200,200,200,0); color: rgb(100,100,100); font-size: 22px; font-weight: 600; border-radius: 10px; border:none;}
                                    QPushButton:hover{color: rgb(200,200,200); background-color: rgba(200,200,200,0.1);}""")
        self.SettingsBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.SettingsBtn.clicked.connect(lambda:self.OpenSettings())
        self.Layout.addWidget(self.SettingsBtn,alignment=Qt.AlignmentFlag.AlignRight)

    def OpenSettings(self):
        self.SettingsPanel = Profile(parent=window)
        self.Responce = self.SettingsPanel.exec()

    def ChangeInfo(self,name,icon):
        self.NameLbl.setText(f"{ name}")
        self.IconPath = icon
        self.Icon.setImage(self.IconPath)

class Profile(pyside.QDialog):
    def __init__(self,parent = None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowFlags.FramelessWindowHint | Qt.WindowFlags.NoDropShadowWindowHint | Qt.Dialog)
        self.setWindowModality(Qt.WindowModal)
        self.setFixedSize(QSize(800,500))
        self.setWindowTitle("Profile")
        self.setStyleSheet("background-color: rgb(30,30,30); border: 1px solid rgb(100,100,100); border-radius: 10px; outline: none;")
        self.Layout = pyside.QGridLayout(self)
        self.Layout.setSpacing(0)
        self.Layout.setContentsMargins(0,0,0,0)
        self.Layout.setRowStretch(0,1)
        self.Layout.setRowStretch(1,19)
        #upper bar
        self.UpperBar = pyside.QWidget()
        self.UpperBarLayout = pyside.QGridLayout(self.UpperBar)
        self.UpperBarLayout.setColumnStretch(0,19)
        self.UpperBarLayout.setColumnStretch(1,1)
        self.UpperBar.setStyleSheet("background-color: transparent; border: none; border-bottom: 1px solid rgb(100,100,100); border-bottom-left-radius: 0px; border-bottom-right-radius: 0px;")
        self.Layout.addWidget(self.UpperBar,0,0)
        #
        self.BarLabel = pyside.QLabel("  Account Settings")
        self.BarLabel.setStyleSheet("font-size: 23px; color: rgb(200,200,200); border: none;")
        self.UpperBarLayout.addWidget(self.BarLabel,0,0)
        #
        self.CloseBtn = pyside.QPushButton("×")
        self.CloseBtn.setStyleSheet("""QPushButton{background-color: transparent; border-radius: 10px; font-size: 40px; border: none; color: rgb(200,200,200);}
                                        QPushButton:hover{background-color: rgba(200,200,200,0.1);}""")
        self.CloseBtn.setFixedSize(QSize(50,45))
        self.CloseBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.CloseBtn.clicked.connect(self.close)
        self.UpperBarLayout.addWidget(self.CloseBtn,0,1)
        #Main
        #
        self.Main = pyside.QWidget()
        self.Main.setStyleSheet("background-color: transparent; margin-right: 40px;")
        self.MainLayout = pyside.QGridLayout(self.Main)
        self.ScrollBar = pyside.QScrollArea()
        self.ScrollBar.setStyleSheet("background-color: transparent; border: none; margin-left: 25px; margin-right: 1px; margin-bottom: 5px;")
        self.ScrollBar.verticalScrollBar().setStyleSheet("""
            QScrollBar:vertical {
                border: none;
                background: rgb(30, 30, 30);
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #444444;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #666666;
                
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
                width: 0px;
                image: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        self.ScrollBar.horizontalScrollBar().setStyleSheet("""
            QScrollBar:horizontal {
                border: none;
                background: rgb(30, 30, 30);
                height: 10px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #444444;
                min-width: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #666666;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
                height: 0px;
                width: 0px;
                image: none;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)
        self.ScrollBar.setWidgetResizable(True)
        self.ScrollBar.setWidget(self.Main)
        self.Layout.addWidget(self.ScrollBar,1,0)
        #
        self.Anounce = pyside.QLabel("Account Info")
        self.Anounce.setStyleSheet("font-size: 25px; color: rgb(180,180,255); font-weight: 600;")
        self.MainLayout.addWidget(self.Anounce,0,0)
        #-----
        self.Holder = pyside.QWidget()
        self.Holder.setMinimumHeight(80)
        self.Holder.setStyleSheet("border-bottom: 1px solid rgb(100,100,100); border-radius: 0px;")
        self.HolderLayout = pyside.QGridLayout(self.Holder)
        self.HolderLayout.setColumnStretch(1,1)
        self.MainLayout.addWidget(self.Holder,1,0)
        #
        self.Username = pyside.QLabel("Username")
        self.Username.setStyleSheet("font-size: 18px; color: rgb(200,200,200); font-weight: 600; border: none;")
        self.HolderLayout.addWidget(self.Username,0,0)
        #
        self.NameData = pyside.QLabel(f"{window.User["Name"]}")
        self.NameData.setStyleSheet("font-size: 18px; color: rgb(200,200,200); font-weight: 600; border: none;")
        self.HolderLayout.addWidget(self.NameData,0,2)
        #
        self.Edit = pyside.QPushButton(" Edit ")
        self.Edit.setStyleSheet("""QPushButton{background-color: rgba(100,100,100,0.1); border-radius: 10px; padding: 3px; font-size: 23px; border: none; color: rgb(200,200,200);}
                                        QPushButton:hover{background-color: rgba(200,200,200,0.1);}""")
        self.Edit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.Edit.clicked.connect(lambda:self.OpenNameTab())
        self.HolderLayout.addWidget(self.Edit,0,3)
        #-----
        self.Holder2 = pyside.QWidget()
        self.Holder2.setMinimumHeight(80)
        self.Holder2.setStyleSheet("border-bottom: 1px solid rgb(100,100,100); border-radius: 0px;")
        self.HolderLayout2 = pyside.QGridLayout(self.Holder2)
        self.HolderLayout2.setColumnStretch(1,1)
        self.MainLayout.addWidget(self.Holder2,2,0)
        #
        self.Password = pyside.QLabel("Password")
        self.Password.setStyleSheet("font-size: 18px; color: rgb(200,200,200); font-weight: 600; border: none;")
        self.HolderLayout2.addWidget(self.Password,0,0)
        #
        self.Edit2 = pyside.QPushButton(" Edit ")
        self.Edit2.setStyleSheet("""QPushButton{background-color: rgba(100,100,100,0.1); border-radius: 10px; padding: 3px; font-size: 23px; border: none; color: rgb(200,200,200);}
                                        QPushButton:hover{background-color: rgba(200,200,200,0.1);}""")
        self.Edit2.setCursor(Qt.CursorShape.PointingHandCursor)
        self.Edit2.clicked.connect(lambda:self.OpenPasswordTab())
        self.HolderLayout2.addWidget(self.Edit2,0,2)
        #-----
        self.Anounce2 = pyside.QLabel("Profile Appearance")
        self.Anounce2.setStyleSheet("font-size: 25px; color: rgb(180,180,255); font-weight: 600; margin-top: 20px; margin-bottom: 20px;")
        self.MainLayout.addWidget(self.Anounce2,3,0)
        #-----
        self.Holder3 = pyside.QWidget()
        self.Holder3.setMinimumHeight(80)
        self.Holder3.setStyleSheet("border-bottom: 1px solid rgb(100,100,100); border-radius: 0px;")
        self.HolderLayout3 = pyside.QGridLayout(self.Holder3)
        self.HolderLayout3.setColumnStretch(1,1)
        self.MainLayout.addWidget(self.Holder3,4,0)
        #
        self.Icon = pyside.QLabel("Icon")
        self.Icon.setStyleSheet("font-size: 18px; color: rgb(200,200,200); font-weight: 600; border: none;")
        self.HolderLayout3.addWidget(self.Icon,0,0)
        #
        self.Edit3 = pyside.QPushButton(" Edit ")
        self.Edit3.setStyleSheet("""QPushButton{background-color: rgba(100,100,100,0.1); border-radius: 10px; padding: 3px; font-size: 23px; border: none; color: rgb(200,200,200);}
                                        QPushButton:hover{background-color: rgba(200,200,200,0.1);}""")
        self.Edit3.setCursor(Qt.CursorShape.PointingHandCursor)
        self.Edit3.clicked.connect(lambda:self.OpenIconTab())
        self.HolderLayout3.addWidget(self.Edit3,0,2)
        #-----
        self.Holder4 = pyside.QWidget()
        self.Holder4.setMinimumHeight(80)
        self.Holder4.setStyleSheet("border-bottom: 1px solid rgb(100,100,100); border-radius: 0px;")
        self.HolderLayout4 = pyside.QGridLayout(self.Holder4)
        self.HolderLayout4.setColumnStretch(1,1)
        self.MainLayout.addWidget(self.Holder4,5,0)
        #
        self.Banner = pyside.QLabel("Banner")
        self.Banner.setStyleSheet("font-size: 18px; color: rgb(200,200,200); font-weight: 600; border: none;")
        self.HolderLayout4.addWidget(self.Banner,0,0)
        #
        self.ColorData = pyside.QLabel(f"{window.User["Banner"][4:-1]}")
        x,y,z = window.User["Banner"][4:-1].split(",")
        if int(x)+int(y)+int(z) > 400:
            self.ColorData.setStyleSheet(f"background-color: rgb({x},{y},{z}); font-size: 18px; color: black; font-weight: 600; padding: 4px; border: none; border-radius: 10px;")
        else:
            self.ColorData.setStyleSheet(f"background-color: rgb({x},{y},{z}); font-size: 18px; color: rgb(200,200,200); font-weight: 600; padding: 4px; border: none; border-radius: 10px;")
        self.HolderLayout4.addWidget(self.ColorData,0,2)
        #
        self.Edit4 = pyside.QPushButton(" Edit ")
        self.Edit4.setStyleSheet("""QPushButton{background-color: rgba(100,100,100,0.1); border-radius: 10px; padding: 3px; font-size: 23px; border: none; color: rgb(200,200,200);}
                                        QPushButton:hover{background-color: rgba(200,200,200,0.1);}""")
        self.Edit4.setCursor(Qt.CursorShape.PointingHandCursor)
        self.Edit4.clicked.connect(lambda:self.OpenBannerTab())
        self.HolderLayout4.addWidget(self.Edit4,0,3)
        #-----
        self.Holder5 = pyside.QWidget()
        self.Holder5.setMinimumHeight(80)
        self.Holder5.setStyleSheet("border-bottom: 1px solid rgb(100,100,100); border-radius: 0px;")
        self.HolderLayout5 = pyside.QGridLayout(self.Holder5)
        self.HolderLayout5.setColumnStretch(1,1)
        self.MainLayout.addWidget(self.Holder5,6,0)
        #
        self.Bio = pyside.QLabel("Bio")
        self.Bio.setStyleSheet("font-size: 18px; color: rgb(200,200,200); font-weight: 600; border: none;")
        self.HolderLayout5.addWidget(self.Bio,0,0)
        #
        self.BioData = pyside.QLabel(f"{window.User["Bio"][0:20]}...")
        self.BioData.setStyleSheet("font-size: 18px; color: rgb(200,200,200); font-weight: 600; border: none;")
        self.HolderLayout5.addWidget(self.BioData,0,2)
        #
        self.Edit5 = pyside.QPushButton(" Edit ")
        self.Edit5.setStyleSheet("""QPushButton{background-color: rgba(100,100,100,0.1); border-radius: 10px; padding: 3px; font-size: 23px; border: none; color: rgb(200,200,200);}
                                        QPushButton:hover{background-color: rgba(200,200,200,0.1);}""")
        self.Edit5.setCursor(Qt.CursorShape.PointingHandCursor)
        self.Edit5.clicked.connect(lambda:self.OpenBioTab())
        self.HolderLayout5.addWidget(self.Edit5,0,3)
        #
        self.SoundAnounce = pyside.QLabel("Sound")
        self.SoundAnounce.setStyleSheet("font-size: 25px; color: rgb(180,180,255); font-weight: 600;")
        self.MainLayout.addWidget(self.SoundAnounce,7,0)
        #
        self.Holder6 = pyside.QWidget()
        self.Holder6.setMinimumHeight(80)
        self.Holder6.setStyleSheet("border-bottom: 1px solid rgb(100,100,100); border-radius: 0px;")
        self.HolderLayout6 = pyside.QGridLayout(self.Holder6)
        self.HolderLayout6.setColumnStretch(0,1)
        self.HolderLayout6.setColumnStretch(1,1)
        self.MainLayout.addWidget(self.Holder6,8,0)
        #
        self.Notification = pyside.QLabel("Notification")
        self.Notification.setStyleSheet("font-size: 18px; color: rgb(200,200,200); font-weight: 600; border: none;")
        self.HolderLayout6.addWidget(self.Notification,0,0)
        #
        self.Value = window.Settings.value("Sound", 1.0, type=float)
        self.NotifData = pyside.QLabel(f"{round(self.Value*100)}%")
        self.NotifData.setStyleSheet("font-size: 18px; color: rgb(200,200,200); font-weight: 600; border: none; margin-left: 2px;")
        self.HolderLayout6.addWidget(self.NotifData,0,3)
        #
        self.SliderTimer = QTimer()
        self.SliderTimer.setInterval(600)
        self.SliderTimer.setSingleShot(True)
        self.SliderTimer.timeout.connect(lambda:self.SaveSound())
        #
        self.Edit6 = pyside.QSlider(Qt.Horizontal)
        self.Edit6.setFixedSize(QSize(250,30))
        self.Edit6.setRange(0,100)
        self.Edit6.setValue(self.Value*100)
        self.Edit6.setStyleSheet("""
            QSlider{
                border:none;
                margin: 0px;
            }
            QSlider::groove:horizontal {
                border: 1px solid #444444;
                height: 6px;
                background: #2b2b2b;
                border-radius: 3px;
            }

            QSlider::sub-page:horizontal {
                background: rgb(100,100,100);
                border-radius: 3px;
            }

            QSlider::handle:horizontal {
                background: rgb(40,40,40);
                border: 1px solid #cccccc;
                width: 9px;
                height: 19px;
                margin: -5px 0;
                border-radius: 4px;
            }

            QSlider::handle:horizontal:hover {
                background: rgb(40,40,40);
                border-color: rgb(150,150,255);
            }
        """)
        self.Edit6.setCursor(Qt.CursorShape.PointingHandCursor)
        self.Edit6.valueChanged.connect(lambda:self.SoundChanged())
        self.Edit6.sliderReleased.connect(lambda:self.SaveSound())
        self.HolderLayout6.addWidget(self.Edit6,0,2)
        #
        self.Cont = pyside.QWidget()
        self.Cont.setStyleSheet("margin-top: 30px;")
        self.ContL = pyside.QGridLayout(self.Cont)
        self.MainLayout.addWidget(self.Cont,9,0)
        #
        self.LogOutBtn = pyside.QPushButton("Log Out")
        self.LogOutBtn.setStyleSheet("""QPushButton{background-color: rgb(50,50,50); font-size: 23px; color: rgb(200,200,200); padding: 4px; margin: 10px; margin-right: 50px;}
                                        QPushButton:hover{background-color: rgb(40,40,40);}""")
        self.LogOutBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.LogOutBtn.clicked.connect(lambda:asyncio.create_task(self.LogOut()))
        self.ContL.addWidget(self.LogOutBtn,0,1)
        #
        self.DeleteBtn = pyside.QPushButton("Delete Account")
        self.DeleteBtn.setStyleSheet("""QPushButton{background-color: rgb(200,50,50); font-size: 23px; color: rgb(200,200,200); padding: 4px; margin: 10px; margin-left: 50px;}
                                        QPushButton:hover{background-color: rgb(150,50,50);}""")
        self.DeleteBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ContL.addWidget(self.DeleteBtn,0,0)

    def OpenNameTab(self):
        self.Changer = NameChanging(self)
        self.Answer = self.Changer.exec()
        if self.Answer:        
            asyncio.create_task(self.ChangeName())

    async def ChangeName(self):
            Characters = string.ascii_letters + string.digits + "_."
            header = {
                "Id":window.User["ID"],
                "NewUser":self.Changer.UserFeild.text(),
                "Password":self.Changer.PassFeild.text(),
                "Token":window.User["Token"]
            }
            if self.Changer.UserFeild.text().strip() and self.Changer.PassFeild.text().strip() and self.Changer.UserFeild.text() != window.User["Name"]:
                if self.Changer.UserFeild.text() and len(self.Changer.UserFeild.text()) <= 20:
                    if all(char in Characters for char in self.Changer.UserFeild.text()):
                        response = await asyncio.to_thread(lambda:requests.post("http://" + window.TargetIP + ":8000/api/users/username",json=header))
                        #response = requests.post("http://" + window.TargetIP + ":8000/api/users/username",json=header)
                        Details = response.json()
                        if response.status_code == 200:

                            # set the name on most labels
                            window.User["Name"] = Details.get("Name")
                            self.NameData.setText(f"{window.User["Name"]}")
                            window.ProfileView.NameLbl.setText(f"{ window.User["Name"]}")
                            window.ProfileView.Name = window.User["Name"]
                            #
                            feed = FeedBack(Details.get("message"),(70,255,70),self)
                            feed.exec()
                        else:
                            print(Details.get("detail"))
                            feed = FeedBack(Details.get("detail"),(255,70,70),self)
                            feed.exec()
                    else:
                        feed = FeedBack("Unaccepted characters",(255,70,70),self)
                        feed.exec()
                else:
                    feed = FeedBack("Name cant be empty or greater than 20 characters",(255,70,70),self)
                    feed.exec()
            else:
                feed = FeedBack("Please fill the feilds correctly",(255,70,70),self)
                feed.exec()

    def OpenPasswordTab(self):
        self.Changer = PassChanging(self)
        self.Answer = self.Changer.exec()
        if self.Answer:
            Key = window.User["Key"]
            Salt = window.User["Salt"]
            Salt = base64.b64decode(Salt)
            PKey = window.PasswordEncryptionKey(self.Changer.NewPassFeild.text(),Salt)
            Pcipher = Fernet(PKey)
            SKey = window.User["SKey"]
            SKey = SKey.encode("utf-8")
            if self.Changer.CurPassFeild.text() != self.Changer.NewPassFeild.text():
                asyncio.create_task(self.ChangePassword(Pcipher,SKey))
            else:
                feed = FeedBack("Your new password cant be the same as the old one",(255,70,70),self)
                feed.exec()

    async def ChangePassword(self,Pcipher,SKey):
            EnvKey = Pcipher.encrypt(SKey)
            header = {
                "Id":window.User["ID"],
                "Password":self.Changer.CurPassFeild.text(),
                "NewPassword":self.Changer.NewPassFeild.text(),
                "Token":window.User["Token"],
                "EnvelopeKey":EnvKey.decode("utf-8")
            }
            if self.Changer.CurPassFeild.text().strip() and self.Changer.NewPassFeild.text().strip() and self.Changer.CNewPassFeild.text().strip() and self.Changer.NewPassFeild.text() == self.Changer.CNewPassFeild.text():
                response = await asyncio.to_thread(lambda:requests.post("http://" + window.TargetIP + ":8000/api/users/password",json=header))
                #response = requests.post("http://" + window.TargetIP + ":8000/api/users/password",json=header)  
                Details = response.json()
                if response.status_code == 200:
                    print("all good password changed")
                    #
                    feed = FeedBack(Details.get("message"),(70,255,70),self)
                    feed.exec()
                else:
                    print(Details.get("detail"))
                    feed = FeedBack(Details.get("detail"),(255,70,70),self)
                    feed.exec()
            else:
                feed = FeedBack("Please fill the feilds correctly",(255,70,70),self)
                feed.exec()

    def OpenIconTab(self):
        self.Changer = IconChanging(self)
        self.Answer = self.Changer.exec()
        if self.Answer:
            FilePath = self.Changer.ChosenPath
            *_,image = FilePath.split("/")
            with Pillow.open(FilePath) as RawImage:
                RawImage.thumbnail((160,160))
                # Image = RawImage.read()
                Name = image
                size = 7.5 * 1024
                quality = 95
                while True:
                    buffer = io.BytesIO()
                    RawImage.save(buffer, format="JPEG", quality=quality)
                    Image = buffer.getvalue()
                    if len(Image) <= size or quality <= 30:
                        break
                    quality -= 5
                
            print(f"Compressed size: {len(Image)} bytes")
            asyncio.create_task(self.ChangeIcon(Name,Image))

    async def ChangeIcon(self,Name,Image):
                header = {
                    "Id":window.User["ID"],
                    "Token":window.User["Token"]
                }
                File = {"Image": (Name,Image)}
                response = await asyncio.to_thread(lambda:requests.post("http://" + window.TargetIP + ":8000/api/users/icon",data=header,files=File))
                #response = requests.post("http://" + window.TargetIP + ":8000/api/users/icon",data=header,files=File)  
                Details = response.json()
                if response.status_code == 200:
                    print("all good Icon changed")
                    window.User["Icon"] = UrlToData(Details.get("image"))
                    window.ProfileView.IconPath = window.User["Icon"]
                    window.ProfileView.Icon.setImage(window.User["Icon"])
                    feed = FeedBack(Details.get("message"),(70,255,70),self)
                    feed.exec()

                else:
                    print(Details.get("detail"))
                    feed = FeedBack(Details.get("detail"),(255,70,70),self)
                    feed.exec()

    def OpenBannerTab(self):
        while True:
            self.Changer = BannerChanging(self)
            self.Answer = self.Changer.exec()
            if self.Answer:
                color = self.Changer.ColorPicker.currentColor()
                r,g,b,_ = color.getRgb()
                color2 = f"{r},{g},{b}"
                self.Preview = ProfilePreview(self,color2)
                self.Answer2 = self.Preview.exec()
                if self.Answer2:
                    asyncio.create_task(self.ChangeBanner(color))
                else:
                    continue
            else:
                break

    async def ChangeBanner(self,color):
                header = {
                    "Id":window.User["ID"],
                    "Color": f"rgb({color.red()},{color.green()},{color.blue()})",
                    "Token":window.User["Token"]
                }
                if color != window.User["Banner"]:
                    response = await asyncio.to_thread(lambda:requests.post("http://" + window.TargetIP + ":8000/api/users/banner",json=header)  )
                    #response = requests.post("http://" + window.TargetIP + ":8000/api/users/banner",json=header)  
                    Details = response.json()
                    if response.status_code == 200:
                        print("all good banner changed")
                        #
                        window.User["Banner"] = Details.get("color")
                        self.ColorData.setText(f"{window.User["Banner"][4:-1]}")
                        x,y,z = window.User["Banner"][4:-1].split(",")
                        if int(x)+int(y)+int(z) > 450:
                            self.ColorData.setStyleSheet(f"background-color: rgb({x},{y},{z}); font-size: 18px; color: black; font-weight: 600; padding: 4px; border: none; border-radius: 10px;")
                        else:
                            self.ColorData.setStyleSheet(f"background-color: rgb({x},{y},{z}); font-size: 18px; color: rgb(200,200,200); font-weight: 600; padding: 4px; border: none; border-radius: 10px;")

                        #
                        feed = FeedBack(Details.get("message"),(70,255,70),self)
                        feed.exec()
                    else:
                        print(Details.get("detail"))
                        feed = FeedBack(Details.get("detail"),(255,70,70),self)
                        feed.exec()

    def OpenBioTab(self):
        self.Changer = BioChanging(self)
        self.Answer = self.Changer.exec()
        if self.Answer:
            bio = self.Changer.TextBox.toPlainText()
            asyncio.create_task(self.ChangeBio(bio))

    async def ChangeBio(self,bio):
            header = {
                "Id":window.User["ID"],
                "Bio": bio,
                "Token":window.User["Token"]
            }
            if bio != window.User["Bio"] and bio.strip():
                response = await asyncio.to_thread(lambda:requests.post("http://" + window.TargetIP + ":8000/api/users/bio",json=header)  )
                #response = requests.post("http://" + window.TargetIP + ":8000/api/users/bio",json=header)  
                Details = response.json()
                if response.status_code == 200:
                    print("all good bio changed")
                    #
                    window.User["Bio"] = Details.get("bio")
                    self.BioData.setText(f"{window.User["Bio"][0:20]}")
                    #
                    feed = FeedBack(Details.get("message"),(70,255,70),self)
                    feed.exec()
                else:
                    print(Details.get("detail"))
                    feed = FeedBack(Details.get("detail"),(255,70,70),self)
                    feed.exec()

    def SoundChanged(self):
        value = self.Edit6.value()
        self.NotifData.setStyleSheet("font-size: 18px; color: rgb(180,180,255); font-weight: 600; border: none; margin-left: 2px;")
        self.NotifData.setText(f"{value}%")
        self.SliderTimer.start()

    def SaveSound(self):
        if self.SliderTimer.isActive():
            self.SliderTimer.stop()
        value = self.Edit6.value()
        self.NotifData.setStyleSheet("font-size: 18px; color: rgb(200,200,200); font-weight: 600; border: none; margin-left: 2px;")
        print(f"saved sound at {value}%")
        window.Settings.setValue("Sound",value/100)
        window.SoundPlayer.setVolume(value/100)

    async def LogOut(self):
        window.UpdBeforeClose()
        header = {
            "Id":window.User["ID"],
            "SessionToken":window.User["Token"]
        }        
        response = await asyncio.to_thread(lambda:requests.post("http://" + window.TargetIP + ":8000/api/logout",json=header)  )
        #response = requests.post("http://" + window.TargetIP + ":8000/api/logout",json=header)  
        Details = response.json()
        if response.status_code == 200:
            print("logout aproved")
            keyring.delete_password("Discus","user") 
            #123f
            #reset EVERYTHING
            window.Friends.clear()
            window.FriendInfo.clear()
            window.FriendRequests.clear()
            window.PendingRequests.clear()
            window.FriendRequestsWidgets.clear()
            window.PendingRequestWidgets.clear()
            window.CurrentId = None
            window.LastMesg = None
            window.PendingCounter = 0 
            window.OnlineCounter = 0 
            window.RequestsCounter = 0 
            window.AllCounter = 0 
            window.AllFriendsWidgets.clear()
            window.MessageHistory.clear()
            window.TempMessages.clear()
            window.PrivChats.clear()
            window.Timestamps.clear()
            #
            window.ClearPriv()
            window.ClearFriendWidgets()
            window.ClearFriendReqWidgets()
            window.ClearPendingReqWidgets()
            window.ClearChatMessages()
            try:
                asyncio.create_task(window.SendMessage(window.User["ID"],"0","0","Disconnect"))
                for a in window.User.keys():
                    if a != "Icon":
                        print(window.User[a])
                try:
                    await window.User["Socket"].close()
                    window.Listening.cancel()
                except:
                    pass
                window.User.clear()
                window.toLogTab()
                self.close()
                print("disconnected from websocket")
            except:
                traceback.print_exc()
        else:
            print(Details.get("detail"))


#By gemini (a spinning circle)
class SimpleSpinner(pyside.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 60)
        self._angle = 0
        
        # Setup animation (0 to 360 degrees, continuously)
        self.anim = QPropertyAnimation(self, b"angle")
        self.anim.setDuration(1000)
        self.anim.setStartValue(0)
        self.anim.setEndValue(360)
        self.anim.setLoopCount(-1) 
        #self.anim.start()

    # Qt needs getter/setter to animate "angle"
    def get_angle(self):
        return self._angle
    
    def set_angle(self, val):
        self._angle = val
        self.update()


    angle = Property(int, get_angle, set_angle)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        

        p.translate(self.width() / 2, self.height() / 2)
        p.rotate(self._angle)
        

        pen = QPen(QColor("#3498db"), 4)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.drawArc(-15, -15, 30, 30, -90 * 16, 270 * 16)
#---
class LoadingBar(pyside.QWidget):
    def __init__(self):
        super().__init__()
        self.Layout = pyside.QGridLayout(self)
        self.ProgressBar = pyside.QProgressBar()
        self.ProgressBar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #2b2b2b;
                text-align: center;
                color: white;
                font-weight: bold;
            }
            QProgressBar::chunk {
                /*background-color: #3498db;*/
                background-color: rgb(180,180,255);
                border-radius: 4px;
            }
        """)
        self.ProgressBar.setTextVisible(False)
        self.ProgressBar.setFixedSize(QSize(300,10))
        self.ProgressBar.setRange(0,100)
        self.ProgressBar.setValue(50)
        self.Layout.addWidget(self.ProgressBar,0,0)

    def setPercentage(self,value):
        self.ProgressBar.setValue(value)

class Unfriend(pyside.QDialog):
    def __init__(self,id,name):
        super().__init__()
        self.setWindowFlags(Qt.WindowFlags.FramelessWindowHint | Qt.WindowFlags.NoDropShadowWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(QSize(450,200))
        self.setStyleSheet("background-color: rgb(30,30,30); border: none;")
        self.setWindowTitle("Delete Friend")
        self.Layout = pyside.QGridLayout(self)
        self.Layout.setSpacing(0)
        self.Layout.setContentsMargins(0,0,0,0)
        #upper bar
        self.UpperBar = pyside.QWidget()
        self.UpperBarLayout = pyside.QGridLayout(self.UpperBar)
        self.UpperBarLayout.setColumnStretch(0,19)
        self.UpperBarLayout.setColumnStretch(1,1)
        self.UpperBar.setStyleSheet("""background-color: rgb(30,30,30); border: none; border-radius: 0px; border-top-left-radius: 10px; border-top-right-radius: 10px;
                                     border-top: 1px solid rgb(100,100,100); border-left: 1px solid rgb(100,100,100); border-right: 1px solid rgb(100,100,100);""")
        self.Layout.addWidget(self.UpperBar,0,0)
        #
        self.BarLabel = pyside.QLabel(f"  Delete {name}?")
        self.BarLabel.setStyleSheet("font-size: 25px; color: rgb(200,200,200); border: none; font-weight: 600;")
        self.UpperBarLayout.addWidget(self.BarLabel,0,0)
        #
        self.CloseBtn = pyside.QPushButton("×")
        self.CloseBtn.setStyleSheet("""QPushButton{background-color: transparent; border-radius: 10px; font-size: 40px; border: none; color: rgb(200,200,200);}
                                        QPushButton:hover{background-color: rgba(200,200,200,0.1);}""")
        self.CloseBtn.setFixedSize(QSize(50,45))
        self.CloseBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.CloseBtn.clicked.connect(self.close)
        self.UpperBarLayout.addWidget(self.CloseBtn,0,1)
        #
        self.BarLabel = pyside.QLabel(f"  Are you sure you want to unfriend {name}?")
        self.BarLabel.setWordWrap(True)
        self.BarLabel.setStyleSheet("font-size: 20px; color: rgb(200,200,200); border: none;")
        self.UpperBarLayout.addWidget(self.BarLabel,1,0)
        #Main
        self.Main = pyside.QWidget()
        self.Main.setObjectName("Main")
        self.Main.setStyleSheet("""#Main{background-color: rgb(30,30,30); border: none; border-radius: 0px; border-bottom-left-radius: 10px; border-bottom-right-radius: 10px;
                                     border-bottom: 1px solid rgb(100,100,100); border-left: 1px solid rgb(100,100,100); border-right: 1px solid rgb(100,100,100);}""")
        self.MainLayout = pyside.QGridLayout(self.Main)
        self.Layout.addWidget(self.Main,2,0)
        #-----
        self.CancelBtn = pyside.QPushButton("Cancel")
        self.CancelBtn.setStyleSheet("""QPushButton{background-color: rgb(40,40,40); border-radius: 10px; padding: 5px; font-size: 25px; border: none; margin: 10px; margin-right: 5px; color: rgb(200,200,200);}
                                        QPushButton:hover{background-color: rgb(60,60,60);}""")
        self.CancelBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.CancelBtn.clicked.connect(self.close)
        self.MainLayout.addWidget(self.CancelBtn,0,0)
        #
        self.SaveBtn = pyside.QPushButton("Delete Friend")
        self.SaveBtn.setStyleSheet("""QPushButton{background-color: rgb(230,40,40); border-radius: 10px; padding: 5px; font-size: 25px; border: none; margin: 10px; margin-left: 5px; color: rgb(200,200,200);}
                                        QPushButton:hover{background-color: rgb(170,40,40);}""")
        self.SaveBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.SaveBtn.clicked.connect(self.accept)
        self.MainLayout.addWidget(self.SaveBtn,0,1)

class Refriend(pyside.QDialog):
    def __init__(self,id,name):
        super().__init__()
        self.setWindowFlags(Qt.WindowFlags.FramelessWindowHint | Qt.WindowFlags.NoDropShadowWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(QSize(450,200))
        self.setStyleSheet("background-color: rgb(30,30,30); border: none;")
        self.setWindowTitle("ReAdd Friend")
        self.Layout = pyside.QGridLayout(self)
        self.Layout.setSpacing(0)
        self.Layout.setContentsMargins(0,0,0,0)
        #upper bar
        self.UpperBar = pyside.QWidget()
        self.UpperBarLayout = pyside.QGridLayout(self.UpperBar)
        self.UpperBarLayout.setColumnStretch(0,19)
        self.UpperBarLayout.setColumnStretch(1,1)
        self.UpperBar.setStyleSheet("""background-color: rgb(30,30,30); border: none; border-radius: 0px; border-top-left-radius: 10px; border-top-right-radius: 10px;
                                     border-top: 1px solid rgb(100,100,100); border-left: 1px solid rgb(100,100,100); border-right: 1px solid rgb(100,100,100);""")
        self.Layout.addWidget(self.UpperBar,0,0)
        #
        self.BarLabel = pyside.QLabel(f"  Add {name}?")
        self.BarLabel.setStyleSheet("font-size: 25px; color: rgb(200,200,200); border: none; font-weight: 600;")
        self.UpperBarLayout.addWidget(self.BarLabel,0,0)
        #
        self.CloseBtn = pyside.QPushButton("×")
        self.CloseBtn.setStyleSheet("""QPushButton{background-color: transparent; border-radius: 10px; font-size: 40px; border: none; color: rgb(200,200,200);}
                                        QPushButton:hover{background-color: rgba(200,200,200,0.1);}""")
        self.CloseBtn.setFixedSize(QSize(50,45))
        self.CloseBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.CloseBtn.clicked.connect(self.close)
        self.UpperBarLayout.addWidget(self.CloseBtn,0,1)
        #
        self.BarLabel = pyside.QLabel(f"  Are you sure you want to friend {name}?")
        self.BarLabel.setWordWrap(True)
        self.BarLabel.setStyleSheet("font-size: 20px; color: rgb(200,200,200); border: none;")
        self.UpperBarLayout.addWidget(self.BarLabel,1,0)
        #Main
        self.Main = pyside.QWidget()
        self.Main.setObjectName("Main")
        self.Main.setStyleSheet("""#Main{background-color: rgb(30,30,30); border: none; border-radius: 0px; border-bottom-left-radius: 10px; border-bottom-right-radius: 10px;
                                     border-bottom: 1px solid rgb(100,100,100); border-left: 1px solid rgb(100,100,100); border-right: 1px solid rgb(100,100,100);}""")
        self.MainLayout = pyside.QGridLayout(self.Main)
        self.Layout.addWidget(self.Main,2,0)
        #-----
        self.CancelBtn = pyside.QPushButton("Cancel")
        self.CancelBtn.setStyleSheet("""QPushButton{background-color: rgb(40,40,40); border-radius: 10px; padding: 5px; font-size: 25px; border: none; margin: 10px; margin-right: 5px; color: rgb(200,200,200);}
                                        QPushButton:hover{background-color: rgb(60,60,60);}""")
        self.CloseBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.CancelBtn.clicked.connect(self.close)
        self.MainLayout.addWidget(self.CancelBtn,0,0)
        #
        self.SaveBtn = pyside.QPushButton("Add Friend")
        self.SaveBtn.setStyleSheet("""QPushButton{background-color: rgb(40,230,40); border-radius: 10px; padding: 5px; font-size: 25px; border: none; margin: 10px; margin-left: 5px; color: rgb(200,200,200);}
                                        QPushButton:hover{background-color: rgb(40,170,40);}""")
        self.SaveBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.SaveBtn.clicked.connect(self.accept)
        self.MainLayout.addWidget(self.SaveBtn,0,1)


# Setting classes

class NameChanging(pyside.QDialog):
    def __init__(self,parent = None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowFlags.FramelessWindowHint | Qt.WindowFlags.NoDropShadowWindowHint | Qt.Dialog)
        self.setWindowModality(Qt.WindowModal)
        self.setFixedSize(QSize(450,400))
        self.setStyleSheet("background-color: rgb(30,30,30); border: 1px solid rgb(100,100,100); border-radius: 10px;")
        self.setWindowTitle("Change Name")
        self.Layout = pyside.QGridLayout(self)
        self.Layout.setSpacing(0)
        self.Layout.setContentsMargins(0,0,0,0)
        self.Layout.setRowStretch(0,1)
        #self.Layout.setRowStretch(1,1)
        self.Layout.setRowStretch(2,22)
        #upper bar
        self.UpperBar = pyside.QWidget()
        self.UpperBarLayout = pyside.QGridLayout(self.UpperBar)
        self.UpperBarLayout.setColumnStretch(0,19)
        self.UpperBarLayout.setColumnStretch(1,1)
        self.UpperBar.setStyleSheet("background-color: transparent; border: none; border-bottom-left-radius: 0px; border-bottom-right-radius: 0px;")
        self.Layout.addWidget(self.UpperBar,0,0)
        #
        self.BarLabel = pyside.QLabel("  Change your username")
        self.BarLabel.setStyleSheet("font-size: 25px; color: rgb(200,200,200); border: none;")
        self.UpperBarLayout.addWidget(self.BarLabel,0,0)
        #
        self.CloseBtn = pyside.QPushButton("×")
        self.CloseBtn.setStyleSheet("""QPushButton{background-color: transparent; border-radius: 10px; font-size: 40px; border: none; color: rgb(200,200,200);}
                                        QPushButton:hover{background-color: rgba(200,200,200,0.1);}""")
        self.CloseBtn.setFixedSize(QSize(50,45))
        self.CloseBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.CloseBtn.clicked.connect(self.close)
        self.UpperBarLayout.addWidget(self.CloseBtn,0,1)
        #
        self.BarLabel = pyside.QLabel("  Enter your new username and your existing password")
        self.BarLabel.setStyleSheet("font-size: 14px; color: rgb(200,200,200); border: none;")
        self.UpperBarLayout.addWidget(self.BarLabel,1,0)
        #Main
        self.Main = pyside.QWidget()
        self.Main.setStyleSheet("background-color: transparent; margin-right: 5px; margin-left: 5px; border: none;")
        self.MainLayout = pyside.QGridLayout(self.Main)
        self.Layout.addWidget(self.Main,2,0)
        #
        self.UserNameLbl = pyside.QLabel("Username")
        self.UserNameLbl.setStyleSheet("font-size: 16px; color: rgb(200,200,200);")
        self.MainLayout.addWidget(self.UserNameLbl,0,0,1,2)
        #
        self.UserFeild = pyside.QLineEdit()
        self.UserFeild.setFixedHeight(40)
        self.UserFeild.setStyleSheet("""QLineEdit{font-size: 18px; border: 2px solid rgb(60,60,60); color: rgb(200,200,200); border-radius: 7px; margin-bottom: 2px;}
                                        QLineEdit:focus{border: 2px solid rgb(100,100,255);}""")
        self.UserFeild.setText(f"{window.User["Name"]}")
        self.MainLayout.addWidget(self.UserFeild,1,0,1,2)
        #
        self.disclamer = pyside.QLabel("Please use letters,numbers,underscores and dots")
        self.disclamer.setStyleSheet("font-size: 11px; color: rgb(200,200,200); font-weight: 600; margin-top: 0px;")
        self.MainLayout.addWidget(self.disclamer,2,0,1,2)
        #
        self.UserPassLbl = pyside.QLabel("Password")
        self.UserPassLbl.setStyleSheet("font-size: 16px; color: rgb(200,200,200);")
        self.MainLayout.addWidget(self.UserPassLbl,3,0,1,2)
        #
        self.PassFeild = pyside.QLineEdit()
        self.PassFeild.setEchoMode(pyside.QLineEdit.EchoMode.Password)
        self.PassFeild.setFixedHeight(57)
        self.PassFeild.setStyleSheet("""QLineEdit{font-size: 18px; border: 2px solid rgb(60,60,60); color: rgb(200,200,200); border-radius: 7px; margin-bottom: 20px;}
                                        QLineEdit:focus{border: 2px solid rgb(100,100,255);}""")
        self.PassFeild.setText("")
        self.MainLayout.addWidget(self.PassFeild,4,0,1,2)
        #
        self.CancelBtn = pyside.QPushButton("Cancel")
        self.CancelBtn.setStyleSheet("""QPushButton{background-color: rgb(40,40,40); border-radius: 10px; font-size: 30px; border: none; margin: 10px; margin-right: 5px; color: rgb(200,200,200);}
                                        QPushButton:hover{background-color: rgb(60,60,60);}""")
        self.CancelBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.CancelBtn.clicked.connect(self.close)
        self.MainLayout.addWidget(self.CancelBtn,5,0)
        #
        self.SaveBtn = pyside.QPushButton("Save")
        self.SaveBtn.setStyleSheet("""QPushButton{background-color: rgb(70,70,255); border-radius: 10px; font-size: 30px; border: none; margin: 10px; margin-left: 5px; color: rgb(200,200,200);}
                                        QPushButton:hover{background-color: rgb(100,100,255);}""")
        self.SaveBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.SaveBtn.clicked.connect(self.accept)
        self.MainLayout.addWidget(self.SaveBtn,5,1)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.Sub()
            event.accept()
        else:
            super().keyPressEvent(event)

    def Sub(self):
        self.accept()

class FeedBack(pyside.QDialog):
    def __init__(self,message,color,parent = None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowFlags.FramelessWindowHint | Qt.WindowFlags.NoDropShadowWindowHint | Qt.Dialog)
        self.setWindowModality(Qt.WindowModal)
        self.setFixedSize(QSize(400,150))
        self.setStyleSheet("background-color: rgb(30,30,30); border: 1px solid rgb(100,100,100); border-radius: 10px;")
        self.setWindowTitle("Feedback")
        self.Layout = pyside.QGridLayout(self)
        self.Layout.setSpacing(0)
        self.Layout.setContentsMargins(0,0,0,0)
        self.Layout.setRowStretch(0,1)
        self.Layout.setRowStretch(1,19)
        #upper bar
        self.UpperBar = pyside.QWidget()
        self.UpperBarLayout = pyside.QGridLayout(self.UpperBar)
        self.UpperBar.setStyleSheet("background-color: transparent; border: none; border-bottom-left-radius: 0px; border-bottom-right-radius: 0px;")
        self.Layout.addWidget(self.UpperBar,0,0)
        #
        self.BarLabel = pyside.QLabel("  Message")
        self.BarLabel.setStyleSheet("font-size: 25px; color: rgb(200,200,200); border: none;")
        self.UpperBarLayout.addWidget(self.BarLabel,0,0)
        #
        self.CloseBtn = pyside.QPushButton("×")
        self.CloseBtn.setStyleSheet("""QPushButton{background-color: transparent; border-radius: 10px; font-size: 40px; border: none; color: rgb(200,200,200);}
                                        QPushButton:hover{background-color: rgba(200,200,200,0.1);}""")
        self.CloseBtn.setFixedSize(QSize(50,45))
        self.CloseBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.CloseBtn.clicked.connect(self.close)
        self.UpperBarLayout.addWidget(self.CloseBtn,0,1)
        #Main
        self.Main = pyside.QWidget()
        self.Main.setStyleSheet("background-color: transparent; margin-right: 5px; margin-left: 5px; border: none;")
        self.MainLayout = pyside.QGridLayout(self.Main)
        self.Layout.addWidget(self.Main,1,0)
        #
        self.UserNameLbl = pyside.QLabel(f"{message}")
        self.UserNameLbl.setWordWrap(True)
        self.UserNameLbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.UserNameLbl.setStyleSheet(f"font-size: 25px; color: rgb({color[0]},{color[1]},{color[2]});")
        self.MainLayout.addWidget(self.UserNameLbl,0,0)

class PassChanging(pyside.QDialog):
    def __init__(self,parent = None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowFlags.FramelessWindowHint | Qt.WindowFlags.NoDropShadowWindowHint | Qt.Dialog)
        self.setWindowModality(Qt.WindowModal)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(QSize(450,470))
        self.setStyleSheet("background-color: rgb(30,30,30); border: 1px solid rgb(100,100,100); border-radius: 10px;")
        self.setWindowTitle("Change Password")
        self.Layout = pyside.QGridLayout(self)
        self.Layout.setSpacing(0)
        self.Layout.setContentsMargins(0,0,0,0)
        self.Layout.setRowStretch(0,1)
        #self.Layout.setRowStretch(1,1)
        self.Layout.setRowStretch(2,22)
        #upper bar
        self.UpperBar = pyside.QWidget()
        self.UpperBarLayout = pyside.QGridLayout(self.UpperBar)
        self.UpperBarLayout.setColumnStretch(0,19)
        self.UpperBarLayout.setColumnStretch(1,1)
        self.UpperBar.setStyleSheet("background-color: rgb(30,30,30); border: 1px solid rgb(100,100,100); border-bottom: none; border-bottom-left-radius: 0px; border-bottom-right-radius: 0px;")
        self.Layout.addWidget(self.UpperBar,0,0)
        #
        self.BarLabel = pyside.QLabel("  Change your Password")
        self.BarLabel.setStyleSheet("font-size: 25px; color: rgb(200,200,200); border: none;")
        self.UpperBarLayout.addWidget(self.BarLabel,0,0)
        #
        self.CloseBtn = pyside.QPushButton("×")
        self.CloseBtn.setStyleSheet("""QPushButton{background-color: transparent; border-radius: 10px; font-size: 40px; border: none; color: rgb(200,200,200);}
                                        QPushButton:hover{background-color: rgba(200,200,200,0.1);}""")
        self.CloseBtn.setFixedSize(QSize(50,45))
        self.CloseBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.CloseBtn.clicked.connect(self.close)
        self.UpperBarLayout.addWidget(self.CloseBtn,0,1)
        #
        self.BarLabel = pyside.QLabel("  Enter your current password and your new password")
        self.BarLabel.setStyleSheet("font-size: 14px; color: rgb(200,200,200); border: none;")
        self.UpperBarLayout.addWidget(self.BarLabel,1,0)
        #Main
        self.Main = pyside.QWidget()
        self.Main.setStyleSheet("background-color: rgb(30,30,30); border: 1px solid rgb(100,100,100); border-top: none; border-top-left-radius: 0px; border-top-right-radius: 0px; ")
        self.MainLayout = pyside.QGridLayout(self.Main)
        self.Layout.addWidget(self.Main,2,0)
        #----
        self.CurPassLbl = pyside.QLabel("Current Password")
        self.CurPassLbl.setStyleSheet("font-size: 16px; color: rgb(200,200,200); border: none;")
        self.MainLayout.addWidget(self.CurPassLbl,0,0,1,2)
        #
        self.CurPassFeild = pyside.QLineEdit()
        self.CurPassFeild.setEchoMode(pyside.QLineEdit.EchoMode.Password)
        self.CurPassFeild.setFixedHeight(40)
        self.CurPassFeild.setStyleSheet("""QLineEdit{font-size: 18px; border: 2px solid rgb(60,60,60); color: rgb(200,200,200); border-radius: 7px; margin-bottom: 2px;}
                                        QLineEdit:focus{border: 2px solid rgb(100,100,255);}""")
        self.MainLayout.addWidget(self.CurPassFeild,1,0,1,2)
        #----
        self.NewPassLbl = pyside.QLabel("New Password")
        self.NewPassLbl.setStyleSheet("font-size: 16px; color: rgb(200,200,200); border: none;")
        self.MainLayout.addWidget(self.NewPassLbl,2,0,1,2)
        #
        self.NewPassFeild = pyside.QLineEdit()
        self.NewPassFeild.setEchoMode(pyside.QLineEdit.EchoMode.Password)
        self.NewPassFeild.setFixedHeight(60)
        self.NewPassFeild.setStyleSheet("""QLineEdit{font-size: 18px; border: 2px solid rgb(60,60,60); color: rgb(200,200,200); border-radius: 7px; margin-bottom: 20px;}
                                        QLineEdit:focus{border: 2px solid rgb(100,100,255);}""")
        self.MainLayout.addWidget(self.NewPassFeild,3,0,1,2)
        #----
        self.CNewPassLbl = pyside.QLabel("Confirm New Password")
        self.CNewPassLbl.setStyleSheet("font-size: 16px; color: rgb(200,200,200); border: none;")
        self.MainLayout.addWidget(self.CNewPassLbl,4,0,1,2)
        #
        self.CNewPassFeild = pyside.QLineEdit()
        self.CNewPassFeild.setEchoMode(pyside.QLineEdit.EchoMode.Password)
        self.CNewPassFeild.setFixedHeight(60)
        self.CNewPassFeild.setStyleSheet("""QLineEdit{font-size: 18px; border: 2px solid rgb(60,60,60); color: rgb(200,200,200); border-radius: 7px; margin-bottom: 20px;}
                                        QLineEdit:focus{border: 2px solid rgb(100,100,255);}""")
        self.MainLayout.addWidget(self.CNewPassFeild,5,0,1,2)

        #-----
        self.CancelBtn = pyside.QPushButton("Cancel")
        self.CancelBtn.setStyleSheet("""QPushButton{background-color: rgb(40,40,40); border-radius: 10px; font-size: 30px; border: none; margin: 10px; margin-right: 5px; color: rgb(200,200,200);}
                                        QPushButton:hover{background-color: rgb(60,60,60);}""")
        self.CancelBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.CancelBtn.clicked.connect(self.close)
        self.MainLayout.addWidget(self.CancelBtn,6,0)
        #
        self.SaveBtn = pyside.QPushButton("Save")
        self.SaveBtn.setStyleSheet("""QPushButton{background-color: rgb(70,70,255); border-radius: 10px; font-size: 30px; border: none; margin: 10px; margin-left: 5px; color: rgb(200,200,200);}
                                        QPushButton:hover{background-color: rgb(100,100,255);}""")
        self.SaveBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.SaveBtn.clicked.connect(self.accept)
        self.MainLayout.addWidget(self.SaveBtn,6,1)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.Sub()
            event.accept()
        else:
            super().keyPressEvent(event)

    def Sub(self):
        self.accept()

class IconChanging(pyside.QDialog):
    def __init__(self,parent = None):
        super().__init__(parent)
        self.ChosenPath = None
        self.setWindowFlags(Qt.WindowFlags.FramelessWindowHint | Qt.WindowFlags.NoDropShadowWindowHint | Qt.Dialog)
        self.setWindowModality(Qt.WindowModal)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(QSize(500,400))
        self.setStyleSheet("background-color: rgb(30,30,30); border: none;")
        self.setWindowTitle("Icon Picture")
        self.Layout = pyside.QGridLayout(self)
        self.Layout.setSpacing(0)
        self.Layout.setContentsMargins(0,0,0,0)
        self.Layout.setRowStretch(0,1)
        #self.Layout.setRowStretch(1,1)
        self.Layout.setRowStretch(2,22)
        #upper bar
        self.UpperBar = pyside.QWidget()
        self.UpperBarLayout = pyside.QGridLayout(self.UpperBar)
        self.UpperBarLayout.setColumnStretch(0,19)
        self.UpperBarLayout.setColumnStretch(1,1)
        self.UpperBar.setStyleSheet("""background-color: rgb(30,30,30); border: none; border-radius: 0px; border-top-left-radius: 10px; border-top-right-radius: 10px;
                                     border-top: 1px solid rgb(100,100,100); border-left: 1px solid rgb(100,100,100); border-right: 1px solid rgb(100,100,100);""")
        self.Layout.addWidget(self.UpperBar,0,0)
        #
        self.BarLabel = pyside.QLabel("  Change your Icon Picture")
        self.BarLabel.setStyleSheet("font-size: 25px; color: rgb(200,200,200); border: none;")
        self.UpperBarLayout.addWidget(self.BarLabel,0,0)
        #
        self.CloseBtn = pyside.QPushButton("×")
        self.CloseBtn.setStyleSheet("""QPushButton{background-color: transparent; border-radius: 10px; font-size: 40px; border: none; color: rgb(200,200,200);}
                                        QPushButton:hover{background-color: rgba(200,200,200,0.1);}""")
        self.CloseBtn.setFixedSize(QSize(50,45))
        self.CloseBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.CloseBtn.clicked.connect(self.close)
        self.UpperBarLayout.addWidget(self.CloseBtn,0,1)
        #
        self.BarLabel = pyside.QLabel("  Select an image from your device")
        self.BarLabel.setStyleSheet("font-size: 14px; color: rgb(200,200,200); border: none;")
        self.UpperBarLayout.addWidget(self.BarLabel,1,0)
        #Main
        self.Main = pyside.QWidget()
        self.Main.setObjectName("Main")
        self.Main.setStyleSheet("""#Main{background-color: rgb(30,30,30); border: none; border-radius: 0px; border-bottom-left-radius: 10px; border-bottom-right-radius: 10px;
                                     border-bottom: 1px solid rgb(100,100,100); border-left: 1px solid rgb(100,100,100); border-right: 1px solid rgb(100,100,100);}""")
        self.MainLayout = pyside.QGridLayout(self.Main)
        self.Layout.addWidget(self.Main,2,0)
        #----
        self.PreviewIcon = CircularImage(Path= window.IconFolder + "Default.png",size=110)
        self.PreviewIcon.setImage(window.User["Icon"])
        self.MainLayout.addWidget(self.PreviewIcon,0,0,1,2,alignment=Qt.AlignmentFlag.AlignHCenter)
        #
        self.Container = pyside.QWidget()
        self.ContaierLayout = pyside.QGridLayout(self.Container)
        self.ContaierLayout.setColumnStretch(0,1)
        self.ContaierLayout.setColumnStretch(1,1)
        self.MainLayout.addWidget(self.Container,1,0,1,2)
        #
        self.SelectImg = pyside.QPushButton(" Select Image ")
        self.SelectImg.setMaximumWidth(180)
        self.SelectImg.setStyleSheet("""QPushButton{background-color: rgb(70,70,255); border-radius: 10px; font-size: 20px; border: none; color: rgb(200,200,200); padding: 4px;}
                                        QPushButton:hover{background-color: rgb(100,100,255);}""")
        self.SelectImg.setCursor(Qt.CursorShape.PointingHandCursor)
        self.SelectImg.clicked.connect(self.OpenFile)
        self.ContaierLayout.addWidget(self.SelectImg,0,0,alignment=Qt.AlignmentFlag.AlignHCenter)
        #
        self.SelectedImg = pyside.QLabel("image.png")
        self.SelectedImg.setStyleSheet("color: rgb(100,100,100); font-size: 20px;")
        self.ContaierLayout.addWidget(self.SelectedImg,0,1)
        

        #-----
        self.CancelBtn = pyside.QPushButton("Cancel")
        self.CancelBtn.setStyleSheet("""QPushButton{background-color: rgb(40,40,40); border-radius: 10px; font-size: 30px; border: none; margin: 10px; margin-right: 5px; color: rgb(200,200,200);}
                                        QPushButton:hover{background-color: rgb(60,60,60);}""")
        self.CancelBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.CancelBtn.clicked.connect(self.close)
        self.MainLayout.addWidget(self.CancelBtn,6,0)
        #
        self.SaveBtn = pyside.QPushButton("Save")
        self.SaveBtn.setDisabled(True)
        self.SaveBtn.setStyleSheet("""QPushButton{background-color: rgb(70,70,255); border-radius: 10px; font-size: 30px; border: none; margin: 10px; margin-left: 5px; color: rgb(200,200,200);}
                                    QPushButton:hover{background-color: rgb(100,100,255);}""")
        self.SaveBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.SaveBtn.clicked.connect(self.accept)
        self.MainLayout.addWidget(self.SaveBtn,6,1)

    def OpenFile(self):
        FilePath, _ = pyside.QFileDialog.getOpenFileName(self,"Select an Image","", "Image Files (*.png *.jpg *.jpeg *.webp)")

        if FilePath:
            self.PreviewIcon.setImage(FilePath)
            *_,image = FilePath.split("/")
            self.SelectedImg.setText(f"{image}")
            if self.PreviewIcon.pixmap.isNull():
                self.SaveBtn.setDisabled(True)
            else:
                self.SaveBtn.setDisabled(False)
                self.ChosenPath = FilePath

class BannerChanging(pyside.QDialog):
    def __init__(self,parent = None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowFlags.FramelessWindowHint | Qt.WindowFlags.NoDropShadowWindowHint | Qt.Dialog)
        self.setWindowModality(Qt.WindowModal)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(QSize(600,550))
        self.setStyleSheet("background-color: rgb(30,30,30); border: none;")
        self.setWindowTitle("Banner Color")
        self.Layout = pyside.QGridLayout(self)
        self.Layout.setSpacing(0)
        self.Layout.setContentsMargins(0,0,0,0)
        self.Layout.setRowStretch(0,1)
        #self.Layout.setRowStretch(1,1)
        self.Layout.setRowStretch(2,22)
        #upper bar
        self.UpperBar = pyside.QWidget()
        self.UpperBarLayout = pyside.QGridLayout(self.UpperBar)
        self.UpperBarLayout.setColumnStretch(0,19)
        self.UpperBarLayout.setColumnStretch(1,1)
        self.UpperBar.setStyleSheet("""background-color: rgb(30,30,30); border: none; border-radius: 0px; border-top-left-radius: 10px; border-top-right-radius: 10px;
                                     border-top: 1px solid rgb(100,100,100); border-left: 1px solid rgb(100,100,100); border-right: 1px solid rgb(100,100,100);""")
        self.Layout.addWidget(self.UpperBar,0,0)
        #
        self.BarLabel = pyside.QLabel("  Change your Banner color")
        self.BarLabel.setStyleSheet("font-size: 25px; color: rgb(200,200,200); border: none;")
        self.UpperBarLayout.addWidget(self.BarLabel,0,0)
        #
        self.CloseBtn = pyside.QPushButton("×")
        self.CloseBtn.setStyleSheet("""QPushButton{background-color: transparent; border-radius: 10px; font-size: 40px; border: none; color: rgb(200,200,200);}
                                        QPushButton:hover{background-color: rgba(200,200,200,0.1);}""")
        self.CloseBtn.setFixedSize(QSize(50,45))
        self.CloseBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.CloseBtn.clicked.connect(self.close)
        self.UpperBarLayout.addWidget(self.CloseBtn,0,1)
        #
        self.BarLabel = pyside.QLabel("  Select a Banner color")
        self.BarLabel.setStyleSheet("font-size: 14px; color: rgb(200,200,200); border: none;")
        self.UpperBarLayout.addWidget(self.BarLabel,1,0)
        #Main
        self.Main = pyside.QWidget()
        self.Main.setObjectName("Main")
        self.Main.setStyleSheet("""#Main{background-color: rgb(30,30,30); border: none; border-radius: 0px; border-bottom-left-radius: 10px; border-bottom-right-radius: 10px;
                                     border-bottom: 1px solid rgb(100,100,100); border-left: 1px solid rgb(100,100,100); border-right: 1px solid rgb(100,100,100);}""")
        self.MainLayout = pyside.QGridLayout(self.Main)
        self.Layout.addWidget(self.Main,2,0)
        #----
        self.ColorPicker = pyside.QColorDialog(currentColor=QColor(255,255,255))
        self.ColorPicker.setWindowTitle("Pick a color")
        self.ColorPicker.setOption(pyside.QColorDialog.ColorDialogOption.DontUseNativeDialog,True)
        self.ColorPicker.setOption(pyside.QColorDialog.ColorDialogOption.NoButtons,True)
        self.ColorPicker.setStyleSheet("""QColorDialog{ color: rgb(200,200,200); border: none;}
                                        QColorDialog QLineEdit{background-color: rgb(50,50,50); color: rgb(200,200,200); border-radius: 2px; border: none;}
                                        QColorDialog QSpinBox{background-color: rgb(50,50,50); color: rgb(200,200,200); border-radius: 2px; border: none;}
                                        QColorDialog QLabel{ color: rgb(200,200,200); border: none;}
                                        QColorDialog QPushButton{ color: rgb(200,200,200); border: none;}
                                        QColorDialog QColorWell{ border: none;}""")
        self.MainLayout.addWidget(self.ColorPicker,0,0,1,2)
        

        #-----
        self.CancelBtn = pyside.QPushButton("Cancel")
        self.CancelBtn.setStyleSheet("""QPushButton{background-color: rgb(40,40,40); border-radius: 10px; font-size: 30px; border: none; margin: 10px; margin-right: 5px; color: rgb(200,200,200);}
                                        QPushButton:hover{background-color: rgb(60,60,60);}""")
        self.CancelBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.CancelBtn.clicked.connect(self.close)
        self.MainLayout.addWidget(self.CancelBtn,6,0)
        #
        self.SaveBtn = pyside.QPushButton("Preview")
        self.SaveBtn.setStyleSheet("""QPushButton{background-color: rgb(70,70,255); border-radius: 10px; font-size: 30px; border: none; margin: 10px; margin-left: 5px; color: rgb(200,200,200);}
                                        QPushButton:hover{background-color: rgb(100,100,255);}""")
        self.SaveBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.SaveBtn.clicked.connect(self.accept)
        self.MainLayout.addWidget(self.SaveBtn,6,1)

class BioChanging(pyside.QDialog):
    def __init__(self,parent = None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowFlags.FramelessWindowHint | Qt.WindowFlags.NoDropShadowWindowHint | Qt.Dialog)
        self.setWindowModality(Qt.WindowModal)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(QSize(450,330))
        self.setStyleSheet("background-color: rgb(30,30,30); border: none;")
        self.setWindowTitle("Bio")
        self.Words = 0
        self.Layout = pyside.QGridLayout(self)
        self.Layout.setSpacing(0)
        self.Layout.setContentsMargins(0,0,0,0)
        self.Layout.setRowStretch(0,1)
        #self.Layout.setRowStretch(1,1)
        self.Layout.setRowStretch(2,22)
        #upper bar
        self.UpperBar = pyside.QWidget()
        self.UpperBarLayout = pyside.QGridLayout(self.UpperBar)
        self.UpperBarLayout.setColumnStretch(0,19)
        self.UpperBarLayout.setColumnStretch(1,1)
        self.UpperBar.setStyleSheet("""background-color: rgb(30,30,30); border: none; border-radius: 0px; border-top-left-radius: 10px; border-top-right-radius: 10px;
                                     border-top: 1px solid rgb(100,100,100); border-left: 1px solid rgb(100,100,100); border-right: 1px solid rgb(100,100,100);""")
        self.Layout.addWidget(self.UpperBar,0,0)
        #
        self.BarLabel = pyside.QLabel("  Change your Bio")
        self.BarLabel.setStyleSheet("font-size: 25px; color: rgb(200,200,200); border: none;")
        self.UpperBarLayout.addWidget(self.BarLabel,0,0)
        #
        self.CloseBtn = pyside.QPushButton("×")
        self.CloseBtn.setStyleSheet("""QPushButton{background-color: transparent; border-radius: 10px; font-size: 40px; border: none; color: rgb(200,200,200);}
                                        QPushButton:hover{background-color: rgba(200,200,200,0.1);}""")
        self.CloseBtn.setFixedSize(QSize(50,45))
        self.CloseBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.CloseBtn.clicked.connect(self.close)
        self.UpperBarLayout.addWidget(self.CloseBtn,0,1)
        #
        self.BarLabel = pyside.QLabel("  Please use appropriate language")
        self.BarLabel.setStyleSheet("font-size: 14px; color: rgb(200,200,200); border: none;")
        self.UpperBarLayout.addWidget(self.BarLabel,1,0)
        #Main
        self.Main = pyside.QWidget()
        self.Main.setObjectName("Main")
        self.Main.setStyleSheet("""#Main{background-color: rgb(30,30,30); border: none; border-radius: 0px; border-bottom-left-radius: 10px; border-bottom-right-radius: 10px;
                                     border-bottom: 1px solid rgb(100,100,100); border-left: 1px solid rgb(100,100,100); border-right: 1px solid rgb(100,100,100);}""")
        self.MainLayout = pyside.QGridLayout(self.Main)
        self.Layout.addWidget(self.Main,2,0)
        #----
        self.Container = pyside.QWidget()
        self.Container.setStyleSheet("background-color: rgb(40,40,40); border-radius: 10px;")
        self.ContainerLayout = pyside.QGridLayout(self.Container)
        self.ContainerLayout.setColumnStretch(0,19)
        self.ContainerLayout.setColumnStretch(1,1)
        self.MainLayout.addWidget(self.Container,0,0,1,2)
        #
        self.TextBox = pyside.QTextEdit()
        self.TextBox.setStyleSheet("font-size: 20px; color: rgb(200,200,200);")
        self.TextBox.textChanged.connect(lambda:self.Count())
        self.ContainerLayout.addWidget(self.TextBox,0,0,1,2)
        #
        self.CounterLabel = pyside.QLabel(f"{self.Words}/100")
        self.CounterLabel.setStyleSheet("font-size: 16px; font-weight: 600; color: rgb(200,200,200);")
        self.ContainerLayout.addWidget(self.CounterLabel,1,1)
        #-----
        self.CancelBtn = pyside.QPushButton("Cancel")
        self.CancelBtn.setStyleSheet("""QPushButton{background-color: rgb(40,40,40); border-radius: 10px; font-size: 30px; border: none; margin: 10px; margin-right: 5px; color: rgb(200,200,200);}
                                        QPushButton:hover{background-color: rgb(60,60,60);}""")
        self.CancelBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.CancelBtn.clicked.connect(self.close)
        self.MainLayout.addWidget(self.CancelBtn,1,0)
        #
        self.SaveBtn = pyside.QPushButton("Save")
        self.SaveBtn.setStyleSheet("""QPushButton{background-color: rgb(70,70,255); border-radius: 10px; font-size: 30px; border: none; margin: 10px; margin-left: 5px; color: rgb(200,200,200);}
                                        QPushButton:hover{background-color: rgb(100,100,255);}""")
        self.SaveBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.SaveBtn.clicked.connect(self.accept)
        self.MainLayout.addWidget(self.SaveBtn,1,1)

    def Count(self):
        if len(self.TextBox.toPlainText()) <= 100:
            self.Words = len(self.TextBox.toPlainText())
            self.CounterLabel.setText(f"{self.Words}/100")
        else:
            if self.TextBox.toPlainText():
                self.TextBox.setText(self.TextBox.toPlainText()[:-1])
                cursor = self.TextBox.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                self.Words = len(self.TextBox.toPlainText())
                self.TextBox.setTextCursor(cursor)
                self.CounterLabel.setText(f"{self.Words}/100")
            else:
                self.Words = 0
                self.CounterLabel.setText(f"{self.Words}/100")

class CircularImage(pyside.QWidget):
    def __init__(self, Path=None, size=80, parent=None):
        super().__init__(parent)
        self.dpr = self.devicePixelRatio()
        self.Size = int(size*self.dpr)
        self.setFixedSize(size, size)
        self.pixmap = None
        
        if Path:
            self.setImage(Path)

    def setImage(self, Path):
        self.pixmap = QPixmap(Path).scaled(self.Size, self.Size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        if self.pixmap.isNull():
            print("pixmap is null pal...retrying")
            self.pixmap = QPixmap()
            self.pixmap.loadFromData(Path)
            self.pixmap = self.pixmap.scaled(self.Size, self.Size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            if self.pixmap.isNull():
                print("still failed")

        self.pixmap.setDevicePixelRatio(self.dpr)
        self.update()

    #From gemini
    def paintEvent(self, event):
        if not self.pixmap:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addEllipse(0, 0, self.width(), self.height())
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, self.pixmap)

class ProfilePreview(pyside.QDialog):
    def __init__(self,parent = None,Color = None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowFlags.FramelessWindowHint | Qt.WindowFlags.NoDropShadowWindowHint | Qt.Dialog)
        self.setWindowModality(Qt.WindowModal)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(QSize(400,300))
        self.setStyleSheet("background-color: rgb(30,30,30); border: none;")
        self.setWindowTitle("Profile Preview")
        self.Layout = pyside.QGridLayout(self)
        self.Layout.setSpacing(0)
        self.Layout.setContentsMargins(0,0,0,0)
        self.Layout.setRowStretch(0,1)
        #self.Layout.setRowStretch(1,1)
        self.Layout.setRowStretch(2,22)
        #upper bar
        self.UpperBar = pyside.QWidget()
        self.UpperBarLayout = pyside.QGridLayout(self.UpperBar)
        self.UpperBarLayout.setColumnStretch(0,19)
        self.UpperBarLayout.setColumnStretch(1,1)
        self.UpperBar.setStyleSheet("""background-color: rgb(30,30,30); border: none; border-radius: 0px; border-top-left-radius: 10px; border-top-right-radius: 10px;
                                     border-top: 1px solid rgb(100,100,100); border-left: 1px solid rgb(100,100,100); border-right: 1px solid rgb(100,100,100);""")
        self.Layout.addWidget(self.UpperBar,0,0)
        #
        self.BarLabel = pyside.QLabel("  Profile Preview")
        self.BarLabel.setStyleSheet("font-size: 25px; color: rgb(200,200,200); border: none;")
        self.UpperBarLayout.addWidget(self.BarLabel,0,0)
        #
        self.CloseBtn = pyside.QPushButton("×")
        self.CloseBtn.setStyleSheet("""QPushButton{background-color: transparent; border-radius: 10px; font-size: 40px; border: none; color: rgb(200,200,200);}
                                        QPushButton:hover{background-color: rgba(200,200,200,0.1);}""")
        self.CloseBtn.setFixedSize(QSize(50,45))
        self.CloseBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.CloseBtn.clicked.connect(self.close)
        self.UpperBarLayout.addWidget(self.CloseBtn,0,1)
        #
        #Main
        self.Main = pyside.QWidget()
        self.Main.setObjectName("Main")
        self.Main.setStyleSheet("""#Main{background-color: rgb(30,30,30); border: none; border-radius: 0px; border-bottom-left-radius: 10px; border-bottom-right-radius: 10px;
                                     border-bottom: 1px solid rgb(100,100,100); border-left: 1px solid rgb(100,100,100); border-right: 1px solid rgb(100,100,100);}""")
        self.MainLayout = pyside.QGridLayout(self.Main)
        self.Layout.addWidget(self.Main,1,0)
        # banner
        if Color is None:
            bits = window.User["Banner"][4:-1]
        else:
            bits = Color
        r,g,b = bits.split(",")
        self.Banner = pyside.QWidget()
        self.BannerL = pyside.QHBoxLayout(self.Banner)
        self.Banner.setFixedHeight(110)
        self.Banner.setSizePolicy(pyside.QSizePolicy.Policy.Expanding,pyside.QSizePolicy.Policy.Maximum)
        self.Banner.setStyleSheet(f"background-color: rgb({int(r)},{int(g)},{int(b)}); border:none; border-radius: 0px; border-top-left-radius: 10px; border-top-right-radius: 10px; margin-bottom:20px; margin-top: 0px;")
        self.MainLayout.addWidget(self.Banner,0,0,1,2)
        #
        self.IconBackground = CircleIcon(self.Main)
        self.IconBackground.move(20,35)
        self.IconBackground.ChangeColor((30,30,30))
        self.IconBackground.setFixedSize(QSize(94,94))
        self.IconBackground.raise_()
        #
        self.UserIcon = CircularImage(parent=self.Main,Path= window.IconFolder + "Default.png")
        self.UserIcon.setImage(window.User["Icon"])
        self.UserIcon.move(27,42)
        self.UserIcon.raise_()

        #-----
        self.CancelBtn = pyside.QPushButton("Cancel")
        self.CancelBtn.setStyleSheet("""QPushButton{background-color: rgb(40,40,40); border-radius: 10px; font-size: 30px; border: none; margin: 10px; margin-right: 5px; color: rgb(200,200,200);}
                                        QPushButton:hover{background-color: rgb(60,60,60);}""")
        self.CancelBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.CancelBtn.clicked.connect(self.close)
        self.MainLayout.addWidget(self.CancelBtn,1,0)
        #
        self.SaveBtn = pyside.QPushButton("Save")
        self.SaveBtn.setStyleSheet("""QPushButton{background-color: rgb(70,70,255); border-radius: 10px; font-size: 30px; border: none; margin: 10px; margin-left: 5px; color: rgb(200,200,200);}
                                        QPushButton:hover{background-color: rgb(100,100,255);}""")
        self.SaveBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.SaveBtn.clicked.connect(self.accept)
        self.MainLayout.addWidget(self.SaveBtn,1,1)
#Main program --------------------------------------------

heart = pyside.QApplication(sys.argv)


loop = QEventLoop(heart)
asyncio.set_event_loop(loop)

window = CreateWindow()
window.show()

pyside.QApplication.instance().aboutToQuit.connect(window.UpdBeforeClose)

loop.call_soon(lambda: asyncio.create_task(window.AutoLogin()))

#sys.exit(heart.exec())

with loop:
    loop.run_forever()
