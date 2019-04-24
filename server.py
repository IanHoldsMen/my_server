from http.server import BaseHTTPRequestHandler, HTTPServer
from http import cookies
from urllib.parse import parse_qs
import json
import sys

from card_db import CardDB
from session_store import SessionStore

gSessionStore = SessionStore()

class RequestHandler(BaseHTTPRequestHandler):

    def end_headers(self):
        self.sendCookie()
        self.send_header("Access-Control-Allow-Origin", self.headers["Origin"])
        self.send_header("Access-Control-Allow-Credentials", "true")
        BaseHTTPRequestHandler.end_headers(self)

    def loadCookie(self):
        if "Cookie" in self.headers:
            self.cookie = cookies.SimpleCookie(self.headers["Cookie"])
        else:
            self.cookie = cookies.SimpleCookie()
 
    def sendCookie(self):
        for morsel in self.cookie:
            self.send_header("Set-Cookie", morsel.OutputString())

    def loadSession(self):
        self.loadCookie()
        if "sessionId" in self.cookie:
            # Session ID found in the cookie
            sessionId = self.cookie["sessionId"].value
            self.session = gSessionStore.getSessionData(sessionId)
            if self.session == None:
                # Session ID no longer found in the session store
                # Create a new session ID
                sessionId = gSessionStore.createSession()
                self.session = gSessionStore.getSessionData(sessionId)
                self.cookie["sessionId"] = sessionId
        else:
            # no session ID found in the cookie
            # create a brand new session ID
            sessionId = gSessionStore.createSession()
            self.session = gSessionStore.getSessionData(sessionId)
            self.cookie["sessionId"] = sessionId

    def isLoggedIn(self):
        if "userId" in self.session:
            return True
        return False

    def handleCardsList(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        db = CardDB()
        cards = db.getAllCards()
        self.wfile.write(bytes(json.dumps(cards), "utf-8"))

    def handleCardsCreate(self):
        length = self.headers["Content-length"]
        body = self.rfile.read(int(length)).decode("utf-8")
        print("The text body:", body)
        parsed_body = parse_qs(body)
        print("The parsed body:", parsed_body)

        name = parsed_body["name"][0]
        suit = parsed_body["suit"][0]
        value = parsed_body["value"][0]
        db = CardDB()
        db.createCard(name, suit, value)

        self.send_response(201)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
    
    def handleCardsUpdate(self, id):
        length = self.headers["Content-length"]
        body = self.rfile.read(int(length)).decode("utf-8")
        print("The text body:", body)
        parsed_body = parse_qs(body)
        print("The parsed body:", parsed_body)
        
        db = CardDB()
        card = db.getCard(id)
        if card == None:
            self.handleNotFound()
            
        name = parsed_body["name"][0]
        suit = parsed_body["suit"][0]
        value = parsed_body["value"][0]
        
        db.updateCard(id, name, suit, value)

        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
    
    def handleCardsRetrieve(self, id):
        db = CardDB()
        card = db.getCard(id)

        if card == None:
            self.handleNotFound()
        else:
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(bytes(json.dumps(card), "utf-8"))
    
    def handleCardsDelete(self, id):
        db = CardDB()
        card = db.getCard(id)
        
        if card == None:
            self.handleNotFound()
        else:
            db.deleteCard(id)
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

    def handleNotFound(self):
        self.send_response(404)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(bytes("Not found", "utf-8"))

       
    def do_OPTIONS(self):
        self.loadSession()
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-type")
        self.end_headers()

    def do_DELETE(self):
        self.loadSession()
        parts = self.path.split('/')[1:]
        collection = parts[0]
        if len(parts) > 1:
            id = parts[1]
        else:
            id = None
        
        if collection == "cards":
            if id == None:
                self.handleNotFound()
            else:
                self.handleCardsDelete(id)
        else:
            self.handleNotFound()

    def do_PUT(self):
        self.loadSession()
        parts = self.path.split('/')[1:]
        collection = parts[0]
        if len(parts) > 1:
            id = parts[1]
        else:
            id = None
        
        if collection == "cards":
            if id == None:
                self.handleNotFound()
            else:
                self.handleCardsUpdate(id)
        else:
            self.handleNotFound()

    def do_GET(self):
        self.loadSession()
        parts = self.path.split('/')[1:]
        collection = parts[0]
        if len(parts) > 1:
            id = parts[1]
        else:
            id = None
        
        if collection == "cards":
            if id == None:
                self.handleCardsList()
            else:
                self.handleCardsRetrieve(id)
        else:
            self.handleNotFound()

    
    def do_POST(self):
        self.loadSession()
        if self.path == "/cards":
            self.handleCardsCreate()
        else:
            self.handleNotFound()
    
def run():

    db = CardDB()
    db.createCardTable()
    db = None

    port = 8080
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    listen = ("0.0.0.0", port)
    server = HTTPServer(listen, RequestHandler)

    print("Listening...")
    server.serve_forever()

run()