import sqlite3
connection = sqlite3.connect("betting-EV.db")
cursor = connection.cursor()

async def insertBet(bet_obj):
    cursor.execute(
        """INSERT INTO bets(league, event, date, book, market, bet_name, kelly, qk, odds, fv, num_books, timestamp)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,datetime('now','localtime'))
        """, (bet_obj['League'], bet_obj['Event'], bet_obj['Date'], bet_obj['Sportsbook'], bet_obj['Market'], bet_obj['Bet Name'], bet_obj['Kelly'], bet_obj['QK'], bet_obj['Odds'], bet_obj['Fair Odds'], bet_obj['Books']))
    connection.commit()

async def getAllBets():
    print(cursor.execute("Select * FROM bets").fetchall())

async def resetBets():
    cursor.execute("DELETE FROM bets;")
    connection.commit()