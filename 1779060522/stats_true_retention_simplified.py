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

def retentionAsString(n, d):
    return "%0.1f%%" % ((n * 100) / d) if d else "N/A"

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

    return [
        ypassed,
        yflunked,
        retentionAsString(ypassed, float(ypassed + yflunked)), 
        mpassed,
        mflunked,
        retentionAsString(mpassed, float(mpassed + mflunked)), 
        ypassed + mpassed,
        yflunked + mflunked,
        retentionAsString(ypassed + mpassed, float(ypassed + mpassed + yflunked + mflunked)), 
        learned,
        relearned]

def statsRow(name, values):
    return u"""
        <tr>
            <td class="trl">""" + name + """</td>
            <td class="trr"><span class="young">""" + str(values[0]) + u"""</span></td>
            <td class="trr"><span class="young">""" + str(values[1]) + u"""</span></td>
            <td class="trr"><span class="young"><i>""" + values[2] + u"""</i></span></td>
            <td class="trr"><span class="mature">""" + str(values[3]) + u"""</span></td>
            <td class="trr"><span class="mature">""" + str(values[4]) + u"""</span></td>
            <td class="trr"><span class="mature"><i>""" + values[5] + u"""</i></span></td>
            <td class="trr"><span class="yam">""" + str(values[6]) + u"""</span></td>
            <td class="trr"><span class="yam">""" + str(values[7]) + u"""</span></td>
            <td class="trr"><span class="yam"><i>""" + values[8] + u"""</i></span></td>
            <td class="trr"><span class="young">""" + str(values[9]) + u"""</span></td>
            <td class="trr"><span class="relearn">""" + str(values[10]) + u"""</span></td>
        </tr>"""

def todayStats(self):
    lim = self._revlogLimit()
    if lim:
        lim = u" and " + lim
    
    pastDay = statList(self, lim, (self.col.sched.dayCutoff-86400)*1000)

    pastSecondDay = statList(self, lim, (self.col.sched.dayCutoff-86400*2)*1000)
    pastSecondDay[0] -= pastDay[0]
    pastSecondDay[1] -= pastDay[1]
    pastSecondDay[2] = retentionAsString(pastSecondDay[0], pastSecondDay[0] + pastSecondDay[1])
    pastSecondDay[3] -= pastDay[3]
    pastSecondDay[4] -= pastDay[4]
    pastSecondDay[5] = retentionAsString(pastSecondDay[3], pastSecondDay[3] + pastSecondDay[4])
    pastSecondDay[6] = pastSecondDay[0] + pastSecondDay[3]
    pastSecondDay[7] = pastSecondDay[1] + pastSecondDay[4]
    pastSecondDay[8] = retentionAsString(pastSecondDay[6], pastSecondDay[6] + pastSecondDay[7])
    pastSecondDay[9] -= pastDay[9]
    pastSecondDay[10] -= pastDay[10]

    pastWeek = statList(self, lim, (self.col.sched.dayCutoff-86400*7)*1000)
    
    if self.type == 0:
        period = 31; pname = u"Month"
    elif self.type == 1:
        period = 365; pname = u"Year"
    elif self.type == 2:
        period = float('inf'); pname = u"Deck life"    
    pastPeriod = statList(self, lim, (self.col.sched.dayCutoff-86400*period)*1000)
    
    rv = todayStats_old(self)
    rv += anki.stats.CollectionStats._title(self, _("True Retention"), _("The true retention is calculated on learned cards only."))
    rv += u"""
        <style>
            td.trl { border: 1px solid; text-align: left }
            td.trr { border: 1px solid; text-align: right }
            td.trc { border: 1px solid; text-align: center }
            span.young { color: #77cc77 }
            span.mature { color: #00aa00 }
            span.yam { color: #55aa55 }
            span.relearn { color: #c35617 }
        </style>
        <br />
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
    rv += statsRow("Day", pastDay)
    rv += statsRow("Yesterday", pastSecondDay)
    rv += statsRow("Week", pastWeek)
    rv += statsRow(pname, pastPeriod)
    rv += "</table>"

    return rv

todayStats_old = anki.stats.CollectionStats.todayStats
anki.stats.CollectionStats.todayStats = todayStats
