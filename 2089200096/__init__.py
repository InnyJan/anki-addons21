# -*- coding: utf-8 -*-
# Copyright: Damien Elmes (http://help.ankiweb.net)
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html

from aqt import mw
from aqt.qt import *
from anki.hooks import addHook
from aqt.utils import showInfo, askUser
from anki.utils import ids2str, intTime


# Modified copy of `Scheduler.reschedCards' that doesn't change `ease' factor.
def reschedCards(scheduler, cids):
    "Put cards in review queue with a new interval of 1 day."
    d = []
    due = scheduler.today
    usn = scheduler.col.usn()
    mod = intTime()
    for id in cids:
        d.append((due, usn, mod, id,))
    scheduler.remFromDyn(cids)
    scheduler.col.db.executemany(
        f"""
update cards set odue=0,reps=0,lapses=0,ivl=1,
due=?,usn=?,mod=? where id=?""",
        d,
    )
    scheduler.col.log(cids)

def onResetCards(browser):
    cids = browser.selectedCards()
    if not cids:
        showInfo("No cards selected.")
        return
    if not askUser("Are you sure you wish to reset the selected cards?"):
        return

    mw.col.modSchema(check=True)
    mw.progress.start(immediate=True)
    mw.col.db.execute("delete from revlog where cid in " + ids2str(cids))
    
    # Reschedule cards for today and reset `reps' and `lapses' counters.
    reschedCards(mw.col.sched, cids)
    
    mw.col.setMod()
    mw.col.save()
    mw.progress.finish()

    browser.model.reset()
    mw.requireReset()

    showInfo("Reset %d cards" % len(cids))

def onMenuSetup(browser):
    act = QAction(browser)
    act.setText("Reset Cards")
    mn = browser.form.menu_Cards
    mn.addSeparator()
    mn.addAction(act)
    act.triggered.connect(lambda b=browser: onResetCards(browser))

addHook("browser.setupMenus", onMenuSetup)
