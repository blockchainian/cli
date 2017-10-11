#!/usr/bin/env python

# Requires: lxml, bs4

import cmd, getpass, json, re, sys, requests
from lxml import html
from bs4 import BeautifulSoup

def args( arg ):
    return arg.split()

class Problem( object ):
    def __init__( self, pid, slug, level, desc=None ):
        self.pid = pid
        self.slug = slug
        self.level = level
        self.desc = desc

    def __str__( self ):
        return '%3d %s' % ( self.pid, self.slug )

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

    def get_description( self, slug ):
        url = self.url + '/problems/%s/description/' % slug
        cls = { 'class' : 'question-description' }

        resp = self.session.get( url )
        soup = BeautifulSoup( resp.text, 'lxml' )
        for e in soup.find_all( 'div', attrs=cls ):
            return e.text

        return None

class CodeShell( cmd.Cmd, OJMixin ):
    tags, tag, problems, pid = {}, None, {}, None

    @property
    def prompt( self ):
        return self.cwd() + '> '

    def cwd( self ):
        wd = '/'
        if self.tag:
            wd += self.tag
            if self.pid:
                wd += '/%s-%d' % ( self.problems[ self.pid ].slug, self.pid )
        return wd

    def precmd( self, line ):
        return line.lower()

    def do_login( self, unused ):
        self.login()
        self.tags = self.tag = None

    def do_clear( self, unused ):
        print "\033c"

    def do_ls( self, _filter ):
        if not self.tags:
            self.tags = self.get_tags()

        if not self.problems:
            self.problems = self.get_problems()

        if not self.tag:
            for t in sorted( self.tags.keys() ):
                print '\t', '%3d' % len( self.tags[ t ] ), t
        elif not self.pid:
            ql = self.tags.get( self.tag )
            for i in sorted( ql ):
                print '\t', self.problems[ i ]
        else:
            p = self.problems[ self.pid ]
            if not p.desc:
                p.desc = self.get_description( p.slug )
            print p.desc

    def complete_cd( self, text, line, start, end ):
        if self.tag:
            keys = [ str( i ) for i in self.tags[ self.tag ] ]
        else:
            keys = self.tags.keys()

        prefix, suffixes = line.split()[ -1 ], []

        for t in sorted( keys ):
            if t.startswith( prefix ):
                i = len( prefix )
                suffixes.append( t[ i: ] )

        return [ text + s for s in suffixes ]

    def do_cd( self, tag ):
        if tag == '..':
            if self.pid:
                self.pid = None
            elif self.tag:
                self.tag = None
        elif tag in self.tags:
            self.tag = tag
        elif tag.isdigit():
            pid = int( tag )
            if pid in self.problems:
                self.pid = pid

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
    shell.login()
    shell.cmdloop()
