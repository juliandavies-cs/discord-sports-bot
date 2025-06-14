import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import discord
from discord.ext import commands 
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from discord.ext import tasks

from src import backend
from sql import init

import time
import json
from dotenv import load_dotenv

load_dotenv()

token = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix=".", intents=discord.Intents.all())
driver = webdriver.Chrome()
wait = WebDriverWait(driver, 10)

driver.get('https://crazyninjaodds.com/site/tools/positive-ev.aspx')

def main():
    # Set up
    backend.resetBets();

    props = driver.find_elements(By.LINK_TEXT, 'here')
    props[1].click()
    time.sleep(2)

    faq = wait.until(EC.element_to_be_clickable(driver.find_element(By.PARTIAL_LINK_TEXT, 'FAQ')))
    faq.click()
    time.sleep(2)

    # Open the webpage
    driver.get('https://crazyninjaodds.com/site/account/settings.aspx')

    radio = wait.until(EC.element_to_be_clickable(driver.find_element(By.ID, 'ContentPlaceHolderMain_ContentPlaceHolderRight_RadioButtonListIsMain_2')))
    radio.click()

    list_sites = driver.find_elements(By.XPATH, '//label[contains(@for,"ContentPlaceHolderMain_ContentPlaceHolderRight_CheckBoxListSportsbookSites")]')
    for site in list_sites:
        if site.text != 'FanDuel' and site.text != 'BetMGM' and site.text != 'DraftKings' and site.text != 'ESPN Bet' and site.text != 'Caesars':
            parent = site.find_element(By.XPATH, '..')
            checkbox = parent.find_element(By.XPATH, './input')
            checkbox.click()

    min_EV = driver.find_element(By.NAME, 'ctl00$ctl00$ContentPlaceHolderMain$ContentPlaceHolderRight$TextBoxMinimumEVPercentage')
    min_EV.clear()
    min_EV.send_keys('2%') 

    bankroll = driver.find_element(By.NAME, 'ctl00$ctl00$ContentPlaceHolderMain$ContentPlaceHolderRight$TextBoxKellyBankroll')
    bankroll.clear()
    bankroll.send_keys('$5000')

    kellyX = driver.find_element(By.NAME, 'ctl00$ctl00$ContentPlaceHolderMain$ContentPlaceHolderRight$TextBoxKellyMultiplier')
    kellyX.clear()
    kellyX.send_keys('0.25')

    minBooks = driver.find_element(By.NAME, 'ctl00$ctl00$ContentPlaceHolderMain$ContentPlaceHolderRight$TextBoxMinimumOddsProviderCount')
    minBooks.clear()
    minBooks.send_keys('5')

    save = driver.find_element(By.ID, 'ContentPlaceHolderMain_ContentPlaceHolderRight_ButtonSaveSettings')
    save.click()
    time.sleep(5)

    driver.get('https://crazyninjaodds.com/site/tools/positive-ev.aspx')

    minOdds = wait.until(EC.element_to_be_clickable(driver.find_element(By.NAME, 'ctl00$ctl00$ContentPlaceHolderMain$ContentPlaceHolderRight$WebUserControl_FilterMinimumOdds$TextBoxMinimumOdds')))
    minOdds.send_keys('-200') #150

    maxOdds = wait.until(EC.element_to_be_clickable(driver.find_element(By.NAME, 'ctl00$ctl00$ContentPlaceHolderMain$ContentPlaceHolderRight$WebUserControl_FilterMaximumOdds$TextBoxMaximumOdds')))
    maxOdds.send_keys('500') # 150

    startIn = wait.until(EC.element_to_be_clickable(driver.find_element(By.NAME, 'ctl00$ctl00$ContentPlaceHolderMain$ContentPlaceHolderRight$WebUserControl_FilterMaximumDateHours$TextBoxMaximumDateHours')))
    startIn.send_keys('5')
    time.sleep(2)


    msgData = []
    # Setup done
    @tasks.loop(seconds=60.0)
    async def pollData():
        await backend.getAllBets()
        try: 
            button = wait.until(EC.element_to_be_clickable(driver.find_element(By.ID, 'ContentPlaceHolderMain_ContentPlaceHolderRight_ButtonUpdate')))
            button.click()
            print('clicked')

            time.sleep(5) # wait for entries to populate

            newData = []
            newDataId = []
            entries = driver.find_elements(By.CLASS_NAME, 'footable-row-detail')
            for entry in entries:
                calc = wait.until(EC.element_to_be_clickable(entry.find_element(By.XPATH, './/input[@value="Calc"]')))
                calc.click();
                
                qk = driver.find_element(By.ID, 'PopupCalc_KellyUnits').text
                kelly = driver.find_element(By.ID, 'PopupCalc_KellyWager').text

                closeKelly = wait.until(EC.element_to_be_clickable(driver.find_element(By.NAME, 'ctl00$ctl00$ContentPlaceHolderMain$ContentPlaceHolderRight$btnClose')))
                closeKelly.click();

                # Initialize an empty dictionary to hold key-value pairs
                data_dict = {}
                
                # Split the input string by newline to get individual lines
                lines = entry.text.strip().split('\n')
                
                # Process each line
                for line in lines:
                    # Split the line into key and value parts
                    key, value = line.split(' :', 1)  # Limit the split to 1 occurrence
                    if key != 'Calc' and key != 'PHR Calc':
                        data_dict[key.strip()] = value.strip()  # Strip any extra spaces
                
                data_dict['Kelly'] = kelly
                data_dict['QK'] = qk
                if(data_dict['Sportsbook'] == "ESPN Bet"):
                    data_dict['Sportsbook'] = "theScore"
                id = str(hash(json.dumps(data_dict)))
                data_dict['id'] = id
                newData.append(data_dict)
                newDataId.append(id)
                inserted = await backend.insertBet(data_dict);

                if(inserted):
                    embed = discord.Embed(
                        colour=discord.Color.dark_teal(),
                        title=data_dict['Event']+' | '+data_dict['Date']
                    );
                    embed.add_field(name="Sportsbook", value=data_dict['Sportsbook'], inline=False)
                    embed.add_field(name="Bet", value=data_dict['Market']+' , '+data_dict['Bet Name'], inline=False)
                    embed.add_field(name="Bet Size", value='QK: '+data_dict['QK']+'\nKelly: '+data_dict['Kelly']+'\nOdds: '+data_dict['Odds'], inline=True)
                    embed.add_field(name="Stats", value='Fair Odds: '+data_dict['Fair Odds']+'\nBooks: '+data_dict['Books'], inline=False)
                    match data_dict['Sportsbook']:
                        case "FanDuel":
                            embed.add_field(name="Alert!", value='<@&1287390080176099348>')
                        case "DraftKings":
                            embed.add_field(name="Alert!", value='<@&1287390272162103390>')
                        case "BetMGM":
                            embed.add_field(name="Alert!", value='<@&1287390318559232032>')
                        case "theScore":
                            embed.add_field(name="Alert!", value='<@&1287390342882263050>')
                        case "Caesars":
                            embed.add_field(name="Alert!", value='<@&1308573710986510386>')   

                    match data_dict['League']:
                        case "MLB":
                            msg = await mlb_channel.send(embed=embed)
                            msgData.append({"msg_id": msg.id, "data_id": id, "data": data_dict})
                        case "WNBA":
                            msg = await wnba_channel.send(embed=embed)
                            msgData.append({"msg_id": msg.id, "data_id": id, "data": data_dict})
                        case "NHL":
                            msg = await nhl_channel.send(embed=embed)
                            msgData.append({"msg_id": msg.id, "data_id": id, "data": data_dict})
                        case "NFL":
                            msg = await nfl_channel.send(embed=embed)
                            msgData.append({"msg_id": msg.id, "data_id": id, "data": data_dict})
                        case "NCAAF":
                            msg = await ncaaf_channel.send(embed=embed)
                            msgData.append({"msg_id": msg.id, "data_id": id, "data": data_dict})
                        case "NBA":
                            msg = await nba_channel.send(embed=embed)
                            msgData.append({"msg_id": msg.id, "data_id": id, "data": data_dict})
                        case "NCAAB":
                            msg = await ncaab_channel.send(embed=embed)
                            msgData.append({"msg_id": msg.id, "data_id": id, "data": data_dict})
                        case _:
                            print("no sport match")
            """
            for msg in msgData[:]:
                for data in newData:
                    if msg["data"]['League'] == data['League'] and msg["data"]['Event'] == data['Event'] and msg["data"]['Market'] == data['Market'] and msg["data"]['Bet Name'] == data['Bet Name'] and msg["data"]['Sportsbook'] == data['Sportsbook'] and data not in oldData6:
                        print('Pinging this entry/updated')
                        oldData6.append(data)

                        embed = discord.Embed(
                            colour=discord.Color.dark_teal(),
                            title=data['Event']+' | '+data['Date']
                        );
                        embed.add_field(name="Sportsbook", value=data['Sportsbook'], inline=False)
                        embed.add_field(name="Bet", value=data['Market']+' , '+data['Bet Name'], inline=False)
                        embed.add_field(name="Bet Size", value='QK: '+data['QK']+'\nKelly: '+data['Kelly']+'\nOdds: '+data['Odds'], inline=True)
                        embed.add_field(name="Stats", value='Fair Odds: '+data['Fair Odds']+'\nBooks: '+data['Books'], inline=False)
                        match data['Sportsbook']:
                            case "FanDuel":
                                embed.add_field(name="Alert!", value='<@&1287390080176099348>')
                            case "DraftKings":
                                embed.add_field(name="Alert!", value='<@&1287390272162103390>')
                            case "BetMGM":
                                embed.add_field(name="Alert!", value='<@&1287390318559232032>')
                            case "theScore":
                                embed.add_field(name="Alert!", value='<@&1287390342882263050>')
                            case "Caesars":
                                embed.add_field(name="Alert!", value='<@&1308573710986510386>')   

                        match data['League']:
                            case "MLB":
                                msg = await mlb_channel.send(embed=embed)
                                msgData.append({"msg_id": msg.id, "data": data})
                            case "WNBA":
                                msg = await wnba_channel.send(embed=embed)
                                msgData.append({"msg_id": msg.id, "data": data})
                            case "NHL":
                                msg = await nhl_channel.send(embed=embed)
                                msgData.append({"msg_id": msg.id, "data": data})
                            case "NFL":
                                msg = await nfl_channel.send(embed=embed)
                                msgData.append({"msg_id": msg.id, "data": data})
                            case "NCAAF":
                                msg = await ncaaf_channel.send(embed=embed)
                                msgData.append({"msg_id": msg.id, "data": data})
                            case "NBA":
                                msg = await nba_channel.send(embed=embed)
                                msgData.append({"msg_id": msg.id, "data": data})
                            case "NCAAB":
                                msg = await ncaab_channel.send(embed=embed)
                                msgData.append({"msg_id": msg.id, "data": data})
                            case _:
                                print("no sport match")
            for data in oldData6[:]:
                if data not in newData:
                    if data in oldData:
                        oldData.remove(data)
                    if data in oldData2:
                        oldData2.remove(data)
                    if data in oldData3:
                        oldData3.remove(data)
                    if data in oldData4:
                        oldData4.remove(data)
                    if data in oldData5:
                        oldData5.remove(data)
                    if data in oldData6:
                        oldData6.remove(data)
            """
            allBets = (await backend.getAllBets())
            for id in allBets[:]:
                id = "".join(id)
                if id not in newDataId:
                    await backend.deleteBet(id)
                    for msg in msgData[:]:
                        if msg["data_id"] == id:
                            print("deleting message")
                            await deleteMessage(msg)       

        except Exception as e:
            print(str(e))

    @bot.event
    async def on_ready():
        print("Bot Ready")

        #initialize global channels
        global mlb_channel, wnba_channel, nhl_channel, nfl_channel, ncaaf_channel, nba_channel, ncaab_channel
        mlb_channel = bot.get_channel(int(os.getenv('mlb_channel')))
        wnba_channel = bot.get_channel(int(os.getenv('wnba_channel')))
        nhl_channel = bot.get_channel(int(os.getenv('nhl_channel')))
        nfl_channel = bot.get_channel(int(os.getenv('nfl_channel')))
        ncaaf_channel = bot.get_channel(int(os.getenv('ncaaf_channel')))
        nba_channel = bot.get_channel(int(os.getenv('nba_channel')))
        ncaab_channel = bot.get_channel(int(os.getenv('ncaab_channel')))

        pollData.start();

    async def deleteMessage(msg):
        match msg["data"]['League']:
            case 'MLB':
                fetch_msg = await mlb_channel.fetch_message(msg["msg_id"])
                await fetch_msg.delete()
                msgData.remove(msg)
            case 'WNBA':
                fetch_msg = await wnba_channel.fetch_message(msg["msg_id"])
                await fetch_msg.delete()
                msgData.remove(msg)
            case 'NHL':
                fetch_msg = await nhl_channel.fetch_message(msg["msg_id"])
                await fetch_msg.delete()
                msgData.remove(msg)
            case 'NFL':
                fetch_msg = await nfl_channel.fetch_message(msg["msg_id"])
                await fetch_msg.delete()
                msgData.remove(msg)
            case 'NCAFF':
                fetch_msg = await ncaaf_channel.fetch_message(msg["msg_id"])
                await fetch_msg.delete()
                msgData.remove(msg)
            case 'NBA':
                fetch_msg = await nba_channel.fetch_message(msg["msg_id"])
                await fetch_msg.delete()
                msgData.remove(msg)
            case 'NCAAB':
                fetch_msg = await ncaab_channel.fetch_message(msg["msg_id"])
                await fetch_msg.delete()
                msgData.remove(msg)
            case _:
                    print("no sport match")

if __name__ == "__main__":
    main()
    bot.run(token)


