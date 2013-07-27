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

class Account(object):
    _client = None
    webfinger = None
    key = None
    secret = None
    token = None
    token_secret = None
    following = None
    cfg = None

    def __init__(self, webfinger, alias=None, client=None):
        self._client = client

        if not webfinger:
            self.webfinger = raw_input('Enter webfinger (user@example.com) for your %s account: ' % alias)
        else:
            self.webfinger = webfinger
            
        self.cfg = self._client.cfg.get(self.webfinger, {})

        self.pump = PyPump(self.webfinger, client_name=self._client.name, **self.cfg)
        self.key, self.secret, self.expiry = self.pump.get_registration()
        self.token, self.token_secret = self.pump.get_token()
        self.writeCfg()

        self.getFollowing()
        self.backupFollowing()
        print('%s (following %s) loaded as %s account\n----' % (self.webfinger, len(self.following), alias))

    def promptEnter(self, msg):
        print(msg)
        try:
            raw_input("Hit enter to continue or ctrl+c to quit")
        except KeyboardInterrupt:
            sys.exit()

    def writeCfg(self):
        self._client.cfg[self.webfinger] = {
            'key':self.key,
            'secret':self.secret,
            'token':self.token,
            'token_secret':self.token_secret
        }
        self._client.writeCfg()

    def backupFollowing(self):
        self._client.backupFollowing(self)

    def getFollowing(self):
        print("Loading contacts for %s (this may take a while)" % self.webfinger)
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
        if self._client.dryrun:
            return True
        try:
            # 'pypump=self.pump' is needed for now,
            # see https://github.com/xray7224/PyPump/issues/37
            return self.pump.Person(webfinger, pypump=self.pump).follow()
        except:
            return False

    def unfollow(self, webfinger):
        if self._client.dryrun:
            return True
        try:
            return self.pump.Person(webfinger, pypump=self.pump).unfollow()
        except:
            return False

    def followMany(self, contacts):
        self.promptEnter("%s will now follow %s new contacts" % (self.webfinger, len(contacts)))

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

        self.getFollowing()
        print("%s is now following %s contacts\n----" % (self.webfinger, len(self.following)))

    def unfollowMany(self, contacts):
        self.promptEnter("%s will now unfollow %s contacts" % (self.webfinger, len(contacts)))

        for contact in contacts:
            # skip contacts we are not following
            if contact not in self.following:
                print(" Skipped %s (not following)" % contact)
            elif self.unfollow(contact):
                print(" Unfollowed: %s" % contact)
            else:
                print(" Failed: %s" % contact)

        self.getFollowing()
        print("%s is now following %s contacts\n----" % (self.webfinger, len(self.following)))
