# AGPLv3
# Copyright (c) 2013 Steve AW
#           (c) 2016-2017 Glutanimate
#           (c) 2019 ijgnd


import datetime
from pprint import pprint as pp

from anki.hooks import wrap
import aqt
from aqt import gui_hooks
from aqt.overview import Overview


def gc(arg, fail=False):
    return aqt.mw.addonManager.getConfig(__name__).get(arg, fail)


def whenIsNextLrnDue():
    did = str(aqt.mw.col.decks.current()["id"])
    o = aqt.mw.col.db.all("""select id, due from cards where queue = 1 and did = """ + did + """ order by due""")
    if o:
        o = dict(o)
        now = datetime.datetime.now()
        # dayOffset - next day starts at
        # in 2.1.14 values can be between 0 and 23, no negative values
        if aqt.mw.col.schedVer() == 2:
            dayOffset = aqt.mw.col.conf['rollover']   # by default 4
        else:
            # https://github.com/ankidroid/Anki-Android/wiki/Database-Structure
            #   crt = timestamp of the creation date. It's correct up to the day. For V1 scheduler,
            #   the hour corresponds to starting a new day. By default, new day is 4.
            dayOffset = datetime.datetime.fromtimestamp(aqt.mw.col.crt).hour

        now = datetime.datetime.today()     # returns the current local date.
                                            # This is equivalent to date.fromtimestamp(time.time())
        if now.hour < dayOffset:
            now = now - datetime.timedelta(days=1)
        todaystart = datetime.datetime(year=now.year, month=now.month,
                                       day=now.day, hour=dayOffset, second=0)
        todaystartepoch = int(todaystart.timestamp())
        for c in sorted(list(o.values())):
            if c < todaystartepoch:
                continue
            for k, v in o.items():
                if v == c:
                    cid = k
                    break
            # pp('###########' + str(cid) + '    ' + str(c))
            cdo = datetime.datetime.fromtimestamp(c)
            if gc("time_with_seconds", True):
                f = "%H:%M:%S"
            else:
                f = "%H:%M"
            tstr = '''<a href=# style="text-decoration: none; color:black;"
            onclick="return pycmd('BrowserSearch#%s')">%s (%s)</a>''' % (str(cid), cdo.strftime(f), timeInAgo(cdo))
            msg = gc("sentence_beginning", "The next learning card due today is due at ") + tstr
            return "<div>" + msg + "</div>"
    else:
        return ""

def timeInAgo(t):
    zero = datetime.timedelta(0)
    now = datetime.datetime.now()
    td = t - now
    due_later = True
    if td < zero:
        due_later = False
        td = now - t
    if int(td.total_seconds()) == 0:
        return "now"
    hours = int(td.total_seconds()/3600)
    minutes = int(td.total_seconds()/60 % 60)
    seconds = int(td.total_seconds() % 60)
    msg = ""
    if hours:
        msg += "%dh" % (hours)
    if minutes:
        msg += "%dm" % (minutes)
    msg += "%ds" % (seconds)
    if due_later:
        msg = "in " + msg
    else:
        msg += " ago"
    return msg

def addRemainingTimeToDesc(overview, content):
    content.desc += whenIsNextLrnDue()

gui_hooks.overview_will_render_content.append(addRemainingTimeToDesc)

def openBrowser(searchterm):
    browser = aqt.dialogs.open("Browser", aqt.mw)
    browser.form.searchEdit.lineEdit().setText(searchterm)
    browser.onSearchActivated()
    if u'noteCrt' in browser.model.activeCols:
        col_index = browser.model.activeCols.index(u'noteCrt')
        browser.onSortChanged(col_index, True)
    browser.form.tableView.selectRow(0)


def myLinkHandler(self, url, _old):
    if url.startswith("BrowserSearch#"):
        out = url.replace("BrowserSearch#", "").split("#", 1)[0]
        openBrowser("cid:" + out)
    else:
        return _old(self, url)
Overview._linkHandler = wrap(Overview._linkHandler, myLinkHandler, "around")
