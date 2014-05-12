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

class App():
    name = 'pumpmigrate'
    version = '0.3.0'

    def __init__(self):
        self.cfgFile = os.path.join(os.environ['HOME'],'.config', self.name,'accounts.json')
        self.cacheDir = os.path.join(os.environ['HOME'],'.cache', self.name)

        self.cfg = {}
        self.accounts = {}
        self.load_config()

        self.parser = Parser(self)

    def say(self, msg):
        if not self.parser.args.quiet:
            print(msg)

    def write_config(self):
        if not os.path.exists(os.path.dirname(self.cfgFile)):
            os.makedirs(os.path.dirname(self.cfgFile))
        with open(self.cfgFile, 'w') as f:
            f.write(json.dumps(self.cfg))
            f.close()
    
    def load_config(self):
        try:
            with open(self.cfgFile, 'r') as f:
                self.cfg = json.loads(f.read())
                f.close()
        except IOError:
            return False
        return True

    def backup_following(self, acct):
        tstamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backupFile = os.path.join(self.cacheDir, "%s_following_%s.json" % (acct.webfinger, tstamp))
        if not os.path.exists(os.path.dirname(backupFile)):
            os.makedirs(os.path.dirname(backupFile))
        with open(backupFile, 'w') as f:
            f.write(json.dumps([p.webfinger for p in acct.following]))
            f.close()

    def move(self, *args, **kwargs):
        aliases = ['old', 'new']
        webfingers = self.parser.args.webfingers or [None, None]
        for alias, webfinger in zip(aliases, webfingers):
            self.accounts[alias] = Account(webfinger, alias=alias, app=self)
        old = self.accounts['old']
        new = self.accounts['new']
        # make new follow contacts from old account
        if not self.parser.args.nofollow:
            old_wf = set([o.webfinger for o in old.following])
            new.follow_many(old_wf)

        # make old unfollow contacts if they are in both old and new
        if not self.parser.args.nounfollow:
            old_wf = set([o.webfinger for o in old.following])
            new_wf = set([n.webfinger for n in new.following])
            inboth_wf = old_wf & new_wf

            old.unfollow_many(inboth_wf)

    def sync(self, *args, **kwargs):
        aliases = ['first', 'second']
        webfingers = self.parser.args.webfingers or [None, None]
        for alias, webfinger in zip(aliases, webfingers):
            self.accounts[alias] = Account(webfinger, alias=alias, app=self)

        first = self.accounts['first']
        second = self.accounts['second']
        first_wf = set([f.webfinger for f in first.following])
        second_wf = set([s.webfinger for s in second.following])
        andor_wf = first_wf | second_wf

        first.follow_many(andor_wf - first_wf)
        second.follow_many(andor_wf - second_wf)

    def load(self, *args, **kwargs):
        alias = 'first'
        webfinger = self.parser.args.webfinger or None

        fn = self.parser.args.filename or None
        with open(fn, 'r') as f:
            webfingers_list = json.loads(f.read())
            f.close()

        self.accounts[alias] = Account(webfinger, alias=alias, app=self)
        acct = self.accounts[alias]

        acct.follow_many(webfingers_list)
        

    def run(self):
        self.parser.args.func(self.parser.args)

if __name__ == '__main__':
    app = App()
    app.run()
