#!/usr/bin/env python
##
# This program is free software: you can redistribute it and/or modify 
# it under the terms of the GNU General Public License as published by 
# the Free Software Foundation, either version 3 of the License, or 
# (at your option) any later version. 
# 
# This program is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the 
# GNU General Public License for more details. 
# 
# You should have received a copy of the GNU General Public License 
# along with this program. If not, see <http://www.gnu.org/licenses/>.
##


import json, os
from datetime import datetime
from account import Account
from parser import Parser

class Client():
    name = 'pumpmigrate'

    def __init__(self):
        self.cfgFile = os.path.join(os.environ['HOME'],'.config', self.name,'accounts.json')
        self.cacheDir = os.path.join(os.environ['HOME'],'.cache', self.name)

        self.cfg = {}
        self.accounts = {}
        self.loadCfg()

        Parser(self)

    def writeCfg(self):
        if not os.path.exists(os.path.dirname(self.cfgFile)):
            os.makedirs(os.path.dirname(self.cfgFile))
        with open(self.cfgFile, 'w') as f:
            f.write(json.dumps(self.cfg))
            f.close()
    
    def loadCfg(self):
        try:
            with open(self.cfgFile, 'r') as f:
                self.cfg = json.loads(f.read())
                f.close()
        except IOError:
            return False
        return True

    def backupFollowing(self, acct):
        tstamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backupFile = os.path.join(self.cacheDir, "%s_following_%s.json" % (acct.webfinger, tstamp))
        if not os.path.exists(os.path.dirname(backupFile)):
            os.makedirs(os.path.dirname(backupFile))
        with open(backupFile, 'w') as f:
            f.write(json.dumps(acct.following))
            f.close()

    def migrate(self, *args, **kwargs):
        aliases = ['old', 'new']
        webfingers = self.webfingers or [None, None]
        for alias, webfinger in zip(aliases, webfingers):
            self.accounts[alias] = Account(webfinger, alias=alias, client=self)
        old = self.accounts['old']
        new = self.accounts['new']
        # follow contacts from old account
        new.followMany(old.following)
        # unfollow contacts if they are in both old and new
        if not self.nounfollow:
            inboth = set(old.following) & set(new.following)
            old.unfollowMany(inboth)

    def sync(self, *args, **kwargs):
        aliases = ['first', 'second']
        webfingers = self.webfingers or [None, None]
        for alias, webfinger in zip(aliases, webfingers):
            self.accounts[alias] = Account(webfinger, alias=alias, client=self)
        first = self.accounts['first']
        second = self.accounts['second']
        andor = set(first.following) | set(second.following)
        first.followMany(andor)
        second.followMany(andor)


if __name__ == '__main__':
    app = Client()
