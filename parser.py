#!/usr/bin/env python
import sys, argparse

class Parser():
    def __init__(self, obj):
        self.parser = argparse.ArgumentParser()
        subparsers = self.parser.add_subparsers(dest='subcommand', title='Actions',
                                                description="(if none is specified, 'move' will be run in interactive mode)")
        migrate = subparsers.add_parser('move', help='Move contacts between accounts.')
        migrate.add_argument('-a', '--accounts', nargs=2, metavar='webfinger',
                             dest='webfingers', help='The accounts to move contacts between.')
        #migrate.add_argument('-q', '--quiet', action='store_true', dest='quiet', help='NOT IMPLEMENTED')
        migrate.add_argument('-u', '--no-unfollow', action='store_true',
                             dest='nounfollow', help='Do not unfollow any contacts.')
        #migrate.add_argument('-p', '--no-prompt', action='store_true', dest='noprompt', help='NOT IMPLEMENTED')
        migrate.add_argument('--dry-run', action='store_true',
                                 dest='dryrun', help='Do not actually follow/unfollow anything')
        migrate.set_defaults(func=obj.migrate)

        sync = subparsers.add_parser('sync', help='Sync contacts between accounts.')
        sync.add_argument('-a', '--accounts', nargs=2, metavar='webfinger',
                          dest='webfingers', help='The accounts to sync contacts between.')
        #sync.add_argument('--silent', action='store_true', help='NOT IMPLEMENTED')
        #sync.add_argument('--noprompt', action='store_true', help='NOT IMPLEMENTED')
        sync.add_argument('--dry-run', action='store_true',
                                 dest='dryrun', help='Do not actually follow/unfollow anything')
        sync.set_defaults(func=obj.sync)

        if len(sys.argv) < 2:
            # run migrate in interactive mode if no args
            self.args = self.parser.parse_args(['move'], namespace=obj)
        else:
            self.args = self.parser.parse_args(namespace=obj)
        self.args.func(self.args)
