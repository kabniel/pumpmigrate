#!/usr/bin/env python
import sys, argparse
from textwrap import dedent

class Parser():
    def __init__(self, obj):
        mainDesc = dedent('''\
                          Transfer contacts between your pump.io accounts

                           For more help run pumpmigrate.py {move,sync} -h
                          ''')
        self.parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                             description=mainDesc)
        self.parser.add_argument('-v', '--version', action='version', version='%s %s' % (obj.name, obj.version))
        subparsers = self.parser.add_subparsers(dest='subcommand', title='subcommands')

        moveDesc = dedent('''\
                          Move contacts between accounts.

                          Example 1:
                            user@pump1 is following foo and user@pump2 is following bar.
                              pumpmigrate.py move -a user@pump1 user@pump2
                            user@pump1 is not following anyone, and user@pump2 is following foo and bar.

                          Example 2:
                            user@pump1 is following foo and user@pump2 is following bar.
                              pumpmigrate.py move -a user@pump1 user@pump2 --no-unfollow
                            user@pump1 is still following foo, and user@pump2 is following foo and bar.
                          ''')

        move = subparsers.add_parser('move', help='Move contacts between accounts.',
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=moveDesc)
        move.add_argument('-a', '--accounts', nargs=2, metavar='webfinger', dest='webfingers',
                          help='The accounts to move contacts between.')
        move.add_argument('--quiet', action='store_true', dest='quiet',
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
        
        syncDesc = dedent('''\
                          Sync contacts between accounts.

                          Example usage:
                            user@pump1 is following foo and user@pump2 is following bar.
                              pumpmigrate.py sync -a user@pump1 user@pump2
                            user@pump1 and user@pump2 are now both following foo and bar.''')
        sync = subparsers.add_parser('sync', help='Sync contacts between accounts.',
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=syncDesc)
        sync.add_argument('-a', '--accounts', nargs=2, metavar='webfinger', dest='webfingers',
                          help='The accounts to sync contacts between.')
        sync.add_argument('--quiet', action='store_true', dest='quiet',
                          help='Do not print any output.')
        sync.add_argument('--continue', action='store_true', dest='noprompt',
                          help='Do not prompt before actions, just continue')
        sync.add_argument('--dry-run', action='store_true',
                                 dest='dryrun', help='Do not actually follow/unfollow any contacts')
        sync.set_defaults(func=obj.sync)

        if len(sys.argv) < 2:
            # show help if no args
            self.args = self.parser.parse_args(['--help'])
        else:
            self.args = self.parser.parse_args()
