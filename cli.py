#!/usr/bin/env python

# Requires: lxml

import cmd, getpass, json, sys, requests
# from leetcode import *
from lxml import html

def args( arg ):
    return arg.split()

class Problem( object ):
    def __init__( self, pid, slug, level ):
        self.pid = pid
        self.slug = slug
        self.level = level

    def __str__( self ):
        return '%3d %s' % ( self.pid, self.slug)

class OJMixin( object ):
    url = 'https://leetcode.com'
    session = requests.session()
    loggedIn = False

    def login( self ):
        url = self.url + '/accounts/login/'
        xpath = "/html/body/div[1]/div[2]/form/input[@name='csrfmiddlewaretoken']/@value"
        username = raw_input( 'Username: ' )
        password = getpass.getpass()

        self.session.cookies.clear()
        self.loggedIn = False

        resp = self.session.get( url )
        csrf = list( set( html.fromstring( resp.text ).xpath( xpath ) ) )[ 0 ]

        headers = { 'referer' : url }
        data = {
            'login': username,
            'password': password,
            'remember': True,
            'csrfmiddlewaretoken': csrf
        }

        r = self.session.post( url, data, headers=headers )
        if r.status_code == requests.codes.ok:
            print 'Welcome!'
            self.loggedIn = True

    def get_tags( self ):
        url = self.url + '/problems/api/tags/'

        resp = self.session.get( url )

        tags = {}
        for e in json.loads( resp.text ).get( 'topics' ):
            t = e.get( 'slug' )
            ql = e.get( 'questions' )
            tags[ t ] = ql

        return tags

    def get_problems( self ):
        url = self.url + '/api/problems/all/'

        resp = self.session.get( url )

        problems = {}
        for e in json.loads( resp.text ).get( 'stat_status_pairs' ):
            i = e.get( 'stat' ).get( 'question_id' )
            s = e.get( 'stat' ).get( 'question__title_slug' )
            l = e.get( 'difficulty' ).get( 'level' )
            problems[ i ] = Problem( pid=i, slug=s, level=l )

        return problems

class CodeShell( cmd.Cmd, OJMixin ):
    prompt = '> '
    tags, tag, problems = {}, None, {}

    def precmd( self, line ):
        return line.lower()

    def do_login( self, unused ):
        self.login()
        self.tags = self.tag = None

    def do_ls( self, _filter ):
        if not self.tags:
            self.tags = self.get_tags()

        if not self.problems:
            self.problems = self.get_problems()

        if not self.tag:
            for t in sorted( self.tags.keys() ):
                print '\t', '%3d' % len( self.tags[ t ] ), t
        else:
            ql = self.tags.get( self.tag )
            for i in sorted( ql ):
                print '\t', self.problems[ i ]

    def complete_cd( self, text, line, start, end ):
        suffixes = []
        for t in sorted( self.tags.keys () ):
            if t.startswith( text ):
                i = len( text )
                suffixes.append( t[ i: ] )

        if len( suffixes ) == 1:
            s = suffixes[ 0 ]
            return [ text + s ]
        elif len( suffixes ) > 1:
            # XXX: binary-*-*
            print ''
            for s in suffixes:
                print '\t', text + s
            sys.stdout.write( self.prompt + line )
        return [ text ]

    def do_cd( self, tag ):
        if tag in self.tags.keys():
            self.tag = tag

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

if __name__ == '__main__':
    shell = CodeShell()
#   shell.login()

    shell.cmdloop()
