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

import sys
from pypump import PyPump, Client

class Account(object):
    _app = None
    webfinger = None
    key = None
    secret = None
    token = None
    token_secret = None
    following = None
    cfg = None

    def __init__(self, webfinger, alias=None, client=None):
        self._app = client

        if not webfinger:
            self.webfinger = raw_input('Enter webfinger (user@example.com) for your %s account: ' % alias)
        else:
            self.webfinger = webfinger
            
        self.cfg = self._app.cfg.get(self.webfinger, {})

        client=Client(
            webfinger=self.webfinger,
            type='native',
            name=self._app.name,
            key=self.cfg.get('key'),
            secret=self.cfg.get('secret')
        )

        self.pump = PyPump(
            client=client,
            verifier_callback=self.verifier,
            token=self.cfg.get('token'),
            secret=self.cfg.get('token_secret')
        )

        self.key, self.secret, self.expiry = self.pump.get_registration()
        self.token, self.token_secret = self.pump.get_token()
        self.write_config()

        self.get_following()
        self.backup_following()
        self._app.say('%s: account ready (following %s contacts)\n----' % (self.webfinger, len(self.following)))

    def verifier(self, url):
        print("Please open and follow the instructions:")
        print(url)
        return raw_input("Verifier: ").strip()

    def prompt_enter(self, msg):
        if self._app.parser.args.quiet and self._app.parser.args.noprompt:
            pass
        else:
            print(msg)
            if not self._app.parser.args.noprompt:
                try:
                    raw_input("Hit enter to continue or ctrl+c to quit")
                except KeyboardInterrupt:
                    sys.exit()

    def write_config(self):
        self._app.cfg[self.webfinger] = {
            'key':self.key,
            'secret':self.secret,
            'token':self.token,
            'token_secret':self.token_secret
        }
        self._app.write_config()

    def backup_following(self):
        self._app.backup_following(self)

    def get_following(self):
        self._app.say("%s: getting contacts (this may take a while)" % self.webfinger)
        self.following = []

        for i in self.pump.me.following:
            self.following.append(i.webfinger)

    def follow(self, webfinger):
        if self._app.parser.args.dryrun:
            return True
        try:
            self.pump.Person(webfinger).follow()
            return True
        except:
            return False

    def unfollow(self, webfinger):
        if self._app.parser.args.dryrun:
            return True
        try:
            self.pump.Person(webfinger).unfollow()
            return True
        except:
            return False

    def follow_many(self, contacts):
        self.prompt_enter("%s: will now follow %s new contacts" % (self.webfinger, len(contacts)))

        for contact in contacts:
            # we dont want to follow ourselves
            if contact == self.webfinger:
                self._app.say(" Skipped: %s (your account)" % contact)
            # skip people we are already following
            elif contact in self.following:
                self._app.say(" Skipped: %s (already following)" % contact)
            elif self.follow(contact):
                self._app.say(" Followed: %s" % contact)
            else:
                self._app.say(" Failed: %s" % contact)

        self.get_following()
        self._app.say("%s: now following %s contacts\n----" % (self.webfinger, len(self.following)))

    def unfollow_many(self, contacts):
        self.prompt_enter("%s: will now unfollow %s contacts" % (self.webfinger, len(contacts)))

        for contact in contacts:
            # skip contacts we are not following
            if contact not in self.following:
                self._app.say(" Skipped %s (not following)" % contact)
            elif self.unfollow(contact):
                self._app.say(" Unfollowed: %s" % contact)
            else:
                self._app.say(" Failed: %s" % contact)

        self.get_following()
        self._app.say("%s: now following %s contacts\n----" % (self.webfinger, len(self.following)))
