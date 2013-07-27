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


import json, sys, os
from datetime import datetime
import requests
from pypump import PyPump
from requests_oauthlib import OAuth1

class Account():
    def __init__(self, client_name, webfinger, key=None, secret=None,
                 token=None, token_secret=None):

        self.following = None

        self.client_name = client_name
        self.webfinger = webfinger
        self.pump = PyPump(self.webfinger, key=key, secret=secret,
                           token=token, token_secret=token_secret,
                           client_name=self.client_name)

        self.key, self.secret, self.expiry = self.pump.get_registration()
        self.token, self.token_secret = self.pump.get_token()

        self.getFollowing()

    def getFollowing(self):
        self.following = []
        url = 'https://%s/api/user/%s/following' % (self.pump.server, self.pump.nickname)
        auth = OAuth1(self.key, self.secret, self.token, self.token_secret)

        while True:
            response = requests.get(url, auth=auth)
            following = json.loads(response.content)
            for item in following['items']:
                self.following.append(item['id'].split(':')[1])
            if 'next' in following['links']:
                url = following['links']['next']['href']
            else:
                break

    def follow(self, webfinger):
        try:
            # 'pypump=self.pump' is needed for now,
            # see https://github.com/xray7224/PyPump/issues/37
            return self.pump.Person(webfinger, pypump=self.pump).follow()
        except:
            return False

    def unfollow(self, webfinger):
        try:
            return self.pump.Person(webfinger, pypump=self.pump).unfollow()
        except:
            return False

    def followMany(self, contacts):
        for contact in contacts:
            # we dont want to follow ourselves
            if contact == self.webfinger:
                print(" Skipped: %s (your account)" % contact)
            # skip people we are already following
            elif contact in self.following:
                print(" Skipped: %s (already following)" % contact)
            elif self.follow(contact):
                print(" Followed: %s" % contact)
            else:
                print(" Failed: %s" % contact)

    def unfollowMany(self, contacts):
        for contact in contacts:
            # skip contacts we are not following
            if contact not in self.following:
                print(" Skipped %s (not following)" % contact)
            elif self.unfollow(contact):
                print(" Unfollowed: %s" % contact)
            else:
                print(" Failed: %s" % contact)

class Client():
    def __init__(self):
        self.client_name = 'pumpmigrate'
        self.cfgFile = os.path.join(os.environ['HOME'],'.config', self.client_name,'config.json')
        self.cacheDir = os.path.join(os.environ['HOME'],'.cache', self.client_name)

        self.cfg = {}
        self.accounts = {}
        self.account_aliases = ['old', 'new']

        self.loadCfg()
        for alias in self.account_aliases:
            self.accountSetup(alias)

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

    def accountSetup(self, alias):
        # Prompt for webfinger
        webfinger = raw_input('Enter webfinger (user@example.com) for your %s account: ' % alias)

        if webfinger in self.cfg:
            # Load account using stored auth info if found in config
            cfg = self.cfg[webfinger]
            self.accounts[alias] = Account(self.client_name,
                                          cfg['webfinger'],
                                          cfg['key'],
                                          cfg['secret'],
                                          cfg['token'],
                                          cfg['token_secret'])

        else:
            # Load account using only webfinger (this will ask user for auth) 
            # and write auth info to config
            self.accounts[alias] = Account(self.client_name, webfinger)

            self.cfg[webfinger] = {
                'webfinger':self.accounts[alias].webfinger,
                'key':self.accounts[alias].key,
                'secret':self.accounts[alias].secret,
                'token':self.accounts[alias].token,
                'token_secret':self.accounts[alias].token_secret
            }
            self.writeCfg()

        self.backupFollowing(self.accounts[alias])
        print('%s (following %s) loaded as %s account\n----' % (self.cfg[webfinger]['webfinger'],
                                                  len(self.accounts[alias].following),
                                                  alias))


    def promptEnter(self, msg):
        print(msg)
        try:
            raw_input("Hit enter to continue or ctrl+c to quit")
        except KeyboardInterrupt:
            sys.exit()

    def run(self):
        old = self.accounts['old']
        new = self.accounts['new']

        # follow contacts from old account
        self.promptEnter("%s will now follow %s new contacts" % (new.webfinger, len(old.following)))
        new.followMany(old.following)
        new.getFollowing()
        print("%s is now following %s contacts\n----" % (new.webfinger, len(new.following)))

        # unfollow contacts followed by both old and new
        oldandnew = [x for x in old.following if x in new.following]
        self.promptEnter("%s will now unfollow %s contacts" % (old.webfinger, len(oldandnew)))
        old.unfollowMany(oldandnew)
        old.getFollowing()
        print("%s is now following %s contacts\n----" % (old.webfinger, len(old.following)))

if __name__ == '__main__':
    app = Client()
    app.run()
