#!/usr/bin/env python

import cmd, sys
# from leetcode import *

def args( arg ):
    return arg.split()

class OJMixin( object ):
    pass

class CodeShell( cmd.Cmd, OJMixin ):
    prompt = '> '

    def do_login( self, username ):
        todo = """login < username >
        ask for password
        token = post to login URL

        tag = <root>"""

        print todo

    def do_list( self, _filter ):
        todo = """list < filter >
        if tag == <root>:
            if not taglist:
                taglist = get taglist URL
            print taglist
        else:
            problems = tagMap.get( tag )
            if not problems:
                problems = get tag URL
                tagMap[ tag ] = problems
            print problems"""

        print todo

    def do_goto( self, tag ):
        todo = """goto < tag >

        if tag in taglist:
            tag = tag"""

        print todo

    def do_solve( self, newPid ):
        todo = """solve <pid>
        if pid:
            confirm if to solve another problem
            if no:
                return
            else:
                pid = newPid

        ( desc, boilerplate ) = get problem <pid> URL

        pad = '/tmp/%d.py' % pid
        with open( pad ) as f:
            f.write( boilerplate )
        pads[ pid ] = pad

        print desc
        print pad"""

        print todo

    def do_check( self, unused ):
        todo = """check
        if pid:
            error = post pads[ pid ] to check URL
            if error:
                print error"""

        print todo

    def do_submit( self, unused ):
        todo = """submit
        if pid:
            error = post pads[ pid ] to submit URL
            if error:
                print test case
                print error"""

        print todo

    def do_cheat( self, unused ):
        todo = """cheat
        if pid:
            sl = cheatsheet.get( pid )
            if not sl:
                sl = get cheatsheet <pid> URL
                cheatsheet[ pid ] = sl
            print the best solutions in sl"""

        print todo

    def do_hint( self, unused ):
        todo = """hint
        if pid:
            # we can also save desc and load locally
            desc = get problem URL
            print desc"""

        print todo

    def do_eof( self, arg ):
        return True

    def precmd( self, line ):
        return line.lower()

if __name__ == '__main__':
    CodeShell().cmdloop()
