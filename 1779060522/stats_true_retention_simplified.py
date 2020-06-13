# -*- coding: utf-8 -*-

"""
Simplified version of the True Retention by Card Maturity Add-on
(https://ankiweb.net/shared/info/923360400)

License: GNU AGPLv3 or later <https://www.gnu.org/licenses/agpl.html>
"""

from __future__ import unicode_literals

############## USER CONFIGURATION START ##############

MATURE_IVL = 21 # mature card interval in days

##############  USER CONFIGURATION END  ##############

import anki.stats

from anki.utils import fmtTimeSpan
from anki.lang import _, ngettext
from anki import version as anki_version


# Types: 0 - new today; 1 - review; 2 - relearn; 3 - (cram?) [before the answer was pressed]
# "Learning" corresponds to New|Relearn. "Review" corresponds to Young|Mature.
# Ease: 1 - flunk button; 2 - second; 3 - third; 4 - fourth (easy) [which button was pressed]
# Intervals: -60 <1m -600 10m etc; otherwise days

def statList(self, lim, span):
    yflunked, ypassed, mflunked, mpassed, learned, relearned = self.col.db.first("""
    select
    sum(case when lastIvl < %(i)d and ease = 1 and type == 1 then 1 else 0 end), /* flunked young */
    sum(case when lastIvl < %(i)d and ease > 1 and type == 1 then 1 else 0 end), /* passed young */
    sum(case when lastIvl >= %(i)d and ease = 1 and type == 1 then 1 else 0 end), /* flunked mature */
    sum(case when lastIvl >= %(i)d and ease > 1 and type == 1 then 1 else 0 end), /* passed mature */
    sum(case when ivl > 0 and type == 0 then 1 else 0 end), /* learned */
    sum(case when ivl > 0 and type == 2 then 1 else 0 end) /* relearned */
    from revlog where id > ? """ % dict(i=MATURE_IVL) +lim, span)
    yflunked, mflunked = yflunked or 0, mflunked or 0
    ypassed, mpassed = ypassed or 0, mpassed or 0
    learned, relearned = learned or 0, relearned or 0

    # True retention
    # young
    try:
        yret = "%0.1f%%" %(ypassed/float(ypassed+yflunked)*100)
    except ZeroDivisionError:
        yret = "N/A"
    # mature
    try:
        mret = "%0.1f%%" %(mpassed/float(mpassed+mflunked)*100)
    except ZeroDivisionError:
        mret = "N/A"
    # total
    try:
        tret = "%0.1f%%" %((ypassed+mpassed)/float(ypassed+mpassed+yflunked+mflunked)*100)
    except ZeroDivisionError:
        tret = "N/A"
    
    return (
        str(ypassed), str(yflunked), yret, 
        str(mpassed), str(mflunked), mret, 
        str(ypassed+mpassed), str(yflunked+mflunked), tret, 
        str(learned), str(relearned))

def todayStats_new(self):
    lim = self._revlogLimit()
    if lim:
        lim = u" and " + lim
    
    pastDay = statList(self, lim, (self.col.sched.dayCutoff-86400)*1000)
    pastWeek = statList(self, lim, (self.col.sched.dayCutoff-86400*7)*1000)
    
    if self.type == 0:
        period = 31; pname = u"Month"
    elif self.type == 1:
        period = 365; pname = u"Year"
    elif self.type == 2:
        period = float('inf'); pname = u"Deck life"
    
    pastPeriod = statList(self, lim, (self.col.sched.dayCutoff-86400*period)*1000)
    
    todayStats = todayStats_old(self)
    todayStats += anki.stats.CollectionStats._title(self, _("True Retention"), _("The true retention is calculated on learned cards only."))
    todayStats +=u"""
    <style>
        td.trl { border: 1px solid; text-align: left }
        td.trr { border: 1px solid; text-align: right }
        td.trc { border: 1px solid; text-align: center }
        span.young { color: #77cc77 }
        span.mature { color: #00aa00 }
        span.yam { color: #55aa55 }
        span.relearn { color: #c35617 }
    </style>"""
    todayStats += u"""
    <table style="border-collapse: collapse;" cellspacing="0" cellpadding="2">
        <tr>
            <td class="trl" rowspan=3><b>Past</b></td>
            <td class="trc" colspan=9><b>Reviews on Cards</b></td>
            <td class="trc" colspan=2 valign=middle><b>Cards</b></td>
        </tr>
        <tr>
            <td class="trc" colspan=3><span class="young"><b>Young</b></span></td>
            <td class="trc" colspan=3><span class="mature"><b>Mature</b></span></td>
            <td class="trc" colspan=3><span class="yam"><b>Young and Mature</b></span></td>
            <td class="trc" rowspan=2><span class="young"><b>Graduated</b></span></td>
            <td class="trc" rowspan=2><span class="relearn"><b>Relearned</b></span></td>
        </tr>
        <tr>
            <td class="trc"><span class="young">Pass</span></td>
            <td class="trc"><span class="young">Fail</span></td>
            <td class="trc"><span class="young"><i>Retention</i></span></td>
            <td class="trc"><span class="mature">Pass</span></td>
            <td class="trc"><span class="mature">Fail</span></td>
            <td class="trc"><span class="mature"><i>Retention</i></span></td>
            <td class="trc"><span class="yam">Pass</span></td>
            <td class="trc"><span class="yam">Fail</span></td>
            <td class="trc"><span class="yam"><i>Retention</i></span></td>
        </tr>"""

    todayStats += u"""
        <tr>
            <td class="trl">Day</td>
            <td class="trr"><span class="young">""" + pastDay[0] + u"""</span></td>
            <td class="trr"><span class="young">""" + pastDay[1] + u"""</span></td>
            <td class="trr"><span class="young"><i>""" + pastDay[2] + u"""</i></span></td>
            <td class="trr"><span class="mature">""" + pastDay[3] + u"""</span></td>
            <td class="trr"><span class="mature">""" + pastDay[4] + u"""</span></td>
            <td class="trr"><span class="mature"><i>""" + pastDay[5] + u"""</i></span></td>
            <td class="trr"><span class="yam">""" + pastDay[6] + u"""</span></td>
            <td class="trr"><span class="yam">""" + pastDay[7] + u"""</span></td>
            <td class="trr"><span class="yam"><i>""" + pastDay[8] + u"""</i></span></td>
            <td class="trr"><span class="young">""" + pastDay[9] + u"""</span></td>
            <td class="trr"><span class="relearn">""" + pastDay[10] + u"""</span></td>
        </tr>"""

    todayStats += u"""
        <tr>
            <td class="trl">Week</td>
            <td class="trr"><span class="young">""" + pastWeek[0] + u"""</span></td>
            <td class="trr"><span class="young">""" + pastWeek[1] + u"""</span></td>
            <td class="trr"><span class="young"><i>""" + pastWeek[2] + u"""</i></span></td>
            <td class="trr"><span class="mature">""" + pastWeek[3] + u"""</span></td>
            <td class="trr"><span class="mature">""" + pastWeek[4] + u"""</span></td>
            <td class="trr"><span class="mature"><i>""" + pastWeek[5] + u"""</i></span></td>
            <td class="trr"><span class="yam">""" + pastWeek[6] + u"""</span></td>
            <td class="trr"><span class="yam">""" + pastWeek[7] + u"""</span></td>
            <td class="trr"><span class="yam"><i>""" + pastWeek[8] + u"""</i></span></td>
            <td class="trr"><span class="young">""" + pastWeek[9] + u"""</span></td>
            <td class="trr"><span class="relearn">""" + pastWeek[10] + u"""</span></td>
        </tr>"""

    todayStats += u"""
        <tr>
            <td class="trl">""" + pname + u"""</td>
            <td class="trr"><span class="young">""" + pastPeriod[0] + u"""</span></td>
            <td class="trr"><span class="young">""" + pastPeriod[1] + u"""</span></td>
            <td class="trr"><span class="young"><i>""" + pastPeriod[2] + u"""</i></span></td>
            <td class="trr"><span class="mature">""" + pastPeriod[3] + u"""</span></td>
            <td class="trr"><span class="mature">""" + pastPeriod[4] + u"""</span></td>
            <td class="trr"><span class="mature"><i>""" + pastPeriod[5] + u"""</i></span></td>
            <td class="trr"><span class="yam">""" + pastPeriod[6] + u"""</span></td>
            <td class="trr"><span class="yam">""" + pastPeriod[7] + u"""</span></td>
            <td class="trr"><span class="yam"><i>""" + pastPeriod[8] + u"""</i></span></td>
            <td class="trr"><span class="young">""" + pastPeriod[9] + u"""</span></td>
            <td class="trr"><span class="relearn">""" + pastPeriod[10] + u"""</span></td>
        </tr>
    </table>"""

    return todayStats

todayStats_old = anki.stats.CollectionStats.todayStats
anki.stats.CollectionStats.todayStats = todayStats_new
