import sqlite3

connection = sqlite3.connect("betting-EV.db")

cursor = connection.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS bets (league TEXT, event TEXT, date TEXT, book TEXT, market TEXT, bet_name TEXT, kelly REAL, qk REAL, odds TEXT, fv TEXT, num_books INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")


cursor.execute("""INSERT INTO bets VALUES 
               ('MLB', 'Miami Marlins @ New York Mets', 'Today at 7:10 PM', 'FanDuel', 'Player Total Bases', 'Brandon Nimmo Over 1.5', 3.64, 0.36, '+160', '+154', 4, datetime('now','localtime'))
               """)
connection.commit()

print("DB Initialized")