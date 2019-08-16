# AGPLv3
# Copyright ijgnd 2019

import datetime
from pprint import pprint as pp

from anki.hooks import wrap
from aqt import mw
from aqt.deckbrowser import DeckBrowser


def gc(arg, fail=False):
    return mw.addonManager.getConfig(__name__).get(arg, fail)


def whenIsNextLrnDue():
    p = mw.col.db.list("""select due from cards where queue = 1 order by due""")
    if p:
        now = datetime.datetime.now()
        # dayOffset - next day starts at
        if mw.col.schedVer() == 2:
            dayOffset = mw.col.conf['rollover']   # by default 4
        else:
            # https://github.com/ankidroid/Anki-Android/wiki/Database-Structure
            #     crt = timestamp of the creation date. It's correct up to the day. 
            #     For V1 scheduler, the hour corresponds to starting a new day. By default, new day is 4.
            dayOffset = datetime.datetime.fromtimestamp(mw.col.crt).hour
        
        now = datetime.datetime.today() # returns the current local date. This is equivalent to date.fromtimestamp(time.time())
        if now.hour < dayOffset:
            myday = now.day - 1
        else:
            myday = now.day
        todaystart = datetime.datetime(year=now.year, month=now.month,
                    day=myday, hour=dayOffset, second=0)
        todaystartepoch = int(todaystart.timestamp())
        for c in p:
            if c < todaystartepoch:
                continue
            cdo = datetime.datetime.fromtimestamp(c)
            if gc("time_with_seconds",True):
                fmt = "%H:%M:%S"
            else:
                fmt = "%H:%M"
            msg = gc("sentence_beginning","The next learning card due today is due at ") + cdo.strftime(fmt)
            return "<div>" + msg + "</div>"
    else:
        return ""


def deckbrowserMessage(self, _old):
    if whenIsNextLrnDue():
        return _old(self) + whenIsNextLrnDue()
    else:
        return _old(self)
DeckBrowser._renderStats = wrap(DeckBrowser._renderStats, deckbrowserMessage, "around")
