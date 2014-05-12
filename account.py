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
    app = None
    webfinger = None
    key = None
    secret = None
    token = None
    token_secret = None
    following = None
    cfg = None

    def __init__(self, webfinger, alias=None, app=None):
        self.app = app

        if not webfinger:
            self.webfinger = raw_input('Enter webfinger (user@example.com) for your %s account: ' % alias)
        else:
            self.webfinger = webfinger
            
        self.cfg = self.app.cfg.get(self.webfinger, {})

        client=Client(
            webfinger=self.webfinger,
            type='native',
            name=self.app.name,
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
        self.app.say('%s: account ready (following %s contacts)\n----' % (self.webfinger, len(self.following)))

    def verifier(self, url):
        print("Please open and follow the instructions:")
        print(url)
        return raw_input("Verifier: ").strip()

    def prompt_enter(self, msg):
        if self.app.parser.args.quiet and self.app.parser.args.noprompt:
            pass
        else:
            print(msg)
            if not self.app.parser.args.noprompt:
                try:
                    raw_input("Hit enter to continue or ctrl+c to quit")
                except KeyboardInterrupt:
                    sys.exit()

    def write_config(self):
        self.app.cfg[self.webfinger] = {
            'key':self.key,
            'secret':self.secret,
            'token':self.token,
            'token_secret':self.token_secret
        }
        self.app.write_config()

    def backup_following(self):
        self.app.backup_following(self)

    def get_following(self):
        self.app.say("%s: getting contacts (this may take a while)" % self.webfinger)
        self.following = list(self.pump.me.following)

    def follow_webfinger(self, webfinger):
        if self.app.parser.args.dryrun:
            return True

        try:
            obj = {
                "id":"acct:%s" % webfinger,
                "objectType":"person",
            }
            activity = {
                "verb":"follow",
                "object":obj,
                "to":[obj],
            }

            self.pump.me._post_activity(activity, unserialize=False)

            return True
        except:
            return False

    def unfollow_webfinger(self, webfinger):
        if self.app.parser.args.dryrun:
            return True
        try:
            obj = {
                "id":"acct:%s" % webfinger,
                "objectType":"person",
            }

            activity = {
                "verb":"stop-following",
                "object":obj,
                "to":[obj],
            }
            
            self.pump.me._post_activity(activity, unserialize=False)

            return True
        except:
            return False

    def follow_many(self, webfingers):
        self.prompt_enter("%s: will now follow %s new contacts" % (self.webfinger, len(webfingers)))

        for webfinger in webfingers:
            # we dont want to follow ourselves
            if webfinger == self.webfinger:
                self.app.say(" Skipped: %s (your account)" % webfinger)
            # skip people we are already following
            elif webfinger in [i.webfinger for i in self.following]:
                self.app.say(" Skipped: %s (already following)" % webfinger)
            elif self.follow_webfinger(webfinger):
                self.app.say(" Followed: %s" % webfinger)
            else:
                self.app.say(" Failed: %s" % webfinger)

        self.get_following()
        self.app.say("%s: now following %s contacts\n----" % (self.webfinger, len(self.following)))

    def unfollow_many(self, webfingers):
        self.prompt_enter("%s: will now unfollow %s contacts" % (self.webfinger, len(webfingers)))

        for webfinger in webfingers:
            # skip contacts we are not following
            if webfinger not in [i.webfinger for i in self.following]:
                self.app.say(" Skipped %s (not following)" % webfinger)
            elif self.unfollow_webfinger(webfinger):
                self.app.say(" Unfollowed: %s" % webfinger)
            else:
                self.app.say(" Failed: %s" % webfinger)

        self.get_following()
        self.app.say("%s: now following %s contacts\n----" % (self.webfinger, len(self.following)))
