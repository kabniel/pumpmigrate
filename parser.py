#!/usr/bin/env python
import sys, argparse

class Parser():
    def __init__(self, obj):
        self.parser = argparse.ArgumentParser()
        subparsers = self.parser.add_subparsers(dest='subcommand', title='Actions',
                                                description="(if none is specified, 'move' will be run in interactive mode)")

        move = subparsers.add_parser('move', help='Move contacts between accounts.')
        move.add_argument('-a', '--accounts', nargs=2, metavar='webfinger', dest='webfingers',
                          help='The accounts to move contacts between.')
        move.add_argument('-q', '--quiet', action='store_true', dest='quiet',
                          help='Do not print any output.')
        move.add_argument('--no-follow', action='store_true', dest='nofollow',
                          help='Do not follow any contacts.')
        move.add_argument('--no-unfollow', action='store_true', dest='nounfollow',
                          help='Do not unfollow any contacts.')
        move.add_argument('--continue', action='store_true', dest='noprompt',
                          help='Do not prompt before actions, just continue')
        move.add_argument('--dry-run', action='store_true', dest='dryrun',
                          help='Do not actually follow/unfollow any contacts')
        move.set_defaults(func=obj.move)

        sync = subparsers.add_parser('sync', help='Sync contacts between accounts.')
        sync.add_argument('-a', '--accounts', nargs=2, metavar='webfinger', dest='webfingers',
                          help='The accounts to sync contacts between.')
        sync.add_argument('-q', '--quiet', action='store_true', dest='quiet',
                          help='Do not print any output.')
        sync.add_argument('--continue', action='store_true', dest='noprompt',
                          help='Do not prompt before actions, just continue')
        sync.add_argument('--dry-run', action='store_true',
                                 dest='dryrun', help='Do not actually follow/unfollow any contacts')
        sync.set_defaults(func=obj.sync)

        if len(sys.argv) < 2:
            # run move in interactive mode if no args
            self.args = self.parser.parse_args(['move'])
        else:
            self.args = self.parser.parse_args()
