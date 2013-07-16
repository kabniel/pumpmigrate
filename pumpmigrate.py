#!/usr/bin/env python

import json
import requests
from clint import resources as res
from pypump import PyPump
from requests_oauthlib import OAuth1

class Account():
    def __init__(self, client_name, webfinger, key=None, secret=None, token=None, token_secret=None):
        self.client_name = client_name
        self.webfinger = webfinger
        self.key = key
        self.secret = secret
        self.token = token
        self.token_secret = token_secret
        self.following = []
        self.uniquefollows = []
        self.pump = PyPump(self.webfinger, key=self.key, secret=self.secret, token=self.token, token_secret=self.token_secret, client_name=self.client_name)

        self.getFollowing()

    def getFollowing(self):
        # Grab contacts followed from account
        if not res.cache.read('%s_at_%s_follows.json' % (self.pump.nickname, self.pump.server)):
            url = 'https://%s/api/user/%s/following?count=200' % (self.pump.server, self.pump.nickname)
            auth = OAuth1(self.key, self.secret, self.token, self.token_secret)
            try:
                following = json.loads(requests.get(url, auth=auth).content)
            except Exception as e:
                print 'couldnt get followers, %s' % e.message
                return
            for item in following['items']:
                self.following.append(item['id'].split(':')[1])
            res.cache.write('%s_at_%s_follows.json' % (self.pump.nickname, self.pump.server),
                            json.dumps(self.following))
        else:
            self.following = json.loads(res.cache.read('%s_at_%s_follows.json' % (self.pump.nickname,
                                                                                  self.pump.server)))
        print '%s is following %s people' % (self.webfinger, len(self.following))


class Client():
    def __init__(self):
        self.client_name = 'pumpmigrate'
        self.account_names = ['old', 'new']
        res.init('kabniel', 'pumpmigrate')
        if res.user.read('config.json'):
            self.cfg = json.loads(res.user.read('config.json'))
        else:
            self.cfg = {}
        self.accounts = {}

        for acct in self.account_names:
            self.accountSetup(acct)

    def accountSetup(self, acct):
        if acct in self.cfg:
            cfg = self.cfg[acct]
            self.accounts[acct] = Account(self.client_name, cfg['webfinger'],cfg['key'], cfg['secret'], cfg['token'], cfg['token_secret'])
            print 'account %s loaded from config[%s]' % (self.cfg[acct]['webfinger'], acct)
        else:
            webfinger = raw_input('Enter your webfinger for your %s account: ' % acct)
            self.accounts[acct] = Account(self.client_name, webfinger)
            key, secret = self.accounts[acct].pump.get_registration()[:2]
            token, token_secret = self.accounts[acct].pump.get_token()
            cfg = {'webfinger':webfinger, 'key':key, 'secret':secret,'token':token,'token_secret':token_secret}
            self.cfg[acct] = cfg
            res.user.write('config.json', json.dumps(self.cfg))

    def getUniqueFollowing(self, account_names):
        for f in self.accounts[account_names[0]].following:
            if f not in self.accounts[account_names[1]].following:
                self.accounts[account_names[0]].uniquefollows.append(f)
        print '%s is not following %s people from %s\'s list' % (self.accounts[account_names[1]].webfinger, len(self.accounts[account_names[0]].uniquefollows), self.accounts[account_names[0]].webfinger)

    def doFollow(self):
        for i in self.accounts['old'].uniquefollows:
            person = self.accounts['new'].pump.Person(i)
            print person.id

    def run(self):
        self.getUniqueFollowing(self.account_names)
        self.getUniqueFollowing(self.account_names[::-1])
        #self.doFollow()

if __name__ == '__main__':
    app = Client()
    app.run()
