#!/usr/bin/env python

import json
import requests
from clint import resources as res
from pypump import PyPump
from requests_oauthlib import OAuth1

class Account():
    def __init__(self, webfinger, key=None, secret=None, token=None, token_secret=None):
        self.webfinger = webfinger
        self.key = key
        self.secret = secret
        self.token = token
        self.token_secret = token_secret
        self.following = None
        self.uniquefollows = []
        self.pump = PyPump(self.webfinger, key=self.key, secret=self.secret, token=self.token, token_secret=self.token_secret, client_name='pumpmigrate')

    def getFollowing(self):
        pass


class Client():
    def __init__(self):
        self.client_name = 'pumpmigrate'
        res.init('kabniel', 'pumpmigrate')
        if res.user.read('config.json'):
            self.cfg = json.loads(res.user.read('config.json'))
        else:
            self.cfg = {}
        self.old = None
        self.new = None

    def accountSetup(self):
        if 'old' in self.cfg:
            cfg = self.cfg['old']
            self.old = Account(cfg['webfinger'],cfg['key'], cfg['secret'], cfg['token'], cfg['token_secret'])
            print 'account %s loaded from config.old' % self.cfg['old']['webfinger']
        else:
            webfinger = raw_input('Enter your webfinger for your old account: ')
            self.old = Account(webfinger)
            key, secret = self.old.pump.get_registration()[:2]
            token, token_secret = self.old.pump.get_token()
            cfg = {'webfinger':webfinger, 'key':key, 'secret':secret,'token':token,'token_secret':token_secret}
            self.cfg['old'] = cfg
            res.user.write('config.json', json.dumps(self.cfg))

        if 'new' in self.cfg:
            cfg = self.cfg['new']
            self.new = Account(cfg['webfinger'],cfg['key'], cfg['secret'], cfg['token'], cfg['token_secret'])
            print 'account %s loaded from config.new' % self.cfg['new']['webfinger']
        else:
            webfinger = raw_input('Enter your webfinger for your new account: ')
            self.new = Account(webfinger)
            key, secret = self.new.pump.get_registration()[:2]
            token, token_secret = self.new.pump.get_token()
            cfg = {'webfinger':webfinger, 'key':key, 'secret':secret,'token':token,'token_secret':token_secret}
            self.cfg['new'] = cfg
            res.user.write('config.json', json.dumps(self.cfg))

    def getFollowing(self):
        # Grab contacts followed from old account
        if not res.cache.read('oldfollows.json'):
            url = 'https://%s/api/user/%s/following?count=200' % (self.old.pump.server, self.old.pump.nickname)
            auth = OAuth1(self.cfg['old']['key'],
                          self.cfg['old']['secret'],
                          self.cfg['old']['token'],
                          self.cfg['old']['token_secret'])
            self.old.following = json.loads(requests.get(url, auth=auth).content)
            oldfollows = []
            for i in self.old.following['items']:
                oldfollows.append(i['id'].split(':')[1])
            self.old.following = oldfollows
            res.cache.write('oldfollows.json', json.dumps(oldfollows))
        else:
            self.old.following = json.loads(res.cache.read('oldfollows.json'))
        print '%s is following %s people' % (self.cfg['old']['webfinger'], len(self.old.following))

        if not res.cache.read('newfollows.json'):
            url = 'https://%s/api/user/%s/following?count=200' % (self.new.pump.server, self.new.pump.nickname)
            auth = OAuth1(self.cfg['new']['key'],
                          self.cfg['new']['secret'],
                          self.cfg['new']['token'],
                          self.cfg['new']['token_secret'])
            self.new.following = json.loads(requests.get(url, auth=auth).content)
            newfollows = []
            for i in self.new.following['items']:
                newfollows.append(i['id'].split(':')[1])
            self.new.following = newfollows
            res.cache.write('newfollows.json', json.dumps(newfollows))
        else:
            self.new.following = json.loads(res.cache.read('newfollows.json'))
        print '%s is following %s people' % (self.cfg['new']['webfinger'], len(self.new.following))

        for f in self.old.following:
            if f not in self.new.following:
                self.old.uniquefollows.append(f)
        print '%s is not following %s people from %s\'s list' % (self.cfg['new']['webfinger'], len(self.old.uniquefollows), self.cfg['old']['webfinger'])

    def doFollow(self):
        for i in self.old.uniquefollows:
            person = self.new.pump.Person(i)
            print person.id



    def run(self):
        self.accountSetup()
        self.getFollowing()
        self.doFollow()

if __name__ == '__main__':
    app = Client()
    app.run()
