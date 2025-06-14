import sqlite3
connection = sqlite3.connect("betting-EV.db")
cursor = connection.cursor()

async def insertBet(bet_obj):
    try:
        cursor.execute(
            """INSERT INTO bets(id, league, event, date, book, market, bet_name, kelly, qk, odds, fv, num_books, timestamp)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,datetime('now','localtime'))
            """, (bet_obj['id'], bet_obj['League'], bet_obj['Event'], bet_obj['Date'], bet_obj['Sportsbook'], bet_obj['Market'], bet_obj['Bet Name'], bet_obj['Kelly'], bet_obj['QK'], bet_obj['Odds'], bet_obj['Fair Odds'], bet_obj['Books']))
        connection.commit()
        return True
    except sqlite3.Error as e:
         print(e)
         print('Already have this entry or Error')
         return False

async def getAllBets():
    allBets = cursor.execute("Select id FROM bets").fetchall()
    print(allBets)
    return allBets

async def resetBets():
    cursor.execute("DELETE FROM bets;")
    connection.commit()

async def deleteBet(id):
    print('deleting bet id')
    cursor.execute("DELETE FROM bets WHERE id = '"+id+"'")
    print("Deleted bet with id: "+id)
    connection.commit()

async def getBet(id):
    cursor.execute("Select * FROM bets WHERE id = '"+id+"'")