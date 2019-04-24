import os
import psycopg2
import psycopg2.extras
import urllib.parse

class CardDB:

    def __init__(self):
        urllib.parse.uses_netloc.append("postgres")
        url = urllib.parse.urlparse(os.environ["DATABASE_URL"])

        self.connection = psycopg2.connect(
            cursor_factory=psycopg2.extras.realDictConstructor,
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )

        self.cursor = self.connection.cursor()

    def __del__(self):
        self.connection.close()

    def createCardTable(self):
        self.cursor.execute("CREATE TABLE IF NOT EXISTS cards (id SERIAL PRIMARY KEY, name VARCHAR(255), suit VARCHAR(255), value INTEGER)")
        self.connection.commit()
    
    def createCard(self, name, suit, value):
        self.cursor.execute("INSERT INTO cards (name, suit, value) VALUES (%s, %s, %s)", (name, suit, value))
        self.connection.commit()
        return
    
    def getAllCards(self):
        self.cursor.execute("SELECT * FROM cards")
        return self.cursor.fetchall()

    def getCard(self, id):
        self.cursor.execute("SELECT  * FROM cards WHERE id = %s", (id,))
        return self.cursor.fetchone()
    
    def deleteCard(self, id):
        self.cursor.execute("DELETE FROM cards WHERE id = %s", (id,))
        self.connection.commit()
        return
    
    def updateCard(self, id, name, suit, value):
        self.cursor.execute("UPDATE cards SET name = %s, suit = %s, value = %s WHERE id = %s", (name, suit, value, id))
        self.connection.commit()
        return