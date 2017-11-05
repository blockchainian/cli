#!/usr/bin/env python

import cmd, contextlib, functools, getpass, os, pprint, random, re, sys, time
import bs4, execjs, json, requests
from datetime import datetime
from lxml import html

class Magic( object ):
    bunnies = [
"""
  (\(\\
 (='.')
o(__")")""",

"""
(\__/)
(='.'=)
(")_(")""",

"""
 (\_/)
=(^.^)=
(")_(")""",

"""
(\ /)
( . .)
c(")(")""",

"""
(\__/)
(>'.'<)
(")_(")""",

"""
++++++++++++
|  LITTLE  |
|  BUNNY   |
|  LOVES   |
|   YOU    |
|    -xt2  |
++++++++++++
(\__/)  ||
(>'.'<) ||
(")_(") //""",

"""
   __//
  /.__.\  oops
  \ \/ /
__/    \\
\-      )
 \_____/
___|_|____
   " " """,
    ]
    def __init__( self ):
        self.motd = random.choice( self.bunnies )[ 1: ]

    def magic( self, msg ):
        return self.__owl( msg )

    def __owl( self, msg ):
        return """,___,\n[O.o]  %s\n/)__)\n-"--"-""" % msg

class Problem( object ):
    def __init__( self, pid, slug, level, topics=[], status=None ):
        self.loaded = False
        self.pid = pid
        self.slug = slug
        self.level = level
        self.topics = topics[ : ]
        self.status = status
        self.desc = self.code = self.test = self.html = ''

    def __str__( self ):
        if self.solved:
            s = ' '
        elif self.failed:
            s = 'x'
        else:
            s = '*'
        s += '%3d %s' % ( self.pid, self.slug )
        return s

    @property
    def solved( self ):
        return self.status == 'ac'

    @solved.setter
    def solved( self, x ):
        self.status = 'ac' if x else 'notac'

    @property
    def failed( self ):
        return self.status == 'notac'

    @property
    def todo( self ):
        return not self.status

class Solution( object ):
    def __init__( self, pid, sid, code ):
        self.pid = pid
        self.sid = sid
        self.code = code

    def __str__( self ):
        s = '[%d ms]\n' % self.sid
        for i, l in enumerate( self.code.splitlines() ):
            s += '%3d %s\n' % ( i, l )
        return s

class Result( object ):
    def __init__( self, sid, result ):
#       pprint.pprint( result )
        self.sid = sid
        self.success = False
        self.fintime = None

        def split( s ):
            return s.splitlines() if type( s ) in [ str, unicode ] else s

        self.input = result.get( 'last_testcase', result.get( 'input', '' ) )
        self.output = split( result.get( 'code_output', '' ) )
        self.expected = split( result.get( 'expected_output', '' ) )
        self.debug = split( result.get( 'std_output' ) )

        self.result = result.get( 'code_answer', [] )
        if not self.result:
            total = result.get( 'total_testcases' )
            passed = result.get( 'total_correct' )
            if total:
                self.result.append( "%d/%d tests passed" % ( passed, total ) )

        self.errors = []
        for e in [ 'compile_error', 'runtime_error', 'error' ]:
            m = result.get( e )
            if m:
                self.errors.append( m )

        status = result.get( 'status_code' )
        if status == 10:
            self.success = True
        elif status == 12:
            self.errors.append( 'Memory Limit Exceeded' )
        elif status == 13:
            self.errors.append( 'Output Limit Exceeded' )
        elif status == 14:
            self.errors.append( 'Time limit Exceeded' )

        ts = result.get( 'status_runtime', '' ).replace( 'ms', '' ).strip()
        self.runtime = int( ts ) if ts.isdigit() else 0

    def __str__( self ):
        limit = 25
        s = '\n'.join( self.errors )
        if s:
            s += '\n'

        if self.result:
            s += 'Result: '
            s += ', '.join( self.result ) + '\n'

        if self.input:
            s += 'Input: ' + ','.join( self.input.splitlines() ) + '\n'

        if self.output:
            s += 'Output:'
            s += '\n' if len( self.output ) > 1 else ' '
            s += '\n'.join( self.output[ : limit ] ) + '\n'

        if self.expected:
            s += 'Expected:'
            s += '\n' if len( self.expected ) > 1 else ' '
            s += '\n'.join( self.expected[ : limit ] ) + '\n'

        if self.debug:
            s += 'Debug:'
            s += '\n' if len( self.debug ) > 1 else ' '
            s += '\n'.join( self.debug[ : limit ] ) + '\n'

        if self.runtime:
            s += 'Runtime: %d ms' % self.runtime + '\n'

        if self.fintime:
            m, sec = self.fintime / 60, self.fintime % 60
            s += 'Finish Time: %d min %d sec' % ( m, sec ) + '\n'

        return s.strip( '\n' )

class Session( object ):
    def __init__( self, sid, name, active ):
        self.sid = sid
        self.name = name if name else '#'
        self.active = active

    def __str__( self ):
        return '*' if self.active else '' + self.name

class OJMixin( object ):
    url = 'https://leetcode.com'
    langs = [ 'c', 'cpp', 'golang', 'java', 'javascript', 'python', 'scala' ]
    lang = 'python'

    @property
    def suffix( self ):
        suffixes = { 'golang': 'go', 'javascript': 'js', 'python': 'py' }
        return suffixes.get( self.lang, self.lang )

    @property
    def language( self ):
        languages = {
            'cpp': 'C++',
            'csharp' : 'C#',
            'golang' : 'Go',
            'javascript' : 'JavaScript'
        }
        return languages.get( self.lang, self.lang.title() )

    session, loggedIn = requests.session(), False

    def login( self ):
        url = self.url + '/accounts/login/'
        xpath = "/html/body/div[1]/div[2]/form/input[@name='csrfmiddlewaretoken']/@value"
        username = raw_input( 'Username: ' )
        password = getpass.getpass()

        self.session.cookies.clear()
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
            self.loggedIn = True
            print 'Welcome %s!' % username
        else:
            self.loggedIn = False

    def parse_sessions( self, resp ):
        sd = {}
        for s in json.loads( resp.text ).get( 'sessions', [] ):
            sid, name, active = s[ 'id' ], s[ 'name' ] or '#', s[ 'is_active' ]
            sd[ name ] = Session( sid, name, active )
        return sd

    def get_sessions( self ):
        url = self.url + '/session/'
        headers = {
                'referer' : url,
                'content-type' : 'application/json',
                'x-csrftoken' : self.session.cookies[ 'csrftoken' ],
                'x-requested-with' : 'XMLHttpRequest',
        }
        resp = self.session.post( url, json={}, headers=headers )
        return self.parse_sessions( resp )

    def create_session( self, name ):
        url = self.url + '/session/'
        headers = {
                'referer' : url,
                'content-type' : 'application/json',
                'x-csrftoken' : self.session.cookies[ 'csrftoken' ],
                'x-requested-with' : 'XMLHttpRequest',
        }
        data = { 'func': 'create', 'name': name, }
        resp = self.session.put( url, json=data, headers=headers )
        return self.parse_sessions( resp )

    def activate_session( self, sid ):
        url = self.url + '/session/'
        headers = {
                'referer' : url,
                'content-type' : 'application/json',
                'x-csrftoken' : self.session.cookies[ 'csrftoken' ],
                'x-requested-with' : 'XMLHttpRequest',
        }
        data = { 'func': 'activate', 'target': sid, }
        resp = self.session.put( url, json=data, headers=headers )
        return self.parse_sessions( resp )

    def get_tags( self ):
        url = self.url + '/problems/api/tags/'

        resp = self.session.get( url )
        data = json.loads( resp.text )

        topics = {}
        for e in data.get( 'topics' ):
            t = e.get( 'slug' )
            ql = e.get( 'questions' )
            topics[ t ] = ql

        companies = {}
        for e in data.get( 'companies' ):
            c = e.get( 'slug' )
            ql = e.get( 'questions' )
            companies[ c ] = set( ql )

        return ( topics, companies )

    def get_problems( self ):
        url = self.url + '/api/problems/all/'

        resp = self.session.get( url )

        problems = {}
        for e in json.loads( resp.text ).get( 'stat_status_pairs' ):
            i = e.get( 'stat' ).get( 'question_id' )
            s = e.get( 'stat' ).get( 'question__title_slug' )
            l = e.get( 'difficulty' ).get( 'level' )
            t = e.get( 'status' )
            problems[ i ] = Problem( pid=i, slug=s, level=l, status=t )

        return problems

    def strip( self, s ):
        return s.replace( '\r', '' )

    def get_problem( self, p ):
        url = self.url + '/problems/%s/description/' % p.slug
        cls = { 'class' : 'question-description' }
        js = r'var pageData =\s*(.*?);'

        resp = self.session.get( url )

        soup = bs4.BeautifulSoup( resp.text, 'lxml' )
        for e in soup.find_all( 'div', attrs=cls ):
            p.desc = self.strip( e.text )
            p.html = e.prettify()
            break

        if p.todo:
            for s in re.findall( js, resp.text, re.DOTALL ):
                v = execjs.eval( s )
                for cs in v.get( 'codeDefinition' ):
                    if cs.get( 'text' ) == self.language:
                        p.code = self.strip( cs.get( 'defaultCode', '' ) )
                p.test = v.get( 'sampleTestCase' )
                break
        else:
            p.code = self.get_latest_solution( p )

        p.loaded = bool( p.desc and p.test and p.code )

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
            'lang': self.lang,
        }

        resp = self.session.post( url, json=data, headers=headers )

        try:
            code = self.strip( json.loads( resp.text ).get( 'code' ) )
        except ValueError:
            code = ''
        return code

    def get_solution( self, pid, token ):
        url = self.url + '/submissions/api/detail/%d/%s/%d/' % \
                ( pid, self.lang, token )

        resp = self.session.get( url )
        data = json.loads( resp.text )
        code = data.get( 'code' )

        return Solution( pid, token, code )

    def get_solutions( self, pid, sid, limit=5 ):
        url = self.url + '/submissions/detail/%s/' % sid
        js = r'var pageData =\s*(.*?);'

        resp = self.session.get( url )
        solutions = []

        for s in re.findall( js, resp.text, re.DOTALL ):
            v = execjs.eval( s )
            try:
                df = json.loads( v.get( 'distribution_formatted' ) )
                if df.get( 'lang' ) == self.lang:
                    for e in df.get( 'distribution' )[ : limit ]:
                        token = int( e[ 0 ] )
                        solutions.append( self.get_solution( pid, token ) )
                    break
            except ValueError:
                pass

        return solutions

    def get_solution_runtimes( self, sid ):
        url = self.url + '/submissions/detail/%s/' % sid
        js = r'var pageData =\s*(.*?);'

        resp = self.session.get( url )
        runtimes = []

        for s in re.findall( js, resp.text, re.DOTALL ):
            v = execjs.eval( s )
            try:
                df = json.loads( v.get( 'distribution_formatted' ) )
                if df.get( 'lang' ) == self.lang:
                    for t, n in df.get( 'distribution' ):
                        runtimes.append( ( int( t ), float( n ) ) )
            except ValueError:
                pass

        return runtimes

    def get_result( self, sid, timeout=30 ):
        url = self.url + '/submissions/detail/%s/check/' % sid

        for i in xrange( timeout ):
            time.sleep( 1 )
            resp = self.session.get( url )
            data = json.loads( resp.text )
            if data.get( 'state' ) == 'SUCCESS':
                break
        else:
            data = { 'error': '< network timeout >' }

        return Result( sid, data )

    def test_solution( self, p, code, tests='', full=False ):
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
            'lang' : self.lang,
            'test_mode' : False,
            'question_id' : str( p.pid ),
            'typed_code' : code,
            'data_input': tests,
        }

        resp = self.session.post( url, json=data, headers=headers )
        try:
            sid = json.loads( resp.text ).get( sidKey )
            result = self.get_result( sid )
        except ValueError:
            result = None

        return result

def login_required( f ):
    @functools.wraps( f )
    def wrapper( *args, **kwargs ):
        cs = args[ 0 ]
        if cs.loggedIn:
            return f( *args, **kwargs )
    return wrapper

class CodeShell( cmd.Cmd, OJMixin, Magic ):
    sessions, ws = {}, 'ws'
    topics, companies, problems, cheatsheet = {}, {}, {}, {}
    topic = pid = sid = None
    xlimit = 0

    def __init__( self ):
        cmd.Cmd.__init__( self )
        Magic.__init__( self )
        if not os.path.exists( self.ws ):
            os.makedirs( self.ws )

    def precmd( self, line ):
        line = line.lower()
        if line.startswith( '/' ):
            line = 'find ' + ' '.join( line.split( '/' ) )
        self.xpid = self.pid
        return line

    def postcmd( self, stop, line ):
        if self.pid != self.xpid:
            self.ts = datetime.now()
        return stop

    def emptyline( self ):
        pass

    @property
    def prompt( self ):
        return self.sname + ':' + self.cwd + '> '

    def complete_all( self, keys, text, line, start, end ):
        prefix, suffixes = ' '.join( line.split()[ 1: ] ), []

        for t in sorted( keys ):
            if t.startswith( prefix ):
                i = len( prefix )
                suffixes.append( t[ i: ] )

        return [ text + s for s in suffixes ]

    @property
    def sname( self ):
        for s in self.sessions.itervalues():
            if s.active:
                return s.name
        return '~'

    @property
    def cwd( self ):
        wd = '/'
        if self.topic:
            wd += self.topic
            if self.pid:
                wd += '/%d-%s' % ( self.pid, self.problems[ self.pid ].slug )
        return wd

    @property
    def pad( self ):
        if self.pid:
            return '%s/%d.%s' % ( self.ws, self.pid, self.suffix )
        else:
            return None

    @property
    def tests( self ):
        return '%s/tests.dat' % self.ws

    def load( self, force=False ):
        if not self.topics or force:
            self.topics, self.companies = self.get_tags()
        if not self.problems or force:
            self.problems = self.get_problems()
            pl = set( self.problems.iterkeys() )
            for t in sorted( self.topics.iterkeys() ):
                for pid in self.topics[ t ]:
                    p = self.problems.get( pid )
                    if p:
                        p.topics.append( t )
                        pl.discard( pid )
                    else:
                        self.topics[ t ].remove( pid )
            map( lambda i: self.problems[ i ].topics.append( '#' ), pl )
            self.topics[ '#' ] = list( sorted( pl ) )

    @contextlib.contextmanager
    def count( self, pl ):
        solved = failed = todo = 0
        for p in pl:
            if p.solved:
                solved += 1
            elif p.failed:
                failed += 1
            else:
                todo += 1
        yield
        if pl:
            print '%d solved %d failed %d todo' % ( solved, failed, todo )

    def list( self, pl ):
        with self.count( pl ):
            l = 0
            for p in sorted( pl, key=lambda p: ( -p.level, p.pid ) ):
                if p.level < l:
                    print ''
                print '   ', p
                l = p.level

    def limit( self, limit ):
        self.xlimit = limit
        if self.xlimit:
            for pid in self.problems.keys():
                if pid > self.xlimit:
                    del self.problems[ pid ]

            for t, pl in self.topics.iteritems():
                self.topics[ t ] = list( filter( lambda i : i <= self.xlimit, pl ) )

            for t, pl in self.companies.iteritems():
                self.companies[ t ] = set( filter( lambda i : i <= self.xlimit, pl ) )

    def do_login( self, unused=None ):
        self.login()
        self.load( force=True )
        self.limit( self.xlimit )
        self.topic = self.pid = self.sid = None
        if self.loggedIn:
            print self.motd
            self.sessions = self.get_sessions()
            self.do_top()

    def complete_su( self, *args ):
        return self.complete_all( self.sessions.keys(), *args )

    @login_required
    def do_su( self, name ):
        if name not in self.sessions:
            prompt = self.magic( "Create session? (y/N)" )
            try:
                c = raw_input( prompt ).lower() in [ 'y', 'yes']
            except EOFError:
                c = False
            if c:
                self.sessions = self.create_session( name )

        s = self.sessions.get( name )
        if s and not s.active:
            self.sessions = self.activate_session( s.sid )
            self.load( force=True )

    def complete_chmod( self, *args ):
        return self.complete_all( self.langs, *args )

    def do_chmod( self, lang ):
        if lang in self.langs and lang != self.lang:
            self.lang = lang
            for p in self.problems.itervalues():
                p.code = ''
            self.cheatsheet.clear()
            self.sid = None
        else:
            print self.lang

    def do_ls( self, unused=None ):
        if not self.topic:
            for t in sorted( self.topics.keys() ):
                pl = self.topics[ t ]
                todo = 0
                for pid in pl:
                    if not self.problems[ pid ].solved:
                        todo += 1
                print '   ', '%3d' % todo, t
            self.do_top()

        elif not self.pid:
            pl = [ self.problems[ i ] for i in self.topics.get( self.topic ) ]
            self.list( pl )
        else:
            p = self.problems[ self.pid ]
            if not p.loaded:
                self.get_problem( p )
            print '[', ', '.join( p.topics ).title(), ']'
            try:
                print p.desc
            except UnicodeEncodeError:
                print '\n...\n'

    def do_find( self, key ):
        if key:
            if key in self.companies:
                fn = lambda p: p.pid in self.companies[ key ]
            else:
                fn = lambda p: p.slug.find( key ) != -1
            pl = list( filter( fn, self.problems.itervalues() ) )
            self.list( pl )

    def complete_cd( self, *args ):
        if self.topic:
            keys = [ str( i ) for i in self.topics[ self.topic ] ]
        else:
            keys = self.topics.keys()
        return self.complete_all( keys, *args )

    def do_cd( self, arg ):
        if arg == '..':
            if self.pid:
                self.pid = None
            elif self.topic:
                self.topic = None
        elif arg in self.topics:
            self.topic = arg
        elif arg.isdigit():
            pid = int( arg )
            if pid in self.problems:
                self.pid = pid
                topics = self.problems[ pid ].topics
                if self.topic not in topics:
                    self.topic = topics[ 0 ]

    def do_cat( self, unused ):
        if self.pad and os.path.isfile( self.tests ):
            with open( self.tests, 'r' ) as f:
                tests = f.read()
            print self.pad, '<<', ', '.join( tests.splitlines() )

    def do_pull( self, arg ):
        sync = arg is '*'
        def writable( p ):
            if sync:
                w = p.solved
            elif not os.path.isfile( self.pad ):
                w = True
            else:
                prompt = self.magic( "Replace working copy? (y/N)" )
                try:
                    w = raw_input( prompt ).lower() in [ 'y', 'yes']
                except EOFError:
                    w = False
            return w

        pl, xpid = sorted( self.problems ) if sync else [ self.pid ], self.pid
        for pid in pl:
            p = self.problems.get( pid )
            if p:
                if not p.loaded:
                    self.get_problem( p )

                if writable( p ):
                    self.pid = pid
                    with open( self.pad, 'w' ) as f:
                        f.write( p.code )
                    print self.pad

                with open( self.tests, 'w' ) as f:
                    f.write( p.test )
        self.pid, self.ts = xpid, datetime.now()

    @login_required
    def do_check( self, unused ):
        p = self.problems.get( self.pid )
        if p and os.path.isfile( self.pad ):
            with open( self.pad, 'r' ) as f:
                code = f.read()
                with open( self.tests, 'r' ) as tf:
                    tests = tf.read()
                    result = self.test_solution( p, code, tests )
                    if result:
                        print 'Input: ', ', '.join( tests.splitlines() )
                        print result

    @login_required
    def do_push( self, unused ):
        def histogram( t, times, limit=25 ):
            try:
                from ascii_graph import Pyasciigraph

                for i in xrange( len( times ) ):
                    t1, n = times[ i ]
                    if t1 >= t:
                        times[ i ] = ( str( t ) + '*', n )
                        break

                g = Pyasciigraph( graphsymbol='*' )
                for l in g.graph( 'Runtime' + 66 * ' ' + 'N  ms', times[ :limit ] ):
                    print l
            except ImportError:
                pass

        p = self.problems.get( self.pid )
        if p and os.path.isfile( self.pad ):
            with open( self.pad, 'r' ) as f:
                code = f.read()
                result = self.test_solution( p, code, full=True )
                if result:
                    self.sid, p.solved, xsolved = result.sid, result.success, p.solved
                    if p.solved:
                        runtimes = self.get_solution_runtimes( result.sid )
                        histogram( result.runtime, runtimes )
                        if not xsolved:
                            result.fintime = ( datetime.now() - self.ts ).seconds
                    else:
                        with open( self.tests, 'a+' ) as f:
                            if f.read().find( result.input ) == -1:
                                f.write( '\n' + result.input )
                    print result

    @login_required
    def do_cheat( self, limit ):
        if self.pid and self.sid:
            cs = self.cheatsheet.get( self.pid )
            if not cs:
                cs = self.get_solutions( self.pid, self.sid )
                self.cheatsheet[ self.pid ] = cs

            limit = min( len( cs ), max( int( limit ), 1 ) if limit else 1 )
            for i in xrange( limit ):
                try:
                    print cs[ i ]
                except UnicodeEncodeError:
                    print '< non-printable >'

    def do_print( self, key ):
        def order( i, j ):
            a = ( -self.problems[ i ].level, i )
            b = ( -self.problems[ j ].level, j )
            return 1 if a > b else -1 if a < b else 0

        def title( p ):
            s = str( p.pid ) + ' ' + p.slug.replace( '-', ' ' ).title()
            if p.todo:
                s = '<font color="blue">' + s + '</font>'
            elif p.failed:
                s = '<font color="red">' + s + '</font>'
            return '<h3>%s</h3>' % s

        if key in self.topics:
            topics = { key: self.topics[ key ] }
        elif key in self.companies:
            topics = { key: self.companies[ key ] }
        else:
            topics, key = self.topics, 'all'
        done = set()

        xout, sys.stdout = sys.stdout, open( self.ws + '/%s.html' % key, 'w' )
        for t in sorted( topics ):
            print '<h2>' + t.title() + '</h2>'
            for pid in sorted( topics.get( t, [] ), order ):
                if pid not in done:
                    p = self.problems[ pid ]
                    if not p.loaded:
                        self.get_problem( p )
                    try:
                        print title( p ) + p.html
                        print '<p>[', ', '.join( p.topics ).title(), ']</p>'
                        if p.solved:
                            print '<pre>' + p.code + '</pre>'
                    except UnicodeEncodeError:
                        pass
                    done.add( pid )
                    xout.write( '\r%d' % len( done ) )
                    xout.flush()
        sys.stdout.close()
        sys.stdout = xout

    def do_top( self, unused=None ):
        with self.count( self.problems.itervalues() ):
            pass

    def do_clear( self, unused ):
        os.system( 'clear' )

    def do_limit( self, limit ):
        if limit.isdigit():
            limit = int( limit )
            if limit > self.xlimit:
                self.load( force=True )
            self.limit( limit )
        elif self.xlimit:
            print self.xlimit

    def do_eof( self, arg ):
        return True

if __name__ == '__main__':
    shell = CodeShell()
    shell.do_login()
    shell.cmdloop()
