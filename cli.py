#!/usr/bin/env python

# Requires: lxml, bs4, PyExecJS

import cmd, getpass, json, os, re, requests, sys, time
from lxml import html
from bs4 import BeautifulSoup
import execjs

def args( arg ):
    return arg.split()

class Problem( object ):
    def __init__( self, pid, slug, level, desc='', code='', test='' ):
        self.pid = pid
        self.slug = slug
        self.level = level
        self.desc = desc
        self.code = code
        self.test = test

    def __str__( self ):
        return '%3d %s' % ( self.pid, self.slug )

class Solution( object ):
    def __init__( self, pid, sid, code ):
        self.pid = pid
        self.sid = sid
        self.code = code

    def __str__( self ):
        s = '%d-%d:\n' % ( self.pid, self.sid )
        s += self.code
        return s

class Result( object ):
    def __init__( self, sid, result ):
        self.sid = sid
        self.success = result.get( 'run_success' )
        self.output = result.get( 'code_output', '' )
        self.runtime = result.get( 'status_runtime' )

        self.result = result.get( 'code_answer', [] )
        if not self.result:
            total = result.get( 'total_testcases' )
            passed = result.get( 'compare_result', '' ).count( '1' )
            self.result = [ "%d/%d tests passed" % ( passed, total ) ]

        self.errors = {}
        for e in [ 'runtime_error' ]:
            m = result.get( e )
            if m:
                self.errors[ e ] = m
        if result.get( 'status_code' ) == 14:
            self.errors[ 'time_limit_exceeded' ] = ''

    def __str__( self ):
        s = ''
        for e, m in self.errors.iteritems():
            s += e.replace( '_', ' ' ).title() + ':' + m
        else:
            if s:
                s += '\n'

        if self.result:
            s += 'Result: ' + ' '.join( self.result ) + '\n'

        s += 'Output: '
        if type( self.output ) == list:
            s += '\n'.join( self.output ) + '\n'
        else:
            s += self.output + '\n'

        s += 'Time: ' + self.runtime
        return s

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

        resp = self.session.post( url, data, headers=headers )
        if self.session.cookies.get( 'LEETCODE_SESSION' ):
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

    def get_problem( self, slug ):
        url = self.url + '/problems/%s/description/' % slug
        cls = { 'class' : 'question-description' }
        js = r'var pageData =\s*(.*?);'

        resp = self.session.get( url )
        desc = code = test = ''

        soup = BeautifulSoup( resp.text, 'lxml' )
        for e in soup.find_all( 'div', attrs=cls ):
            desc = e.text
            break

        for s in re.findall( js, resp.text, re.DOTALL ):
            v = execjs.eval( s )
            for cs in v.get( 'codeDefinition' ):
                if cs.get( 'text' ) == 'Python':
                    code = cs.get( 'defaultCode' )
            test = v.get( 'sampleTestCase' )
            break

        return ( desc, code, test )

    # @login_required
    def get_latest_solution( self, p ):
        url = self.url + '/submissions/latest/'
        referer = self.url + '/problems/%s/description/' % p.slug

        headers = {
                'referer' : referer,
                'content-type' : 'application/json',
                'x-csrftoken' : self.session.cookies[ 'csrftoken' ],
                'x-requested-with' : 'XMLHttpRequest',
        }
        data = {
            'qid': p.pid,
            'lang': 'python',
        }

        resp = self.session.post( url, json=data, headers=headers )
        code = json.loads( resp.text ).get( 'code' )
        return code

    # @login_required
    def get_solution( self, pid, token ):
        url = self.url + '/submissions/api/detail/%d/python/%d/' % ( pid, token )

        resp = self.session.get( url )
        data = json.loads( resp.text )
        code = data.get( 'code' )

        return Solution( pid, token, code )

    # @login_required
    def get_solutions( self, pid, sid, limit=5 ):
        url = self.url + '/submissions/detail/%s/' % sid
        js = r'var pageData =\s*(.*?);'

        resp = self.session.get( url )
        solutions = []

        for s in re.findall( js, resp.text, re.DOTALL ):
            v = execjs.eval( s )
            df = json.loads( v.get( 'distribution_formatted' ) )
            if df.get( 'lang' ) == 'python':
                for e in df.get( 'distribution' )[ : limit ]:
                    token = int( e[ 0 ] )
                    solutions.append( self.get_solution( pid, token ) )
                break

        return solutions

    # @login_required
    def get_result( self, sid ):
        url = self.url + '/submissions/detail/%s/check/' % sid

        while True:
            time.sleep( 1 )
            resp = self.session.get( url )
            data = json.loads( resp.text )
            if data.get( 'state' ) == 'SUCCESS':
                break

        return Result( sid, data )

    # @login_required
    def test_solution( self, p, code, full=False ):
        if full:
            epUrl, sidKey = 'submit/', 'submission_id'
        else:
            epUrl, sidKey = 'interpret_solution/', 'interpret_id'

        url = self.url + '/problems/%s/%s/' % ( p.slug, epUrl )
        referer = self.url + '/problems/%s/description/' % p.slug
        headers = {
                'referer' : referer,
                'content-type' : 'application/json',
                'x-csrftoken' : self.session.cookies[ 'csrftoken' ],
                'x-requested-with' : 'XMLHttpRequest',
        }
        data = {
            'judge_type': 'large',
            'lang' : 'python',
            'test_mode' : False,
            'question_id' : str( p.pid ),
            'typed_code' : code,
            'data_input': p.test,
        }

        resp = self.session.post( url, json=data, headers=headers )
        sid = json.loads( resp.text ).get( sidKey )
        result = self.get_result( sid )

        return result

class CodeShell( cmd.Cmd, OJMixin ):
    tags, problems, cheatsheet = {}, {}, {}
    tag = pid = sid = None

    @property
    def prompt( self ):
        return self.cwd() + '> '

    def precmd( self, line ):
        return line.lower()

    def cwd( self ):
        wd = '/'
        if self.tag:
            wd += self.tag
            if self.pid:
                wd += '/%d-%s' % ( self.pid, self.problems[ self.pid ].slug )
        return wd

    @property
    def pad( self ):
        return '/tmp/%d.py' % self.pid if self.pid else None

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
        elif not self.pid:
            ql = self.tags.get( self.tag )
            for i in sorted( ql ):
                print '\t', self.problems[ i ]
        else:
            p = self.problems[ self.pid ]
            if not p.desc:
                p.desc, p.code, p.test = self.get_problem( p.slug )
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

    def do_cat( self, unused ):
        test = '/tmp/test.dat'

        p = self.problems[ self.pid ]

        if not os.path.isfile( self.pad ):
            with open( self.pad, 'w' ) as f:
                f.write( p.code )

        with open( test, 'w' ) as f:
            f.write( p.test )

        print self.pad

    def do_check( self, unused ):
        p = self.problems.get( self.pid )
        if p:
            with open( self.pad, 'r' ) as f:
                code = f.read()
                result = self.test_solution( p, code )
                print result

    def do_pull( self, unused ):
        p = self.problems.get( self.pid )
        if p:
            code = self.get_latest_solution( p )
            with open( self.pad, 'w' ) as f:
                f.write( code )

    def do_push( self, unused ):
        p = self.problems.get( self.pid )
        if p:
            with open( self.pad, 'r' ) as f:
                code = f.read()
                result = self.test_solution( p, code, full=True )
                self.sid = result.sid
                print result

    def do_cheat( self, limit ):
        if self.pid and self.sid:
            cs = self.cheatsheet.get( self.pid )
            if not cs:
                cs = self.get_solutions( self.pid, self.sid )
                self.cheatsheet[ self.pid ] = cs

            limit = min( len( cs ), max( int( limit ), 1 ) if limit else 1 )
            for i in xrange( limit ):
                print cs[ i ]

    def do_clear( self, unused ):
        print "\033c"

    def do_eof( self, arg ):
        return True

if __name__ == '__main__':
    shell = CodeShell()
    shell.login()
    shell.cmdloop()
