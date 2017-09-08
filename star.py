import datetime
import math
import praw
import re
import requests
import sqlite3
import time
import warnings
from datetime import date
from smite import Endpoint
from smite import SmiteClient
from lxml import html

warnings.simplefilter("ignore", ResourceWarning)
warnings.simplefilter("ignore", UserWarning)
secretinfo = open("secret.txt").read().splitlines()

APP_URI = secretinfo[0]
USER_AGENT = secretinfo[1]

SMITE_APP_ID = secretinfo[2]
SMITE_APP_SECRET = secretinfo[3]
SMITE_APP_REFRESH = secretinfo[4]
PALADINS_APP_ID = secretinfo[5]
PALADINS_APP_SECRET = secretinfo[6]
PALADINS_APP_REFRESH = secretinfo[7]
smite = SmiteClient(secretinfo[8], secretinfo[9])

SUBREDDIT = ""
DATALOGFILE = "datalog.txt"
SMITEFLAIRPRINTFILE = "smiteuserflairs.txt"
PALADINSFLAIRPRINTFILE = "paladinsuserflairs.txt"
r = praw.Reddit(USER_AGENT)

MAXPOSTS = 100
WAIT = 30

datalogTimestamp = True

SmiteStatus = "| [Operational](http://status.hirezstudios.com#/operational) | [Operational](http://status.hirezstudios.com#/operational) | [Operational](http://status.hirezstudios.com#/operational)"
PaladinsStatus = "| [Operational](http://status.hirezstudios.com#/operational) | [Operational](http://status.hirezstudios.com#/operational) | [Operational](http://status.hirezstudios.com#/operational)"
rankingList = ["", "bronze5", "bronze4", "bronze3", "bronze2", "bronze1", "silver5", "silver4", "silver3", "silver2", "silver1", "gold5", "gold4", "gold3", "gold2", "gold1", "platinum5", "platinum4", "platinum3", "platinum2", "platinum1", "diamond5", "diamond4", "diamond3", "diamond2", "diamond1", "master", "grandmaster"]
rankingListFormatted = ["Qualifying", "Bronze V", "Bronze IV", "Bronze III", "Bronze II", "Bronze I", "Silver V", "Silver IV", "Silver III", "Silver II", "Silver I", "Gold V", "Gold IV", "Gold III", "Gold II", "Gold I", "Platinum V", "Platinum IV", "Platinum III", "Platinum II", "Platinum I", "Diamond V", "Diamond IV", "Diamond III", "Diamond II", "Diamond I", "Master", "Gramdmaster"]
rankingListShort = ["Q", "BV", "BIV", "BIII", "BII", "BI", "SV", "SIV", "SIII", "SII", "SI", "GV", "GIV", "GIII", "GII", "GI", "PV", "PIV", "PIII", "PII", "PI", "DV", "DIV", "DIII", "DII", "DI", "M", "GM"]
regionFlagsDictionary = {"North America": "na", "Europe": "eu", "Oceania": "oce", "Brazil": "bra", "Latin America North": "sa", "Southeast Asia": "sea", "China": "chi", "Russia": "rus"}

STATUS_TO_CSS_CLASS_MAP = {
    'Operational' : 'operational',
    'Degraded Performance' : 'issue',
    'Partial Outage' : 'issue',
    'Major Outage' : 'down',
    'Maintenance' : 'maintenance'
}

FLAIRTEXTSUBJECTLINE = ["flairtext", "re: flairtext"]
TIER5SUBJECTLINE = ["tier5", "re: tier5"]
LINKACCOUNTSUBJECTLINE = ["accountlink", "re: accountlink", "linkaccount", "re: linkaccount"]
MASTERYSUBJECTLINE = ["masteryflair", "re: masteryflair"]
LEVELSUBJECTLINE = ["levelflair", "re: levelflair"]
COMPETITIVESUBJECTLINE = ["competitiveflair", "re: competitiveflair", "rankedflair", "re: rankedflair", "rankflair", "re: rankflair"]
DIAMONDSUBJECTLINE = ["diamondflair", "re: diamondflair"]
SAVEFILESUBJECTLINE = ["savefile", "re: savefile"]
LOADFILESUBJECTLINE = ["loadfile", "re: loadfile"]
VIEWFILESUBJECTLINE = ["viewfile", "re: viewfile"]
SCAVENGERSUBJECTLINE = ["scavengerhunt", "re: scavengerhunt"]
SCAVENGERFLAIRSUBJECTLINE = ["scavengerflair", "re: scavengerflair"]
EASTERCODESSUBJECTLINE = ["easteregg", "re: easteregg"]
TESTEASTERSUBJECTLINE = ["testeaster", "re: testeaster"]
EASTERINFOSUBJECTLINE = ["easterinfo", "re: easterinfo"]
EASTERFLAIRSUBJECTLINE = ["easterflair", "re: easterflair"]

seasontickethelp = ["!seasontickethelp", "!helpseasonticket", "!helpticket", "!tickethelp", "!seasonticket"]
starhelp = ["!star", "!starhelp", "!starinfo", "!starinformation", "!smiterobot", "!/u/smiterobot", "!paladinsrobot", "!/u/paladinsrobot"]

MESSAGE_GENERAL_INCORRECT = """
I'm sorry, I do not recognise this request. Please check [this](https://www.reddit.com/r/Smite/wiki/star) page for a complete guide on all my functions and the correct syntax with which to request them.
"""
MESSAGE_SUCCESS = """
Your flair has been set to "_newflair_"
"""
MESSAGE_TOOLONG = """
That flair is too long. It contains {length}/64 characters. Please try again.
"""
MESSAGE_TIER5_EXPIRED = """
The promotional period for this flair is over. Please join us again next year for the next tier 5 flair.
"""
MESSAGE_TIER5_INCORRECT = """
You have not provided the correct information. Please provide your IGN on the first line and your requested flair text on the second line.
"""
MESSAGE_ZERO_FLAIR = """
Please ensure you have a flair equipped before attempting to augment it with mastery, account level, or competitive ranking. You can select a flair from the sidebar.
"""
MESSAGE_MASTERY_SUCCESS = """
You are rank {rank} on {champion}. Your mastery flair was authorised.
"""
MESSAGE_LEVEL_SUCCESS = """
You are level {level}. Your level flair was authorised.
"""
MESSAGE_COMPETITIVE_SUCCESS = """
Your are ranked {rank}. Your competitive flair was authorised.
"""
MESSAGE_DIAMOND_SUCCESS = """
You have _number_ woshippers on _god_ on _platform_. Your diamond flair was authorised.
"""
MESSAGE_DIAMOND_INCORRECT = """
You have not provided the correct information. Please write either `PC`, `XBOX`, or `PS4` on the first line, and your in-game name or gamertag on the second line.
"""
MESSAGE_DIAMOND_SORRY = """
You only have _number_ woshippers on _god_ on _platform_. You need at least 1,000 for a Diamond flair.
"""
MESSAGE_IGN = """
Your username, '{ign}' was not found in our database. If you believe this statement is incorrect, please message the moderators for manual verification.
"""
MESSAGE_LINK_SUCCESS = """
Your account, `{ign}` was successfully linked.

ID: `{id}`, created `{date}`.
"""
MESSAGE_NOT_LINKED = """
Your reddit account has not been linked to your Paladins account. See [here](https://www.reddit.com/r/DrYoshiyahu/wiki/star/accountlink) for instructions on how to link your accounts.
"""
MESSAGE_OOPS = """
Something went wrong! If your account is not hidden, and the syntax for the message was correct, Smite's servers may be down, or they may not recognise the existance of the account.
"""
MESSAGE_OOPS2 = """
Something went wrong! Your platform is "_platform_" and your in-game name is "_IGN_". If your account is not hidden, and the syntax for the message was correct, Smite's servers may be down, or they may not recognise the existance of the account.
"""
MESSAGE_OOPS3 = """
Something went wrong! You listed your in-game name as `{IGN}` and your platform as `{platform}`. If this is correct, Paladins' servers may be having issues. Please contact /u/DrYoshiyahu if you believe this is a mistake.
"""
MESSAGE_OOPS4 = """
Something went wrong! Ensure your account is [linked](https://www.reddit.com/r/DrYoshiyahu/wiki/star/accountlink) and try again.
"""
MESSAGE_MASTERY_WRONGFLAIR = """
Please check that your current flair includes the image of a {character}. Contact /u/DrYoshiyahu if you believe this is a mistake.
"""
MESSAGE_LEVEL_TOO_LOW = """
Your account level is too low. Please try again when your account is at least level 15.
"""
MESSAGE_FILE_INCORRECT = """
You tried to access a file called "_messagebody_". Please try again with either "A", "B", "C", "D", or "E".
"""
MESSAGE_FILE_UNAVAILABLE = """
A savefile for this account could not be found.
"""
MESSAGE_FILE_ERROR = """
Please ensure you have a flair equipped before attempting to save your flair.
"""
MESSAGE_SAVEFILE_SUCCESS = """
Your flair was saved in file _messagebody_. {fileoverview}
"""
MESSAGE_LOADFILE_SUCCESS = """
Your flair was loaded from file _messagebody_. {fileoverview}
"""
MESSAGE_VIEWFILE_SUCCESS = """
You have the following flairs saved:

* **A: _classa_**
 * _texta_
* **B: _classb_**
 * _textb_
* **C: _classc_**
 * _textc_
* **D: _classd_**
 * _textd_
* **E: _classe_**
 * _texte_
"""
MESSAGE_SEASONTICKETHELP = """
You have _days_ days left until SWC 2017 is over. You need to earn the following amounts of Fantasy Points in order to receive the corresponding reward:

* 5,000 FP - _5knumber_ FP per day.
* 10,000 FP - _10knumber_ FP per day.
* 15,000 FP - _15knumber_ FP per day.
* 20,000 FP - _20knumber_ FP per day.
"""
MESSAGE_STARINFO = """
Hello, I am S.T.A.R., the Subreddit Technical Administration Robot. I can:

 * Grant you a verified mastery flair.
 * Save your exclusive and limited flairs for later.
 * Change your flair text without you losing your special flair.

Please see [my wiki page](https://www.reddit.com/r/DrYoshiyahu/wiki/star) for complete documentation on how you can make the most of my services.
"""
MESSAGE_EVENT_EXPIRED = """
The promotional period for this event is over. Thank you for participating!
"""
MESSAGE_SCAVENGER_SUCCESS = """
You have successfully redeemed code **"{codeName}"**. ({code})

{percentage}% of users have found this code.

You have collected {number}/100 codes!{achievement}

{footer}
"""
MESSAGE_EASTER_INCORRECT = """
This code: {code} is invalid. Please check the code and try again.

{footer}
"""
MESSAGE_EASTER_ERROR = """
Something went wrong! Either a code could not be identified in the message you sent, or there was an unexpected error. Please check the message and try again.

{footer}
"""
MESSAGE_EASTER_INFO = """
You have collected {number}/150 codes for /r/{subreddit}!

Here is an overview of your egg collection:

Name|Rarity
:--|:--
{info}

***

*By receiving this message, you have automatically redeemed the "More Information" egg, congratulations!*

{footer}
"""
MESSAGE_EASTER_OOPS = """
Something went wrong! Please wait and try again later.
"""
MESSAGE_SCAVENGER_FOOTER = """
***

**Confused?**

[Announcement Post](https://redd.it/69m2ns) - [Redeem your 100k flair](https://www.reddit.com/message/compose/?to=SmiteRobot&subject=scavengerflair&message=Insert%20flair%20text%20here.) - [Report a Bug](https://www.reddit.com/message/compose/?to=SmiteRobot&subject=scavengerhunt&message=This+is+an+code+for+the+Great+%2Fr%2FSmite+Scavenger+Hunt%21%0D%0AClick+%22send%22+to+add+this+%E2%9A%A1+to+your+collection%3A%0D%0A%0D%0AESTR-S22N-QVGU-MUHS%0A%0A***%0A%0AIf%20you%20really%20do%20have%20a%20bug%20to%20report%2C%20simply%20message%20%2Fu%2FDrYoshiyahu.)
"""
MESSAGE_EASTER_FOOTER = """
***

**Confused?**

[Announcement Post](https://redd.it/61siig) - [Discord Channel](https://discord.gg/ejPm42F) - [Complete Statistics](https://www.reddit.com/message/compose/?to=PaladinsRobot&subject=easterinfo&message=Click%20%22send%22%20for%20a%20list%20of%20every%20egg%20and%20a%20rarity%20value%2C%20in%20the%20form%20of%20a%20percentage%20of%20participants%20that%20have%20found%20the%20egg.) - [Redeem your Easter flair](https://www.reddit.com/message/compose/?to=PaladinsRobot&subject=easterflair&message=Insert%20flair%20text%20here.) - [Report a Bug](https://www.reddit.com/message/compose/?to=PaladinsRobot&subject=easteregg&message=This%20is%20an%20easter%20egg%20for%20the%20Great%202017%20%2Fr%2FPaladins%20Easter%20Egg%20Hunt!%0AClick%20%22send%22%20to%20add%20this%20egg%20to%20your%20collection%3A%0A%0AESTR-PA9C-KZTE-CBF4%0A%0A***%0A%0AIf%20you%20really%20do%20have%20a%20bug%20to%20report%2C%20simply%20message%20%2Fu%2FDrYoshiyahu.)
"""
MESSAGE_EASTER_50ACHIEVEMENT = """


*Congratulations! For finding 50 codes, you have unlocked the limited edition 100k subscriber user flair!*
"""
MESSAGE_EASTER_100ACHIEVEMENT = """


*Congratulations! You are truly a master scavenger hunter! You have found every single lightning bolt, what an incredible achievement!*
"""
MESSAGE_SCAVENGER_FLAIR_SUCCESS = """
Your flair has been set.
"""
MESSAGE_SCAVENGER_FLAIR_INCORRECT = """
You need to find at least 50 lightning bolts to qualify for the 100k flair.
"""
MESSAGE_EASTER_FLAIR_SUCCESS = """
Your flair has been set.

*By receiving this message, you have automatically redeemed the "Chicken" egg, congratulations!*
"""
MESSAGE_EASTER_FLAIR_INCORRECT = """
You need to find at least 50 eggs to qualify for the Easter flair.

*By receiving this message, you have automatically redeemed the "Chicken" egg, congratulations!*
"""

def datalog(string, end="\n"):
    openFile = open(DATALOGFILE, "a")
    global datalogTimestamp
    global timeStamp
    if datalogTimestamp:
        timeStamp = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        print(timeStamp, end=" |\t")
        openFile.write(timeStamp+"| \t")
        print("[%s]" % (SUBREDDIT[0:5]), end="\t")
    openFile.write("[%s]\t" % (SUBREDDIT[0:5]))
    if end != "\n":
        datalogTimestamp = False
    else:
        datalogTimestamp = True
    print(string, end=end)
    openFile.write(string+end)
    openFile.close()

def smiteLogin():
    global SUBREDDIT
    global sql
    global cur
    SUBREDDIT = "Smite"
    #datalog("Logging in to /u/SmiteRobot", end=", ")
    r.set_oauth_app_info(SMITE_APP_ID, SMITE_APP_SECRET, APP_URI)
    r.refresh_access_information(SMITE_APP_REFRESH)
    #datalog("loading SQL database")
    sql = sqlite3.connect("E:\Programs\Scripts\SmiteRobot\smiteSQL.db")
    cur = sql.cursor()
    sql.commit()

def paladinsLogin():
    global SUBREDDIT
    global sql
    global cur
    SUBREDDIT = "Paladins"
    #datalog("Logging in to /u/PaladinsRobot", end=", ")
    r.set_oauth_app_info(PALADINS_APP_ID, PALADINS_APP_SECRET, APP_URI)
    r.refresh_access_information(PALADINS_APP_REFRESH)
    #datalog("loading SQL database")
    sql = sqlite3.connect("E:\Programs\Scripts\SmiteRobot\paladinsSQL.db")
    cur = sql.cursor()
    sql.commit()

try:
    import star
    r = praw.Reddit(USER_AGENT)
    datalog("Initializing...")
    r.set_oauth_app_info(SMITE_APP_ID, SMITE_APP_SECRET, APP_URI)
    r.refresh_access_information(SMITE_APP_REFRESH)
    SUBREDDIT = "Smite"
    sql = sqlite3.connect("E:\Programs\Scripts\SmiteRobot\smiteSQL.db")
    cur = sql.cursor()
    sql.commit()
except:
    pass

def getStatusPage():
    page = requests.get('http://status.hirezstudios.com')
    return html.fromstring(page.content)

def statusStr(status_data):
    status_display = status_data[0]
    status_class = status_data[1]
    return '['+status_display.capitalize()+'](http://status.hirezstudios.com#/'+status_class+')'

def getStatusContent(el):
    return el.text_content().replace('[\n\t\r\f ]+', ' ').strip()

def getStatusName(status_str):
    for key in STATUS_TO_CSS_CLASS_MAP.keys():
        if key in status_str:
            return [key, STATUS_TO_CSS_CLASS_MAP[key]]
    return ['Operational', 'operational']

def statuses():
    doc = getStatusPage()
    raw_statuses = doc.cssselect('.component-inner-container')
    raw_statuses = map(getStatusContent, raw_statuses)
    smite_statuses = filter(lambda s: SUBREDDIT in s and "Tactics" not in s, raw_statuses)
    smite_statuses = map(getStatusName, smite_statuses)
    return map(statusStr, smite_statuses)

def newStatusStr():
    return '| ' + ' | '.join(statuses()) + ' '

def updateOperationalStatus():
    try:
        sub = r.get_subreddit(SUBREDDIT)
        settings = sub.get_settings()
        reduced_description = settings['description'].replace("\n",'')
        m = re.search('\| *\[.+\]\(http:\/\/status\.hirezstudios\.com#\/.+?\)\s+', reduced_description)
        new_statuses = newStatusStr()
        if SUBREDDIT == "Smite":
            global SmiteStatus
            if new_statuses != SmiteStatus:
                SmiteStatus = new_statuses
                datalog("Updating Smite's Server Status")
                new_description = settings['description'].replace(m.group(0), new_statuses)
                sub.update_settings(description=new_description)
            else:
                return
        if SUBREDDIT == "Paladins":
            global PaladinsStatus
            if new_statuses != PaladinsStatus:
                PaladinsStatus = new_statuses
                datalog("Updating Paladins' Server Status")
                new_description = settings['description'].replace(m.group(0), new_statuses)
                sub.update_settings(description=new_description)
            else:
                return
    except:
        datalog("The Operational Status Update failed. Please investigate.")
        pass

def viewfiles(mauthor, message):
    try:
        cur.execute("SELECT * FROM savefiles WHERE NAME=?", [mauthor])
        fetched = cur.fetchone()
        if not fetched:
            datalog("\tSavefile could not be found, writing reply")
            reply = MESSAGE_FILE_UNAVAILABLE
            message.reply(reply)
            return
        datalog("\tLoading data in savefile, writing reply")
        classa = fetched[1]
        texta = fetched[2]
        classb = fetched[3]
        textb = fetched[4]
        classc = fetched[5]
        textc = fetched[6]
        classd = fetched[7]
        textd = fetched[8]
        classe = fetched[9]
        texte = fetched[10]
        reply = MESSAGE_VIEWFILE_SUCCESS
        try:
            reply = reply.replace("_classa_", classa)
        except:
            reply = reply.replace("_classa_", "")
        try:
            reply = reply.replace("_texta_", texta)
        except:
            reply = reply.replace("_texta_", "")
        try:
            reply = reply.replace("_classb_", classb)
        except:
            reply = reply.replace("_classb_", "")
        try:
            reply = reply.replace("_textb_", textb)
        except:
            reply = reply.replace("_textb_", "")
        try:
            reply = reply.replace("_classc_", classc)
        except:
            reply = reply.replace("_classc_", "")
        try:
            reply = reply.replace("_textc_", textc)
        except:
            reply = reply.replace("_textc_", "")
        try:
            reply = reply.replace("_classd_", classd)
        except:
            reply = reply.replace("_classd_", "")
        try:
            reply = reply.replace("_textd_", textd)
        except:
            reply = reply.replace("_textd_", "")
        try:
            reply = reply.replace("_classe_", classe)
        except:
            reply = reply.replace("_classe_", "")
        try:
            reply = reply.replace("_texte_", texte)
        except:
            reply = reply.replace("_texte_", "")
        message.reply(reply)
    except:
        datalog("\tSomething went wrong! Please investigate.")
        pass

def loadfiles(mauthor, mbody, message):
    try:
        mbody = mbody.capitalize()
        cur.execute('SELECT * FROM savefiles WHERE NAME=?', [mauthor])
        fetched = cur.fetchone()
        if not fetched:
            datalog("\tSavefile could not be found, writing reply")
            reply = MESSAGE_FILE_UNAVAILABLE
            message.reply(reply)
            return
        if mbody == "A":
            tempclass = fetched[1]
            temptext = fetched[2]
        elif mbody == "B":
            tempclass = fetched[3]
            temptext = fetched[4]
        elif mbody == "C":
            tempclass = fetched[5]
            temptext = fetched[6]
        elif mbody == "D":
            tempclass = fetched[7]
            temptext = fetched[8]
        elif mbody == "E":
            tempclass = fetched[9]
            temptext = fetched[10]
        else:
            datalog("\tUser selected '%s' as the filename, writing reply" % (mbody))
            sql.commit()
            reply = MESSAGE_FILE_INCORRECT
            reply = reply.replace("_messagebody_", mbody)
            message.reply(reply)
            return
        datalog("\tLoading data in file " + mbody + ": " + tempclass + ", writing reply")
        r.set_flair(SUBREDDIT, mauthor, temptext, tempclass)
        classa = fetched[1]
        texta = fetched[2]
        classb = fetched[3]
        textb = fetched[4]
        classc = fetched[5]
        textc = fetched[6]
        classd = fetched[7]
        textd = fetched[8]
        classe = fetched[9]
        texte = fetched[10]
        reply = MESSAGE_LOADFILE_SUCCESS.format(fileoverview=MESSAGE_VIEWFILE_SUCCESS)
        reply = reply.replace("_messagebody_", mbody)
        try:
            reply = reply.replace("_classa_", classa)
        except:
            reply = reply.replace("_classa_", "")
        try:
            reply = reply.replace("_texta_", texta)
        except:
            reply = reply.replace("_texta_", "")
        try:
            reply = reply.replace("_classb_", classb)
        except:
            reply = reply.replace("_classb_", "")
        try:
            reply = reply.replace("_textb_", textb)
        except:
            reply = reply.replace("_textb_", "")
        try:
            reply = reply.replace("_classc_", classc)
        except:
            reply = reply.replace("_classc_", "")
        try:
            reply = reply.replace("_textc_", textc)
        except:
            reply = reply.replace("_textc_", "")
        try:
            reply = reply.replace("_classd_", classd)
        except:
            reply = reply.replace("_classd_", "")
        try:
            reply = reply.replace("_textd_", textd)
        except:
            reply = reply.replace("_textd_", "")
        try:
            reply = reply.replace("_classe_", classe)
        except:
            reply = reply.replace("_classe_", "")
        try:
            reply = reply.replace("_texte_", texte)
        except:
            reply = reply.replace("_texte_", "")
        message.reply(reply)
    except AttributeError:
        pass

def savefiles(mauthor, mbody, message):
    try:
        mbody = mbody.capitalize()
        current_flair = r.get_flair(SUBREDDIT, mauthor)
        mclass = current_flair['flair_css_class']
        mtext = current_flair['flair_text']
        if mclass is None:
            datalog("\tUser had no flair equipped, writing reply")
            reply = MESSAGE_FILE_ERROR
            message.reply(reply)
            return
        cur.execute('SELECT * FROM savefiles WHERE NAME=?', [mauthor])
        fetched = cur.fetchone()
        if not fetched:
            cur.execute('INSERT INTO savefiles VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', [mauthor, "", "", "", "", "", "", "", "", "", ""])
            sql.commit()
            cur.execute('SELECT * FROM savefiles WHERE NAME=?', [mauthor])
            fetched = cur.fetchone()
            datalog('\tCreating new savefile for ' + mauthor)
        if mbody == "A":
            cur.execute('UPDATE savefiles SET CLASSA=? WHERE NAME=?', [mclass, mauthor])
            cur.execute('UPDATE savefiles SET TEXTA=? WHERE NAME=?', [mtext, mauthor])
        elif mbody == "B":
            cur.execute('UPDATE savefiles SET CLASSB=? WHERE NAME=?', [mclass, mauthor])
            cur.execute('UPDATE savefiles SET TEXTB=? WHERE NAME=?', [mtext, mauthor])
        elif mbody == "C":
            cur.execute('UPDATE savefiles SET CLASSC=? WHERE NAME=?', [mclass, mauthor])
            cur.execute('UPDATE savefiles SET TEXTC=? WHERE NAME=?', [mtext, mauthor])
        elif mbody == "D":
            cur.execute('UPDATE savefiles SET CLASSD=? WHERE NAME=?', [mclass, mauthor])
            cur.execute('UPDATE savefiles SET TEXTD=? WHERE NAME=?', [mtext, mauthor])
        elif mbody == "E":
            cur.execute('UPDATE savefiles SET CLASSE=? WHERE NAME=?', [mclass, mauthor])
            cur.execute('UPDATE savefiles SET TEXTE=? WHERE NAME=?', [mtext, mauthor])
        else:
            datalog("\tUser selected '%s' as the filename, writing reply" % (mbody))
            sql.commit()
            reply = MESSAGE_FILE_INCORRECT
            reply = reply.replace("_messagebody_", mbody)
            message.reply(reply)
            return
        datalog("\tSaving data in file %s: %s, writing reply" % (mbody, mclass))
        sql.commit()
        cur.execute('SELECT * FROM savefiles WHERE NAME=?', [mauthor])
        fetched = cur.fetchone()
        classa = fetched[1]
        texta = fetched[2]
        classb = fetched[3]
        textb = fetched[4]
        classc = fetched[5]
        textc = fetched[6]
        classd = fetched[7]
        textd = fetched[8]
        classe = fetched[9]
        texte = fetched[10]
        reply = MESSAGE_SAVEFILE_SUCCESS.format(fileoverview=MESSAGE_VIEWFILE_SUCCESS)
        try:
            reply = reply.replace("_messagebody_", mbody)
        except:
            reply = reply.replace("_messagebody_", "")
        try:
            reply = reply.replace("_classa_", classa)
        except:
            reply = reply.replace("_classa_", "")
        try:
            reply = reply.replace("_texta_", texta)
        except:
            reply = reply.replace("_texta_", "")
        try:
            reply = reply.replace("_classb_", classb)
        except:
            reply = reply.replace("_classb_", "")
        try:
            reply = reply.replace("_textb_", textb)
        except:
            reply = reply.replace("_textb_", "")
        try:
            reply = reply.replace("_classc_", classc)
        except:
            reply = reply.replace("_classc_", "")
        try:
            reply = reply.replace("_textc_", textc)
        except:
            reply = reply.replace("_textc_", "")
        try:
            reply = reply.replace("_classd_", classd)
        except:
            reply = reply.replace("_classd_", "")
        try:
            reply = reply.replace("_textd_", textd)
        except:
            reply = reply.replace("_textd_", "")
        try:
            reply = reply.replace("_classe_", classe)
        except:
            reply = reply.replace("_classe_", "")
        try:
            reply = reply.replace("_texte_", texte)
        except:
            reply = reply.replace("_texte_", "")
        message.reply(reply)
    except AttributeError:
        pass

def flairmailtext(mauthor, mbody, message):
    current_flair = r.get_flair(SUBREDDIT, mauthor)
    mclass = current_flair['flair_css_class']
    mlength = len(mbody)
    if mlength > 64:
        datalog('\tFlair is too long, writing reply')
        message.reply(MESSAGE_TOOLONG.format(length=mlength))
    else:
        mbody = mbody.replace('\n', '')
        r.set_flair(SUBREDDIT, mauthor, mbody, mclass)
        reply = MESSAGE_SUCCESS
        reply = reply.replace("_newflair_", mbody)
        datalog('\tFlair was set, writing reply')
        message.reply(reply)

def flairmailtier5(mauthor, mbody, message):
    datalog("\tThe promotional period is over, writing reply")
    message.reply(MESSAGE_TIER5_EXPIRED)
    message.mark_as_read()
    return

def oldflairmailtier5(mauthor, mbody, message):
    try:
        mIGN = ""
        mtext = ""
        mclass = "demonicpact"
        tier5file = None
        try:
            mIGN, mtext = message.body.split('\n')
            mlength = len(mIGN)
        except ValueError:
            datalog("\tSyntax was incorrect, writing reply")
            reply = MESSAGE_TIER5_INCORRECT
            message.reply(reply)
            message.mark_as_read()
            return
        try:
            tier5file = open("demonicpact.txt", 'r')
            for line in tier5file:
                if mIGN.lower() in line.lower():
                    datalog("\tIGN '%s' was found" % (mIGN))
                    if mlength > 64:
                        datalog("\tFlair is too long, writing reply")
                        message.reply(MESSAGE_TOOLONG.format(length=mlength))
                        tier5file.close()
                        return
                    else:
                        r.set_flair(SUBREDDIT, mauthor, mtext, mclass)
                        reply = MESSAGE_SUCCESS
                        reply = reply.replace("_newflair_", mtext)
                        datalog("\tFlair was set, writing reply")
                        message.reply(reply)
                        message.mark_as_read()
                        tier5file.close()
                        return
            datalog("\tIGN '%s' was not found, writing reply" % (mIGN))
            reply = MESSAGE_IGN
            message.reply(MESSAGE_IGN.format(ign=mIGN))
            message.mark_as_read()
            tier5file.close()
            return
        except:
            datalog("\tSomething went wrong! Please investigate.")
            pass
    except AttributeError:
        pass

def flairmaildiamond(mauthor, mbody, message):
    try:
        current_flair = r.get_flair(SUBREDDIT, mauthor)
        sep = " "
        try:
            mclass = current_flair['flair_css_class'].split(sep, 1)[0]
        except:
            datalog("\tFlair does not exist, writing reply")
            message.reply(MESSAGE_ZERO_FLAIR)
            message.mark_as_read()
            return
        mtext = current_flair['flair_text']
        try:
            searchgod = ""
            newclass = str(mclass)
            mworshippers = ""
            platform, IGN = message.body.split('\n')
            if "pc" in platform.lower() or "xbox" in platform.lower() or "ps4" in platform.lower():
                if "pc" in platform.lower():
                    smite._switch_endpoint(Endpoint.SMITE_PC)
                    platform = "PC"
                elif "xbox" in platform.lower():
                    smite._switch_endpoint(Endpoint.SMITE_XBOX)
                    platform = "XBOX"
                elif "ps4" in platform.lower():
                    smite._switch_endpoint(Endpoint.SMITE_PS4)
                    platform = "PS4"
                else:
                    smite._switch_endpoint(Endpoint.SMITE_PC)
                    platform = "Default"
                datalog("\tPlatform is " + platform + ", IGN is " + IGN + ", CSS Class is " + mclass)
                godstats = smite.get_god_ranks(str(IGN))
                if mclass == "agni" or mclass == "oldagni":
                    searchgod = "Agni"
                elif mclass == "ah-muzen-cab":
                    searchgod = "Ah Muzen Cab"
                elif mclass == "ah-puch" or mclass == "christmas2015":
                    searchgod = "Ah Puch"
                elif mclass == "amaterasu":
                    searchgod = "Amaterasu"
                elif mclass == "anhur":
                    searchgod = "Anhur"
                elif mclass == "anubis" or mclass == "demonicpact":
                    searchgod = "Anubis"
                elif mclass == "ao-kuang" or mclass == "oldaokuang":
                    searchgod = "Ao Kuang"
                elif mclass == "aphrodite":
                    searchgod = "Aphrodite"
                elif mclass == "apollo":
                    searchgod = "Apollo"
                elif mclass == "arachne" or mclass == "oldarachne":
                    searchgod = "Arachne"
                elif mclass == "ares":
                    searchgod = "Ares"
                elif mclass == "artemis":
                    searchgod = "Artemis"
                elif mclass == "artio":
                    searchgod = "Artio"
                elif mclass == "athena":
                    searchgod = "Athena"
                elif mclass == "awilix":
                    searchgod = "Awilix"
                elif mclass == "bacchus" or mclass == "christmas2012a":
                    searchgod = "Bacchus"
                elif mclass == "bakasura" or mclass == "oldbakasura" or mclass == "easter2013":
                    searchgod = "Bakasura"
                elif mclass == "bastet" or mclass == "oldbastet":
                    searchgod = "Bastet"
                elif mclass == "bellona" or mclass == "summer2016a":
                    searchgod = "Bellona"
                elif mclass == "cabrakan":
                    searchgod = "Cabrakan"
                elif mclass == "camazotz":
                    searchgod = "Camazotz"
                elif mclass == "cernunnos":
                    searchgod = "Cernunnos"
                elif mclass == "chaac" or mclass == "easter2016":
                    searchgod = "Chaac"
                elif mclass == "change" or mclass == "valentine2014":
                    searchgod = "Chang'e"
                elif mclass == "chiron" or mclass == "christmas2016a":
                    searchgod = "Chiron"
                elif mclass == "chronos" or mclass == "fallenlord":
                    searchgod = "Chronos"
                elif mclass == "cuchu" or mclass == "cuangry":
                    searchgod = "Cu Chulainn"
                elif mclass == "cupid" or mclass == "newyears2015":
                    searchgod = "Cupid"
                elif mclass == "daji":
                    searchgod = "Da Ji"
                elif mclass == "erlang-shen":
                    searchgod = "Erlang Shen"
                elif mclass == "fafnir":
                    searchgod = "Fafnir"
                elif mclass == "fenrir" or mclass == "christmas2013":
                    searchgod = "Fenrir"
                elif mclass == "freya" or mclass == "oldfreya" or mclass == "summer2016f":
                    searchgod = "Freya"
                elif mclass == "ganesha":
                    searchgod = "Ganesha"
                elif mclass == "geb":
                    searchgod = "Geb"
                elif mclass == "guan-yu" or mclass == "oldguanyu":
                    searchgod = "Guan Yu"
                elif mclass == "hades" or mclass == "oldhades":
                    searchgod = "Hades"
                elif mclass == "he-bo" or mclass == "oldhebo":
                    searchgod = "He Bo"
                elif mclass == "hel" or mclass == "oldhel" or mclass == "christmas2012b":
                    searchgod = "Hel"
                elif mclass == "hercules" or mclass == "oldhercules":
                    searchgod = "Hercules"
                elif mclass == "hou-yi":
                    searchgod = "Hou Yi"
                elif mclass == "hun-batz":
                    searchgod = "Hun Batz"
                elif mclass == "izanami":
                    searchgod = "Izanami"
                elif mclass == "isis":
                    searchgod = "Isis"
                elif mclass == "janus":
                    searchgod = "Janus"
                elif mclass == "jing-wei" or mclass == "summer2016e":
                    searchgod = "Jing Wei"
                elif mclass == "kali" or mclass == "oldkali":
                    searchgod = "Kali"
                elif mclass == "khepri" or mclass == "valentine2016a" or mclass == "valentine2016b" or mclass == "summer2016b":
                    searchgod = "Khepri"
                elif mclass == "kukulkan":
                    searchgod = "Kukulkan"
                elif mclass == "kumbhakarna":
                    searchgod = "Kumbhakarna"
                elif mclass == "kuzenbo":
                    searchgod = "Kuzenbo"
                elif mclass == "loki" or mclass == "oldloki" or mclass == "halloween2015":
                    searchgod = "Loki"
                elif mclass == "medusa":
                    searchgod = "Medusa"
                elif mclass == "mercury":
                    searchgod = "Mercury"
                elif mclass == "ne-zha" or mclass == "oldnezha":
                    searchgod = "Ne Zha"
                elif mclass == "neith":
                    searchgod = "Neith"
                elif mclass == "nemesis":
                    searchgod = "Nemesis"
                elif mclass == "nike":
                    searchgod = "Nike"
                elif mclass == "nox" or mclass == "independence2017":
                    searchgod = "Nox"
                elif mclass == "nu-wa" or mclass == "oldnuwa" or mclass == "christmas2014a" or mclass == "summer2016d":
                    searchgod = "Nu Wa"
                elif mclass == "odin":
                    searchgod = "Odin"
                elif mclass == "osiris" or mclass == "halloween2014a" or mclass == "halloween2014b":
                    searchgod = "Osiris"
                elif mclass == "poseidon":
                    searchgod = "Poseidon"
                elif mclass == "ra" or mclass == "oldra" or mclass == "independence2014":
                    searchgod = "Ra"
                elif mclass == "raijin":
                    searchgod = "Raijin"
                elif mclass == "rama":
                    searchgod = "Rama"
                elif mclass == "ratatoskr" or mclass == "christmas2016b":
                    searchgod = "Ratatoskr"
                elif mclass == "ravana":
                    searchgod = "Ravana"
                elif mclass == "scylla":
                    searchgod = "Scylla"
                elif mclass == "serqet":
                    searchgod = "Serqet"                    
                elif mclass == "skadi":
                    searchgod = "Skadi"
                elif mclass == "sobek" or mclass == "summer2016c":
                    searchgod = "Sobek"
                elif mclass == "sol":
                    searchgod = "Sol"
                elif mclass == "sun-wukong" or mclass == "oldsunwukong":
                    searchgod = "Sun Wukong"
                elif mclass == "susano":
                    searchgod = "Susano"
                elif mclass == "sylvanus" or mclass == "christmas2014b":
                    searchgod = "Sylvanus"
                elif mclass == "terra":
                    searchgod = "Terra"
                elif mclass == "thanatos" or mclass == "archon" or mclass == "halloween2013":
                    searchgod = "Thanatos"
                elif mclass == "the-morrigan":
                    searchgod = "The Morrigan"
                elif mclass == "thor" or mclass == "ragnarokforcex":
                    searchgod = "Thor"
                elif mclass == "thoth":
                    searchgod = "Thoth"
                elif mclass == "tyr":
                    searchgod = "Tyr"
                elif mclass == "ullr":
                    searchgod = "Ullr"
                elif mclass == "vamana" or mclass == "oldvamana":
                    searchgod = "Vamana"
                elif mclass == "vulcan":
                    searchgod = "Vulcan"
                elif mclass == "xbalanque":
                    searchgod = "Xbalanque"
                elif mclass == "xing-tian":
                    searchgod = "Xing Tian"
                elif mclass == "ymir":
                    searchgod = "Ymir"
                elif mclass == "zeus" or mclass == "independence2015":
                    searchgod = "Zeus"
                elif mclass == "zhong-kui":
                    searchgod = "Zhong Kui"
                else:
                    datalog("\tUser's flair was not recognised, writing reply")
                    reply = MESSAGE_MASTERY_WRONGFLAIR.format(character="god")
                    message.reply(reply)
                    message.mark_as_read()
                    return
                for row in godstats:
                    if str(row["god"]) == searchgod:
                        mworshippers = row["Worshippers"]
                        datalog("\t%s has %s worshippers on %s on %s" % (str(IGN),str(mworshippers), str(row["god"]), platform))
                        if mworshippers >= 15000:
                            newclass = str(mclass) + " FIFTEENDIA"
                        elif mworshippers >= 14000:
                            newclass = str(mclass) + " FOURTEENDIA"
                        elif mworshippers >= 13000:
                            newclass = str(mclass) + " THIRTEENDIA"
                        elif mworshippers >= 12000:
                            newclass = str(mclass) + " TWELVEDIA"
                        elif mworshippers >= 11000:
                            newclass = str(mclass) + " ELEVENDIA"
                        elif mworshippers >= 10000:
                            newclass = str(mclass) + " TENDIA"
                        elif mworshippers >= 9000:
                            newclass = str(mclass) + " NINEDIA"
                        elif mworshippers >= 8000:
                            newclass = str(mclass) + " EIGHTDIA"
                        elif mworshippers >= 7000:
                            newclass = str(mclass) + " SEVENDIA"
                        elif mworshippers >= 6000:
                            newclass = str(mclass) + " SIXDIA"
                        elif mworshippers >= 5000:
                            newclass = str(mclass) + " FIVEDIA"
                        elif mworshippers >= 4000:
                            newclass = str(mclass) + " FOURDIA"
                        elif mworshippers >= 3000:
                            newclass = str(mclass) + " THREEDIA"
                        elif mworshippers >= 2000:
                            newclass = str(mclass) + " TWODIA"
                        elif mworshippers >= 1000:
                            newclass = str(mclass) + " ONEDIA"
                        else:
                            datalog("\tWorshippers were too low, writing reply")
                            reply = MESSAGE_DIAMOND_SORRY
                            reply = reply.replace("_number_", str(mworshippers))
                            reply = reply.replace("_god_", searchgod)
                            reply = reply.replace("_platform_", platform)
                            message.reply(reply)
                            message.mark_as_read()
                            return
                        r.set_flair(SUBREDDIT, mauthor, mtext, newclass)
                        reply = MESSAGE_DIAMOND_SUCCESS
                        reply = reply.replace("_number_", str(mworshippers))
                        reply = reply.replace("_god_", searchgod)
                        reply = reply.replace("_platform_", platform)
                        datalog('\tFlair was set, writing reply')
                        message.reply(reply)
                        message.mark_as_read()
                        return
                    else:
                        #Checks the next god in the list.
                        pass
                else:
                    datalog("\tSomething went wrong, writing reply")
                    reply = MESSAGE_OOPS2
                    reply = reply.replace("_IGN_", IGN)
                    reply = reply.replace("_platform_", platform)
                    message.reply(reply)
                    message.mark_as_read()
                    return
            else:
                datalog("\tSyntax was incorrect, writing reply")
                reply = MESSAGE_DIAMOND_INCORRECT
                message.reply(reply)
                message.mark_as_read()
                return
        except:
            datalog("\tSomething went wrong, writing reply")
            reply = MESSAGE_OOPS
            message.reply(reply)
            message.mark_as_read()
            return
    except:
        datalog("\tSomething went wrong, writing reply")
        reply = MESSAGE_OOPS
        message.reply(reply)
        message.mark_as_read()
        return

def flairmaillevel(mauthor, mbody, message):
    try:
        cur.execute('SELECT * FROM users WHERE NAME=? AND IGN IS NOT NULL', [mauthor])
        fetched = cur.fetchone()
        if not fetched:
            datalog("\tAccount was not linked")
            message.reply(MESSAGE_NOT_LINKED.format())
            message.mark_as_read()
            return
        else:
            platform = fetched[2]
            IGN = fetched[3]
            message.reply(updatelevelflair(mauthor,platform,IGN,True))
            message.mark_as_read()
            return
    except Exception as e:
        datalog("\tSomething went wrong, writing reply -- Error: {e}".format(e=e))
        message.reply(MESSAGE_OOPS4)
        message.mark_as_read()
        return

def flairmailmastery(mauthor, mbody, message):
    try:
        cur.execute('SELECT * FROM users WHERE NAME=? AND IGN IS NOT NULL', [mauthor])
        fetched = cur.fetchone()
        if not fetched:
            datalog("\tAccount was not linked")
            message.reply(MESSAGE_NOT_LINKED.format())
            message.mark_as_read()
        else:
            platform = fetched[2]
            IGN = fetched[3]
            message.reply(updatemasteryflair(mauthor,platform,IGN,True))
            message.mark_as_read()
            return
    except Exception as e:
        datalog("\tSomething went wrong, writing reply -- Error: {e}".format(e=e))
        message.reply(MESSAGE_OOPS4)
        message.mark_as_read()
        return

def flairmailcompetitive(mauthor, mbody, message):
    try:
        cur.execute('SELECT * FROM users WHERE NAME=? AND IGN IS NOT NULL', [mauthor])
        fetched = cur.fetchone()
        if not fetched:
            datalog("\tAccount was not linked")
            message.reply(MESSAGE_NOT_LINKED.format())
            message.mark_as_read()
        else:
            platform = fetched[2]
            IGN = fetched[3]
            message.reply(updatecompetitiveflair(mauthor,platform,IGN,True))
            message.mark_as_read()
            return
    except Exception as e:
        datalog("\tSomething went wrong, writing reply -- Error: {e}".format(e=e))
        message.reply(MESSAGE_OOPS4)
        message.mark_as_read()
        return

def updatelevelflair(name, platform, IGN, log=False):
    try:
        current_flair = r.get_flair(SUBREDDIT, name)
        sep = " "
        try:
            oldclass = current_flair['flair_css_class']
            mclass = oldclass.split(sep, 1)[0]
        except:
            if log:
                datalog("\tFlair does not exist, writing reply")
            return(MESSAGE_ZERO_FLAIR)
        mtext = current_flair['flair_text']
        if platform == "PC":
            smite._switch_endpoint(Endpoint.PALADINS_PC)
        elif platform == "XBOX":
            smite._switch_endpoint(Endpoint.PALADINS_XBOX)
        elif platform == "PS4":
            smite._switch_endpoint(Endpoint.PALADINS_PS4)
        else:
            smite._switch_endpoint(Endpoint.PALADINS_PC)
        if log:
            datalog("\tPlatform is {platform}, IGN is {IGN}, CSS Class is {flair}".format(platform=platform,IGN=IGN,flair=mclass))
        level = ""
        rank = ""
        playerstats = smite.get_player(str(IGN))
        level = playerstats[0]["Level"]
        if log:
            datalog("\t{user} is level {level}".format(user=IGN,level=level))
        if level>=999:
            rank = 999
        elif level>=900:
            rank = 900
        elif level>=800:
            rank = 800
        elif level>=700:
            rank = 700
        elif level>=600:
            rank = 600
        elif level>=500:
            rank = 500
        elif level>=400:
            rank = 400
        elif level>=300:
            rank = 300
        elif level>=200:
            rank = 200
        elif level>=100:
            rank = 100
        elif level>=75:
            rank = 75
        elif level>=50:
            rank = 50
        elif level>=30:
            rank = 30
        elif level>=15:
            rank = 15
        else:
            if log:
                datalog("\tAccount level was not high enough")
            return(MESSAGE_LEVEL_TOO_LOW.format(IGN=IGN,platform=platform))
        newclass = "{mclass} level{rank}account".format(mclass=mclass,rank=rank)
        if str(oldclass) != newclass:
            r.set_flair(SUBREDDIT, name, mtext, newclass)
            if log:
                datalog("\tFlair was set, writing reply")
        else:
            if log:
                datalog("\tFlair did not change, writing reply")
        return(MESSAGE_LEVEL_SUCCESS.format(level=level))
    except Exception as e:
        if log:
            datalog("\tSomething went wrong, writing reply -- Error: {e}".format(e=e))
        return(MESSAGE_OOPS4)

def updatemasteryflair(name, platform, IGN, log=False):
    try:
        current_flair = r.get_flair(SUBREDDIT, name)
        sep = " "
        try:
            oldclass = current_flair['flair_css_class']
            mclass = oldclass.split(sep, 1)[0]
        except:
            if log:
                datalog("\tFlair does not exist, writing reply")
            return(MESSAGE_ZERO_FLAIR)
        mtext = current_flair['flair_text']
        if platform == "PC":
            smite._switch_endpoint(Endpoint.PALADINS_PC)
        elif platform == "XBOX":
            smite._switch_endpoint(Endpoint.PALADINS_XBOX)
        elif platform == "PS4":
            smite._switch_endpoint(Endpoint.PALADINS_PS4)
        else:
            smite._switch_endpoint(Endpoint.PALADINS_PC)
        if log:
            datalog("\tPlatform is {platform}, IGN is {IGN}, CSS Class is {flairclass}".format(platform=platform,IGN=IGN,flairclass=mclass))
        searchchampion = ""
        newclass = str(mclass)
        mrank = ""
        championstats = smite.get_god_ranks(str(IGN))
        searchchampion = newclass
        for row in championstats:
            testchampion = str(row["champion"]).replace("'", "").replace(" ","").lower()
            if testchampion == searchchampion:
                mrank = row["Rank"]
                if log:
                    datalog("\t{user} is ranked {rank} on {champ}".format(user=IGN,rank=mrank,champ=testchampion))
                newclass = "{champ} rank{rank}mastery".format(champ=mclass,rank=mrank)
                if str(oldclass) != newclass:
                    r.set_flair(SUBREDDIT, name, mtext, newclass)
                    if log:
                        datalog("\tFlair was set, writing reply")
                else:
                    if log:
                        datalog("\tFlair did not change, writing reply")
                return(MESSAGE_MASTERY_SUCCESS.format(rank=mrank,champion=testchampion))
            else:
                #Checks next Champion in list.
                pass
        if log:
            datalog("\tUser Flair was not a Champion, writing reply")
        return(MESSAGE_MASTERY_WRONGFLAIR.format(character="Champion"))
    except Exception as e:
        if log:
            datalog("\tSomething went wrong, writing reply -- Error: {e}".format(e=e))
        return(MESSAGE_OOPS4)

def updatecompetitiveflair(name, platform, IGN, log=False):
    try:
        current_flair = r.get_flair(SUBREDDIT, name)
        sep = " "
        try:
            oldclass = current_flair['flair_css_class']
            mclass = oldclass.split(sep, 1)[0]
        except:
            if log:
                datalog("\tFlair does not exist, writing reply")
            return(MESSAGE_ZERO_FLAIR)
        mtext = current_flair['flair_text']
        if platform == "PC":
            smite._switch_endpoint(Endpoint.PALADINS_PC)
        elif platform == "XBOX":
            smite._switch_endpoint(Endpoint.PALADINS_XBOX)
        elif platform == "PS4":
            smite._switch_endpoint(Endpoint.PALADINS_PS4)
        else:
            smite._switch_endpoint(Endpoint.PALADINS_PC)
        if log:
            datalog("\tPlatform is {platform}, IGN is {IGN}, CSS Class is {flairclass}".format(platform=platform,IGN=IGN,flairclass=mclass))
        mclass = str(mclass)
        rankInt = 0
        rankStr = ""
        rankFormatted = ""
        playerstats = smite.get_player(str(IGN))
        rankInt = playerstats[0]["Tier_Conquest"]
        rankStr = rankingList[rankInt]
        rankFormatted = rankingListFormatted[rankInt]
        if log:
            datalog("\t{user} is rank {rank}".format(user=IGN,rank=rankFormatted))
        newclass = "{mclass} {rank}rank".format(mclass=mclass,rank=rankStr)
        if str(oldclass) != newclass:
            r.set_flair(SUBREDDIT, name, mtext, newclass)
            if log:
                datalog("\tFlair was set, writing reply")
        else:
            if log:
                datalog("\tFlair did not change, writing reply")
        return(MESSAGE_COMPETITIVE_SUCCESS.format(rank=rankFormatted))
    except Exception as e:
        if log:
            datalog("\tSomething went wrong, writing reply -- Error: {e}".format(e=e))
        return(MESSAGE_OOPS4)

def linkaccounts(mauthor, mbody, message):
    try:
        platform = ""
        IGN = ""
        try:
            platform, IGN = message.body.split('\n')
            if "pc" in platform.lower() or "xbox" in platform.lower() or "ps4" in platform.lower():
                if "pc" in platform.lower():
                    smite._switch_endpoint(Endpoint.PALADINS_PC)
                    platform = "PC"
                elif "xbox" in platform.lower():
                    smite._switch_endpoint(Endpoint.PALADINS_XBOX)
                    platform = "XBOX"
                elif "ps4" in platform.lower():
                    smite._switch_endpoint(Endpoint.PALADINS_PS4)
                    platform = "PS4"
                else:
                    smite._switch_endpoint(Endpoint.PALADINS_PC)
                    platform = "Default"
            else:
                datalog("\tInformation was not correct, writing reply")
                message.reply(MESSAGE_DIAMOND_INCORRECT)
                message.mark_as_read()
                return
            datalog("\tPlatform is {platform}, IGN is {IGN}".format(platform=platform,IGN=IGN))
            accountdata = smite.get_player(str(IGN))
            accountName = accountdata[0]["Name"]
            accountID = accountdata[0]["Id"]
            accountDate = accountdata[0]["Created_Datetime"]
            try:
                cur.execute('SELECT * FROM users WHERE NAME=?', [mauthor])
                fetched = cur.fetchone()
                if not fetched:
                    cur.execute('INSERT INTO users VALUES(?, ?, ?, ?)', [mauthor, "", platform, IGN])
                else:
                    cur.execute('UPDATE users SET PLATFORM=? WHERE NAME=?', [platform, mauthor])
                    cur.execute('UPDATE users SET IGN=? WHERE NAME=?', [IGN, mauthor])
                sql.commit()
            except Exception as e:
                datalog("\tSomething went wrong, writing reply -- Error: {e}".format(e=e))
                message.reply(MESSAGE_OOPS3.format(IGN=IGN,platform=platform))
                message.mark_as_read()
                return
            datalog("\tAccount was successfully linked, writing reply")
            message.reply(MESSAGE_LINK_SUCCESS.format(ign=accountName,id=accountID,date=accountDate))
            message.mark_as_read()
            return
        except Exception as e:
            datalog("\tSomething went wrong, writing reply -- Error: {e}".format(e=e))
            message.reply(MESSAGE_OOPS3.format(IGN=IGN,platform=platform))
            message.mark_as_read()
            return
    except Exception as e:
        datalog("\tSomething went wrong, writing reply -- Error: {e}".format(e=e))
        message.reply(MESSAGE_OOPS3.format(IGN=IGN,platform=platform))
        message.mark_as_read()
        return

def autochangeflair(pauthor, pflair, ptext):
    if pflair == "vamana":
        pflair = "oldvamana"
        datalog("Changing %s's flair to %s" % (pauthor, pflair))
        current_flair = r.get_flair(SUBREDDIT, pauthor)
        ptext = current_flair['flair_text']
        r.set_flair(SUBREDDIT, pauthor, ptext, pflair)

def seasonticketmaths():
    today = date.today()
    future = date(2017,1,8)
    countdown = future - today
    seasonticket1 = math.ceil(5000 / float(countdown.days))
    seasonticket2 = math.ceil(10000 / float(countdown.days))
    seasonticket3 = math.ceil(15000 / float(countdown.days))
    seasonticket4 = math.ceil(20000 / float(countdown.days))
    reply = MESSAGE_SEASONTICKETHELP
    reply = reply.replace("_days_", str(countdown.days))
    reply = reply.replace("_5knumber_", str(seasonticket1))
    reply = reply.replace("_10knumber_", str(seasonticket2))
    reply = reply.replace("_15knumber_", str(seasonticket3))
    reply = reply.replace("_20knumber_", str(seasonticket4))
    return(reply)

def updateeasterprofile(mauthor,code):
    totalCodes = 0
    cur.execute('SELECT * FROM eastereggs WHERE NAME=?', [mauthor])
    fetch = cur.fetchone()
    if not fetch:
        cur.execute('INSERT INTO eastereggs(NAME) VALUES(?)', [mauthor])
        sql.commit()
        cur.execute('SELECT * FROM eastereggs WHERE NAME=?', [mauthor])
        fetch = cur.fetchone()
    cur.execute('UPDATE eastereggs SET {code}=? WHERE NAME=?'.format(code=code), [1, mauthor])
    cur.execute('UPDATE eastereggs SET PROGRESS=0 WHERE NAME=?', [mauthor])
    cur.execute('SELECT * FROM eastereggs WHERE NAME=?', [mauthor])
    fetch = cur.fetchone()
    for item in fetch:
        if item == 1:
            totalCodes += 1
        else:
            pass
    cur.execute('UPDATE eastereggs SET PROGRESS=? WHERE NAME=?', [totalCodes, mauthor])
    return totalCodes

def eastereggname(code):
    cur.execute("SELECT {code} FROM eastereggs WHERE NAME=?".format(code=code), ["CODENAMES"])
    tempString = cur.fetchone()[0]
    return tempString

def percenteggs(code):
    cur.execute("SELECT COUNT(*) FROM eastereggs")
    totalCount = cur.fetchone()[0]-1
    cur.execute("SELECT SUM({code}) FROM eastereggs".format(code=code))
    redeemedCount = cur.fetchone()[0]
    percentage = round((redeemedCount/totalCount)*100,2)
    return percentage

def easterinfo(mauthor, mbody, message):
    try:
        totalCodes = updateeasterprofile(mauthor,"ESTRP8Z6YXYGTKQQ")
        cur.execute("SELECT * FROM eastereggs WHERE NAME=?", [mauthor])
        redeemedCodes = cur.fetchone()
        cur.execute("SELECT * FROM eastereggs WHERE NAME=?", ["CODENAMES"])
        codenames = cur.fetchone()
        response_list = []
        response_string = ""
        for item in codenames:
            if item:
                i = codenames.index(item)
                if i!=0 and i!=1:
                    if redeemedCodes[i]:
                        itemquotes = "~~"
                    else:
                        itemquotes = "**"
                    totalString = itemquotes+item+itemquotes
                    cur.execute("SELECT * FROM eastereggs")
                    new_tuple = (totalString,percenteggs(cur.description[i][0]))
                    response_list.append(new_tuple)
                else:
                    pass
        response_list.sort(key=lambda x: x[1], reverse=True)
        for i in response_list:
            a = response_list.index(i)
            new_string = "{prev}{name}|{percent}%\n".format(prev=response_string,name=(response_list[a][0]),percent=(response_list[a][1]))
            response_string = new_string
        datalog("\tData collated, writing reply")
        message.reply(MESSAGE_EASTER_INFO.format(number=totalCodes,subreddit=SUBREDDIT,info=response_string,footer=MESSAGE_EASTER_FOOTER))
        return
    except Exception as e:
        datalog("Something went wrong, {error}, writing reply".format(error=e))
        message.reply(MESSAGE_EASTER_OOPS)
        return

def easteregghunt(mauthor, mbody, message):
    datalog("\tThe promotional period is over, writing reply")
    message.reply(MESSAGE_EVENT_EXPIRED)
    message.mark_as_read()
    return

def scavengerhunt(mauthor, mbody, message):
    datalog("\tThe promotional period is over, writing reply")
    message.reply(MESSAGE_EVENT_EXPIRED)
    message.mark_as_read()
    return

def oldscavengerhunt(mauthor, mbody, message, achievement=""):
    condensedbody = mbody.replace("-","")
    try:
        easter_egg_code = re.search("ESTRS.{11}", condensedbody).group(0)
        codefile = open("eastersmite.txt", 'r')
        written_code = easter_egg_code[0:4]+"-"+easter_egg_code[4:8]+"-"+easter_egg_code[8:12]+"-"+easter_egg_code[12:16]
        datalog("\tChecking code: {code}".format(code=written_code))
        for line in codefile:
            if written_code.lower() in line.lower():
                codeName = eastereggname(easter_egg_code)
                percentage = percenteggs(easter_egg_code)
                totalCodes = updateeasterprofile(mauthor,easter_egg_code)
                datalog('\tCode "{codeName}" ({percentage}%) was successfully logged, {totalCodes}/100, writing reply'.format(codeName=codeName,percentage=percentage,totalCodes=totalCodes))
                if totalCodes == 50:
                    achievement=MESSAGE_EASTER_50ACHIEVEMENT
                if totalCodes == 100:
                    achievement=MESSAGE_EASTER_100ACHIEVEMENT
                message.reply(MESSAGE_SCAVENGER_SUCCESS.format(codeName=codeName,code=written_code,percentage=percentage,number=totalCodes,subreddit=SUBREDDIT,footer=MESSAGE_SCAVENGER_FOOTER,achievement=achievement))
                return
        datalog("\tThe code was incorrect, writing reply")
        message.reply(MESSAGE_EASTER_INCORRECT.format(code=written_code,footer=MESSAGE_SCAVENGER_FOOTER))
        return
    except Exception as e:
        datalog("\tError {error}. A code could not be found, writing reply".format(error=e))
        message.reply(MESSAGE_EASTER_ERROR.format(footer=MESSAGE_SCAVENGER_FOOTER))
        return

def scavengerflair(mauthor, mbody, message):
    totalCodes = updateeasterprofile(mauthor,"ESTRS22L83YRLMJW")
    datalog("\tUser has {eggs} eggs".format(eggs=totalCodes))
    newflair = ""
    if totalCodes > 49:
        newflair = "onehundred"
    else:
        datalog("\tNot enough for the 100k flair, writing reply")
        message.reply(MESSAGE_SCAVENGER_FLAIR_INCORRECT)
        return
    mlength = len(mbody)
    if mlength > 64:
        datalog('\tFlair is too long, writing reply')
        message.reply(MESSAGE_TOOLONG.format(length=mlength))
    else:
        r.set_flair(SUBREDDIT, mauthor, mbody.replace('\n', ''), newflair)
        datalog('\tFlair was set, writing reply')
        message.reply(MESSAGE_SCAVENGER_FLAIR_SUCCESS)
    return

def easterflair(mauthor, mbody, message):
    totalCodes = updateeasterprofile(mauthor,"ESTRPZ43T93FB3SA")
    datalog("\tUser has {eggs} eggs".format(eggs=totalCodes))
    newflair = ""
    if totalCodes > 149:
        newflair = "easter eggdetective"
    elif totalCodes > 99:
        newflair = "easter eggstalker"
    elif totalCodes > 49:
        newflair = "easter egghunter"    
    else:
        datalog("\tNot enough for an Easter flair, writing reply")
        message.reply(MESSAGE_EASTER_FLAIR_INCORRECT)
        return
    mlength = len(mbody)
    if mlength > 64:
        datalog('\tFlair is too long, writing reply')
        message.reply(MESSAGE_TOOLONG.format(length=mlength))
    else:
        r.set_flair(SUBREDDIT, mauthor, mbody.replace('\n', ''), newflair)
        datalog('\tFlair was set, writing reply')
        message.reply(MESSAGE_EASTER_FLAIR_SUCCESS)
    return

def getMatchStats(matchID,myplatform,guruplatform):
    try:
        datalog("\tGetting match {id}".format(id=matchID),end=", ")
        info = smite.get_match_details(matchID)
        firstrow = info[0]
        rawseconds = firstrow["Time_In_Match_Seconds"]
        minutes = rawseconds//60
        seconds = rawseconds % 60
        score1 = firstrow["Team1Score"]
        difference1 = 4-score1
        score2 = firstrow["Team2Score"]
        difference2 = 4-score2
        if difference1 < difference2:
            score1 += difference1
            score2 += difference1
        else:
            score1 += difference2
            score2 += difference2
        partyList = []
        replyString = ""
        replyString += "MatchID|Time|Mode|Region|Score|Duration\n:--|:--|:--|:--|:--|:--\n"
        replyString += matchID
        replyString += "|"
        replyString += str(firstrow["Entry_Datetime"]) #Time
        replyString += "|"
        replyString += str(firstrow["name"]).replace(": ","") #Game Mode
        replyString += "|"
        region = firstrow["Region"]
        try:
            region = "[" + region + "](#/flair" + regionFlagsDictionary[region] + ")"
        except:
            pass
        replyString += region #Region
        replyString += "|"
        replyString += str(score1) #Score 1
        replyString += "-"
        replyString += str(score2) #Score 2
        replyString += "|"
        replyString += str(minutes) #Minutes
        replyString += ":"
        replyString += str(seconds) #Seconds
        replyString += "\n\n"
        replyString += "P|[Lv] Player|Rank|Champion|Cred (CPM)|K/D/A|Dmg|Shield|Heal|Obj\n:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--\n"
        for row in info:
            replyString += "|"
            winStr = ""
            if row["Win_Status"] == "Winner":
                winStr = "**"
            party = row["PartyId"]
            if party != 0:
                if party not in partyList:
                    partyList.append(party)
                party = partyList.index(party)
                replyString += winStr
                replyString += chr(party+65) #Party
                replyString += winStr
            replyString += "|"
            replyString += winStr
            replyString += "["
            replyString += str(row["Account_Level"]) #Account Level
            replyString += "] "
            replyString += str(row["playerName"]) #Account Name
            replyString += winStr
            replyString += "|"
            try:
                replyString += winStr + rankingListShort[row["League_Tier"]] + winStr #Ranking
            except:
                pass
            replyString += "|"
            replyString += winStr
            replyString += "["
            replyString += str(row["Reference_Name"]) #Champion
            replyString += "](#/flair"
            replyString += str(row["Reference_Name"]).replace("'", "").replace(" ","").lower() #Flair
            replyString += ")"
            replyString += winStr
            replyString += "|"
            replyString += winStr
            tempGold = row["Gold_Earned"]
            tempCPS = tempGold/rawseconds
            tempCPM = tempCPS*60
            replyString += str("{:,}".format(tempGold)) #Credits
            replyString += " ("
            replyString += str(int(round(tempCPM,0))) #CPM
            replyString += ")"
            replyString += winStr
            replyString += "|"
            replyString += winStr
            replyString += str(row["Kills_Player"]) #Kills
            replyString += "/"
            replyString += str(row["Deaths"]) #Deaths
            replyString += "/"
            replyString += str(row["Assists"]) #Assists
            replyString += winStr
            replyString += "|"
            replyString += winStr
            replyString += "{:,}".format(row["Damage_Player"]) #Damage Dealt
            replyString += winStr
            replyString += "|"
            replyString += winStr
            replyString += "{:,}".format(row["Damage_Mitigated"]) #Shielding
            replyString += winStr
            replyString += "|"
            replyString += winStr
            replyString += "{:,}".format(row["Healing"]) #Healing
            replyString += winStr
            replyString += "|"
            replyString += winStr
            replyString += "{:,}".format(row["Objective_Assists"]) #Objective Time
            replyString += winStr
            replyString += "|\n"
        replyString += "\n"
        replyString += "*More info: [My Paladins](https://{myplatform}mypaladins.com/match/".format(myplatform=myplatform)
        replyString += matchID
        replyString += ") • [Paladins Guru](http://paladins.guru/match/{guruplatform}/".format(guruplatform=guruplatform)
        replyString += matchID
        replyString += ")*"
        datalog("writing reply")
        return(replyString)
    except:
        replyString = "The match '{matchID}' you specified could not be found. Try looking on ".format(matchID=matchID)
        replyString += "[My Paladins](https://{myplatform}mypaladins.com/match/".format(myplatform=myplatform)
        replyString += matchID
        replyString += ") or [Paladins Guru](http://paladins.guru/match/{guruplatform}/".format(guruplatform=guruplatform)
        replyString += matchID
        replyString += ") instead"
        datalog("the API failed to find the match, writing reply")
        return(replyString)

def checkmail():
    unreads = list(r.get_unread(limit=None))
    for message in unreads:
        try:
            mauthor = message.author.name
            msubject = message.subject.lower()
            mbody = message.body
            if any(trigger.lower() == msubject for trigger in SCAVENGERSUBJECTLINE) or SCAVENGERSUBJECTLINE==[]:
                #Scavenger Hunt
                datalog("%s has found a lightning bolt!" % (mauthor))
                scavengerhunt(mauthor, mbody, message)
            elif any(trigger.lower() == msubject for trigger in SCAVENGERFLAIRSUBJECTLINE) or SCAVENGERFLAIRSUBJECTLINE==[]:
                #Scavenger Flair
                datalog("%s has requested a 100k flair" % (mauthor))
                scavengerflair(mauthor, mbody, message)
            elif any(trigger.lower() == msubject for trigger in EASTERFLAIRSUBJECTLINE) or EASTERFLAIRSUBJECTLINE==[]:
                #Easter Flair
                datalog("%s has requested an Easter flair" % (mauthor))
                easterflair(mauthor, mbody, message)
            elif any(trigger.lower() == msubject for trigger in EASTERINFOSUBJECTLINE) or EASTERINFOSUBJECTLINE==[]:
                #Egg Information
                datalog("%s has requested information about the Easter egg hunt" % (mauthor))
                easterinfo(mauthor, mbody, message)
            elif any(trigger.lower() == msubject for trigger in EASTERCODESSUBJECTLINE) or EASTERCODESSUBJECTLINE==[]:
                #Easter Egg Hunt
                datalog("%s has found an easter egg!" % (mauthor))
                easteregghunt(mauthor, mbody, message)
            elif any(trigger.lower() == msubject for trigger in SAVEFILESUBJECTLINE) or SAVEFILESUBJECTLINE==[]:
                #Save File
                datalog("%s wishes to save their flair" % (mauthor))
                savefiles(mauthor, mbody, message)
            elif any(trigger.lower() == msubject for trigger in LOADFILESUBJECTLINE) or LOADFILESUBJECTLINE==[]:
                #Load File
                datalog("%s wishes to load a flair" % (mauthor))
                loadfiles(mauthor, mbody, message)
            elif any(trigger.lower() == msubject for trigger in VIEWFILESUBJECTLINE) or VIEWFILESUBJECTLINE==[]:
                #View File
                datalog("%s wishes to view their file" % (mauthor))
                viewfiles(mauthor, message)
            elif any(trigger.lower() == msubject for trigger in FLAIRTEXTSUBJECTLINE) or FLAIRTEXTSUBJECTLINE==[]:
                #Flair Text
                datalog("%s has requested new flair text" % (mauthor))
                flairmailtext(mauthor, mbody, message)
            elif any(trigger.lower() == msubject for trigger in LINKACCOUNTSUBJECTLINE) or LINKACCOUNTSUBJECTLINE==[]:
                #Account Link
                if SUBREDDIT == "Paladins":
                    datalog("%s has requested an account link" % (mauthor))
                    linkaccounts(mauthor, mbody, message)
            elif any(trigger.lower() == msubject for trigger in MASTERYSUBJECTLINE) or MASTERYSUBJECTLINE==[]:
                #Mastery Flair
                if SUBREDDIT == "Paladins":
                    datalog("%s has requested a mastery flair" % (mauthor))
                    flairmailmastery(mauthor, mbody, message)
            elif any(trigger.lower() == msubject for trigger in LEVELSUBJECTLINE) or LEVELSUBJECTLINE==[]:
                #Level Flair
                if SUBREDDIT == "Paladins":
                    datalog("%s has requested a level flair" % (mauthor))
                    flairmaillevel(mauthor, mbody, message)
            elif any(trigger.lower() == msubject for trigger in COMPETITIVESUBJECTLINE) or COMPETITIVESUBJECTLINE==[]:
                #Competitive Flair
                if SUBREDDIT == "Paladins":
                    datalog("%s has requested a competitive flair" % (mauthor))
                    flairmailcompetitive(mauthor, mbody, message)
            elif any(trigger.lower() == msubject for trigger in DIAMONDSUBJECTLINE) or DIAMONDSUBJECTLINE==[]:
                #Diamond Flair
                if SUBREDDIT == "Smite":
                    datalog("%s has requested a diamond flair" % (mauthor))
                    flairmaildiamond(mauthor, mbody, message)
            elif any(trigger.lower() == msubject for trigger in TIER5SUBJECTLINE) or TIER5SUBJECTLINE==[]:
                #Tier 5 Skin Flair
                if SUBREDDIT == "Smite":
                    datalog('%s has requested a Tier 5 flair' % (mauthor))
                    flairmailtier5(mauthor, mbody, message)
            elif msubject == "test":
                testMessage(mauthor, mbody, message)
            elif message.subject == "username mention" and message.was_comment:
                pass
            elif message.subject == "comment reply" and message.was_comment:
                pass
            else:
                datalog("%s sent a message I do not understand, writing reply" % (mauthor))
                message.mark_as_read()
                reply = MESSAGE_GENERAL_INCORRECT
                message.reply(reply)
        except AttributeError:
            pass
        message.mark_as_read()

def updatedatabase(pauthor,pflair):
    try:
        if pflair is None:
            pflair = "none"
        cur.execute('SELECT * FROM users WHERE NAME=?', [pauthor])
        fetched = cur.fetchone()
        if not fetched:
            cur.execute('INSERT INTO users VALUES(?, ?)', [pauthor, pflair])
            datalog("New user flair data: %s: '%s'" % (pauthor, pflair))
        else:
            oldflair = fetched[1]
            if pflair != oldflair:
                cur.execute('UPDATE users SET FLAIR=? WHERE NAME=?', [pflair, pauthor])
                datalog("Updated user flair data: %s: '%s' > '%s'" % (pauthor, oldflair, pflair))
        sql.commit()
        if SUBREDDIT == "Paladins":
            cur.execute('SELECT * FROM users WHERE NAME=? AND IGN IS NOT NULL', [pauthor])
            fetched = cur.fetchone()
            if fetched:
                try:
                    sep = " "
                    current_flair = fetched[1].split(sep, 1)[0]
                except:
                    return
                if fetched[1].endswith("account"):
                    #Level Flair
                    updatelevelflair(fetched[0], fetched[2], fetched[3])
                if fetched[1].endswith("rank"):
                    #Competitive Flair
                    updatecompetitiveflair(fetched[0], fetched[2], fetched[3])
                if fetched[1].endswith("mastery"):
                    #Mastery Flair
                    updatemasteryflair(fetched[0], fetched[2], fetched[3])
        sql.commit()
    except Exception as e:
        pass

def cachepost(postid):
    cur.execute('SELECT * FROM cache WHERE POSTID=?', [postid])
    fetched = cur.fetchone()
    if not fetched:
        temptimevar = datetime.datetime.now()
        cur.execute('INSERT INTO cache VALUES(?, ?)', [temptimevar, postid])
        sql.commit()
        return True
    else:
        return False

def checkpost(postid):
    try:
        datalog("Checking post {postid}".format(postid=postid))
        post = r.get_info(thing_id=postid)
        pauthor = post.author.name
        pcontent = post.body.lower()
        pflair = post.author_flair_css_class
        ptext = post.author_flair_text
        #CHECK FOR COMMANDS
        if SUBREDDIT == "Paladins":
            if pauthor != "PaladinsRobot":
                isMatch1 = re.search('(?i)match', pcontent)
                isMatch2 = re.search('\d{8,11}', pcontent)
                if isMatch1 and isMatch2:
                    datalog("%s requested the details of a match" % (pauthor))
                    matchID = isMatch2.group(0)
                    if matchID == "":
                        matchID = "0"
                    myplatform = ""
                    guruplatform = "pc"
                    xb1Match = re.search('(?i)xb1|xbox|match\/xb', pcontent)
                    ps4Match = re.search('(?i)ps4|playstation|match\/ps', pcontent)
                    if xb1Match:
                        smite._switch_endpoint(Endpoint.PALADINS_XBOX)
                        myplatform = "xbox."
                        guruplatform = "xb"
                    elif ps4Match:
                        smite._switch_endpoint(Endpoint.PALADINS_PS4)
                        myplatform = "ps4."
                        guruplatform = "ps"
                    else:
                        smite._switch_endpoint(Endpoint.PALADINS_PC)
                        post.reply(getMatchStats(matchID,myplatform,guruplatform))
        isMatch = any(string in pcontent for string in starhelp)
        if isMatch:
            datalog("%s requested more information about me, writing reply" % (pauthor))
            post.reply(MESSAGE_STARINFO)
        #if SUBREDDIT == "Smite":
            #isMatch = any(string in pcontent for string in seasontickethelp)
            #if isMatch:
                #datalog("%s requested help with the Season Ticket, writing reply" % (pauthor))
                #post.reply(seasonticketmaths())
        #CHECK FOR PRO PLAYERS
        if SUBREDDIT == "Smite":
            if "\n"+pauthor+"\n" in open("splproplayers.txt").read():
                if not pflair.endswith(" VER"):
                    datalog("Changing %s's flair from '%s' to '%s VER'" % (pauthor, pflair, pflair))
                    r.set_flair(SUBREDDIT, pauthor, ptext, pflair + " VER")
        #CHECK FOR HIREZ PERSONNEL
        if post.author_flair_css_class == "hirez":
            plinkflairclass = post.submission.link_flair_css_class
            plinkflairtext = post.submission.link_flair_text
            if not plinkflairtext.endswith(" | HIREZ RESPONDED"):
                datalog("%s made a comment. Changing %s flair" % (pauthor, plinkflairtext))
                plinkflairtext = plinkflairtext + " | HIREZ RESPONDED"
                r.set_flair(SUBREDDIT, post.submission, plinkflairtext, plinkflairclass)
        #COLLECT FLAIR DATA
        try:
            #autochangeflair(pauthor, pflair, ptext)
            if pflair is None:
                pflair = "none"
            cur.execute('SELECT * FROM users WHERE NAME=?', [pauthor])
            fetched = cur.fetchone()
            if not fetched:
                cur.execute('INSERT INTO users VALUES(?, ?)', [pauthor, pflair])
                datalog("New user flair data: %s: '%s'" % (pauthor, pflair))
            else:
                oldflair = fetched[1]
                if pflair != oldflair:
                    cur.execute('UPDATE users SET FLAIR=? WHERE NAME=?', [pflair, pauthor])
                    datalog("Updated user flair data: %s: '%s' > '%s'" % (pauthor, oldflair, pflair))
            sql.commit()
        except Exception as e:
            datalog("Error! {e}".format(e=e))
    except Exception as e:
        datalog("Error! {e}".format(e=e))
        
def scanposts():
    sub = r.get_subreddit(SUBREDDIT)
    posts = []
    posts += sub.get_new(limit=MAXPOSTS)
    posts += sub.get_comments(limit=MAXPOSTS)
    for post in posts:
        try:
            if cachepost(post.id):
                pauthor = post.author.name
                pcontent = post.body.lower()
                pflair = post.author_flair_css_class
                ptext = post.author_flair_text
                #CHECK FOR COMMANDS
                if SUBREDDIT == "Paladins":
                    if pauthor != "PaladinsRobot":
                        isMatch1 = re.search('(?i)match', pcontent)
                        isMatch2 = re.search('\d{8,11}', pcontent)
                        if isMatch1 and isMatch2:
                            datalog("%s requested the details of a match" % (pauthor))
                            matchID = isMatch2.group(0)
                            if matchID == "":
                                matchID = "0"
                            myplatform = ""
                            guruplatform = "pc"
                            xb1Match = re.search('(?i)xb1|xbox|match\/xb', pcontent)
                            ps4Match = re.search('(?i)ps4|playstation|match\/ps', pcontent)
                            if xb1Match:
                                smite._switch_endpoint(Endpoint.PALADINS_XBOX)
                                myplatform = "xbox."
                                guruplatform = "xb"
                            elif ps4Match:
                                smite._switch_endpoint(Endpoint.PALADINS_PS4)
                                myplatform = "ps4."
                                guruplatform = "ps"
                            else:
                                smite._switch_endpoint(Endpoint.PALADINS_PC)
                            post.reply(getMatchStats(matchID,myplatform,guruplatform))
                isMatch = any(string in pcontent for string in starhelp)
                if isMatch:
                    datalog("%s requested more information about me, writing reply" % (pauthor))
                    post.reply(MESSAGE_STARINFO)
                #if SUBREDDIT == "Smite":
                    #isMatch = any(string in pcontent for string in seasontickethelp)
                    #if isMatch:
                        #datalog("%s requested help with the Season Ticket, writing reply" % (pauthor))
                        #post.reply(seasonticketmaths())
                #CHECK FOR PRO PLAYERS
                if SUBREDDIT == "Smite":
                    if "\n"+pauthor+"\n" in open("splproplayers.txt").read():
                        if not pflair.endswith(" VER"):
                            datalog("Changing %s's flair from '%s' to '%s VER'" % (pauthor, pflair, pflair))
                            r.set_flair(SUBREDDIT, pauthor, ptext, pflair + " VER")
                #CHECK FOR HIREZ PERSONNEL
                if post.author_flair_css_class == "hirez":
                    plinkflairclass = post.submission.link_flair_css_class
                    plinkflairtext = post.submission.link_flair_text
                    if not plinkflairtext.endswith(" | HIREZ RESPONDED"):
                        datalog("%s made a comment. Changing %s flair" % (pauthor, plinkflairtext))
                        plinkflairtext = plinkflairtext + " | HIREZ RESPONDED"
                        r.set_flair(SUBREDDIT, post.submission, plinkflairtext, plinkflairclass)
                #COLLECT AND UPDATE FLAIR DATA
                updatedatabase(pauthor,pflair)
        except Exception as e:
            pass
    #ADD FLAIR DATA TO .TXT FILE
    if SUBREDDIT == "Smite":
        flairfile = open(SMITEFLAIRPRINTFILE, 'w')
    if SUBREDDIT == "Paladins":
        flairfile = open(PALADINSFLAIRPRINTFILE, 'w')    
    cur.execute('SELECT * FROM users')
    fetch = cur.fetchall()
    fetch.sort(key=lambda x: x[0])
    flaircounts = {}
    for item in fetch:
        itemflair = item[1].split(" ",1)[0]
        if itemflair not in flaircounts:
            flaircounts[itemflair] = 1
        else:
            flaircounts[itemflair] += 1
    print('FLAIR: NO. OF USERS WITH THAT FLAIR', file=flairfile)
    presorted = []
    for flairkey in flaircounts:
        presorted.append(flairkey + ': ' + str(flaircounts[flairkey]))
    presorted.sort()
    for flair in presorted:
        print(flair, file=flairfile)
    print('\n\n', file=flairfile)
    print('NAME: USER\'S FLAIR', file=flairfile)
    for user in fetch:
        print(user[0] + ': ' + user[1], file=flairfile)
    flairfile.close()

def testMessage(mauthor, mbody, message):
    print(mbody)

def testAPIfunction():
    print("Testing the API...")
    try:
        smite._switch_endpoint(Endpoint.PALADINS_PC)
        info = smite.get_player("edcellwarrior")
        print(info)
    except Exception as e:
        print("The API failed - %s" % (e))

while True:
    try:
        #testAPIfunction()
        #--------------------------
        smiteLogin()
        checkmail()
        scanposts()
        updateOperationalStatus()
        sql.commit()
        sql.close()
        #--------------------------
        paladinsLogin()
        #checkpost("t1_dm1hkfh")
        checkmail()
        scanposts()
        updateOperationalStatus()
        sql.commit()
        sql.close()
        #--------------------------
        #datalog("Running again in %s seconds..." % (str(WAIT)))
        time.sleep(WAIT)
    except Exception as e:
        datalog("Encountered error: '%s', running again in %s seconds" % (e, str(WAIT)))
        time.sleep(WAIT)
        try:
            import star
            r = praw.Reddit(USER_AGENT)
            smiteLogin()
        except:
            pass
