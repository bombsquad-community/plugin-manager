"""                         MythB # http://github.com/MythB
mystats module for BombSquad version 1.4.143
Provides functionality for dumping player stats to disk between rounds.
To use this, add the following 2 lines to bsGame.ScoreScreenActivity.onBegin():
import MythBStats
MythBStats.update(self.scoreSet) 
"""
import threading
import json
import os
import urllib2
import fcntl
import time
# where our stats file and pretty html output will go
statsfile = '/root/bs/stats/stats.json'
htmlfile = '/root/bs/stats/statspage.html'
#statsfile = 'C:\Users\MythB\Desktop\SERVER STATS\stats.json'
#htmlfile = 'C:\Users\MythB\Desktop\SERVER STATS\statspage.html'
#Use your own file location here
def update(score_set):
    #look at score-set entries to tally per-account kills for this round
    account_kills = {}
    account_killed = {}
    account_scores = {}
    account_played = {}
    account_name = {}
    for p_entry in score_set.getValidPlayers().values():
        account_id = p_entry.getPlayer().get_account_id()
        if account_id is not None:
            account_kills.setdefault(account_id, 0)
            account_kills[account_id] += p_entry.accumKillCount
            account_killed.setdefault(account_id, 0)
            account_killed[account_id] += p_entry.accumKilledCount
            account_scores.setdefault(account_id, 0)
            account_scores[account_id] += p_entry.accumScore
            account_played.setdefault(account_id, 0)
            account_played[account_id] += 1
            account_name.setdefault(account_id, p_entry.nameFull)
            account_name[account_id] = p_entry.nameFull
    # Ok; now we've got a dict of account-ids and kills.
    # Now lets kick off a background thread to load existing scores
    # from disk, do display-string lookups for accounts that need them,
    # and write everything back to disk (along with a pretty html version)
    # We use a background thread so our server doesn't hitch while doing this.
    UpdateThread(account_kills,account_killed,account_scores,account_played,account_name).start()
class UpdateThread(threading.Thread):
    def __init__(self, account_kills, account_killed, account_scores, account_played, account_name):
        threading.Thread.__init__(self)
        self._account_kills = account_kills
        self._account_killed = account_killed
        self._account_scores = account_scores
        self._account_played = account_played
        self._account_name = account_name
    def run(self):
        # pull our existing stats from disk
        if os.path.exists(statsfile):
            while True:
                try:
                    with open(statsfile) as f:
                        stats = json.loads(f.read())
                        break
                except Exception as (e):
                    print e
                    time.sleep(0.05)
        else:
            stats = {}
            
        # now add this batch of kills to our persistant stats
        for account_id, kill_count in self._account_kills.items():
            # add a new entry for any accounts that dont have one
            if account_id not in stats:
                # also lets ask the master-server for their account-display-str.
                # (we only do this when first creating the entry to save time,
                # though it may be smart to refresh it periodically since
                # it may change)
                url = 'http://bombsquadgame.com/accountquery?id=' + account_id
                response = json.loads(
                    urllib2.urlopen(urllib2.Request(url)).read())
                name_html = response['name_html']
                stats[account_id] = {'kills': 0, 'killed': 0, 'scores': 0, 'played': 0, 'name_html': name_html}
            # now increment their kills whether they were already there or not
            stats[account_id]['kills'] += kill_count
        for account_id, killed_count in self._account_killed.items():
            stats[account_id]['killed'] += killed_count
        for account_id, scores_count in self._account_scores.items():
            stats[account_id]['scores'] += scores_count
        for account_id, played_count in self._account_played.items():
            stats[account_id]['played'] += played_count
        for account_id, name in self._account_name.items():
            stats[account_id]['name_full'] = name
            
        # dump our stats back to disk
        #import fcntl
        while True:
            try:
                with open(statsfile, 'w') as f:
                    fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    f.write(json.dumps(stats,indent=4))
                    f.flush()
                    fcntl.flock(f, fcntl.LOCK_UN)
                    
                # lastly, write a pretty html version.
                # our stats url could point at something like this...
                entries = [(a['kills'], a['killed'], a['scores'], a['played'], a['name_html']) for a in stats.values()]
                # this gives us a list of kills/names sorted high-to-low
                entries.sort(reverse=True)
                with open(htmlfile, 'w') as f:
                    f.write('<head><meta charset="UTF-8"></head><body>')
                    for entry in entries:
                        kills = str(entry[0])
                        killed = str(entry[1])
                        scores = str(entry[2])
                        played = str(entry[3])
                        name = entry[4].encode('utf-8')
                        f.write(kills + ' kills ' + killed + ' deaths ' + scores + ' score ' + played + ' games : ' + name + '<br>')
                    f.write('</body>') 
                    break
            except Exception as (e):
                print e
                time.sleep(0.05)
            
            
        # aaand that's it!  There IS no step 27!
        from datetime import datetime
        msgTime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print 'Added',len(self._account_played),'  Log entries.  ' ,msgTime
        