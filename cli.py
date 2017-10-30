#!/usr/bin/env python

import cmd, contextlib, getpass, json, os, pprint, random, re, sys, time
import bs4, execjs, requests
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
        self.pid = pid
        self.slug = slug
        self.level = level
        self.topics = topics[ : ]
        self.status = status
        self.desc = self.code = self.test = ''

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
        if status == 13:
            self.errors.append( 'Output Limit Exceeded' )
        elif status == 14:
            self.errors.append( 'Time limit Exceeded' )
        elif status == 10:
            self.success = True

        ts = result.get( 'status_runtime', '' ).replace( 'ms', '' ).strip()
        self.runtime = int( ts ) if ts.isdigit() else 0

    def __str__( self ):
        limit = 25
        s = '\n'.join( self.errors )
        if s:
            s += '\n'

        if self.result:
            s += 'Result:'
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
            s += 'Time: %d ms' % self.runtime
        return s

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
            print 'Welcome %s!' % username
            self.loggedIn = True

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

    def get_problem( self, slug ):
        url = self.url + '/problems/%s/description/' % slug
        cls = { 'class' : 'question-description' }
        js = r'var pageData =\s*(.*?);'

        resp = self.session.get( url )
        desc = code = test = ''

        soup = bs4.BeautifulSoup( resp.text, 'lxml' )
        for e in soup.find_all( 'div', attrs=cls ):
            desc = e.text.strip( '\r' )
            break

        for s in re.findall( js, resp.text, re.DOTALL ):
            v = execjs.eval( s )
            for cs in v.get( 'codeDefinition' ):
                if cs.get( 'text' ) == self.language:
                    code = cs.get( 'defaultCode', '' ).strip( '\r' )
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
            'lang': self.lang,
        }

        resp = self.session.post( url, json=data, headers=headers )

        try:
            code = json.loads( resp.text ).get( 'code' )
        except ValueError:
            code = p.code
        return code

    # @login_required
    def get_solution( self, pid, token ):
        url = self.url + '/submissions/api/detail/%d/%s/%d/' % \
                ( pid, self.lang, token )

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

    # @login_required
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

    # @login_required
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

    # @login_required
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

class CodeShell( cmd.Cmd, OJMixin, Magic ):
    ws = 'ws'
    topics, companies, problems, cheatsheet = {}, {}, {}, {}
    topic = pid = sid = None
    xlimit = 0

    def __init__( self ):
        cmd.Cmd.__init__( self )
        Magic.__init__( self )
        if not os.path.exists( self.ws ):
            os.makedirs( self.ws )

    @property
    def prompt( self ):
        return self.cwd() + '> '

    def precmd( self, line ):
        line = line.lower()
        if line.startswith( '/' ):
            line = 'find ' + ' '.join( line.split( '/' ) )
        return line

    def emptyline( self ):
        pass

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

    def do_login( self, unused=None ):
        self.login()
        self.load( force=True )
        self.limit( self.xlimit )
        self.topic = self.pid = self.sid = None
        if self.loggedIn:
            print self.motd
            self.do_top()

    def complete_chmod( self, text, line, start, end ):
        keys = self.langs
        prefix, suffixes = ' '.join( line.split()[ 1: ] ), []

        for t in sorted( keys ):
            if t.startswith( prefix ):
                i = len( prefix )
                suffixes.append( t[ i: ] )

        return [ text + s for s in suffixes ]

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
            if not ( p.desc and p.code ):
                p.desc, p.code, p.test = self.get_problem( p.slug )
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

    def complete_cd( self, text, line, start, end ):
        if self.topic:
            keys = [ str( i ) for i in self.topics[ self.topic ] ]
        else:
            keys = self.topics.keys()
        prefix, suffixes = ' '.join( line.split()[ 1: ] ), []

        for t in sorted( keys ):
            if t.startswith( prefix ):
                i = len( prefix )
                suffixes.append( t[ i: ] )

        return [ text + s for s in suffixes ]

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

    def do_pull( self, unused ):
        p = self.problems.get( self.pid )
        if p:
            if not ( p.desc and p.code ):
                p.desc, p.code, p.test = self.get_problem( p.slug )
            code = self.get_latest_solution( p )
            wr = True
            if os.path.isfile( self.pad ):
                prompt = self.magic( "Replace working copy? (y/N)" )
                try:
                    if raw_input( prompt ).lower() in [ 'n', 'no']:
                        wr = False
                except EOFError:
                    return
            if wr:
                with open( self.pad, 'w' ) as f:
                    f.write( code )
            with open( self.tests, 'w' ) as f:
                f.write( p.test )
            print self.pad

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
                    self.sid = result.sid
                    p.solved = result.success
                    if result.success:
                        runtimes = self.get_solution_runtimes( result.sid )
                        histogram( result.runtime, runtimes )
                    else:
                        with open( self.tests, 'a+' ) as f:
                            if f.read().find( result.input ) == -1:
                                f.write( '\n' + result.input )
                    print result

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

    def do_print( self, unused ):
        def order( i, j ):
            a = ( -self.problems[ i ].level, i )
            b = ( -self.problems[ j ].level, j )
            return 1 if a > b else -1 if a < b else 0

        xtopic, xpid, xout = self.topic, self.pid, sys.stdout
        printed = set()

        sys.stdout = open( self.ws + '/problems.rst', 'w' )
        for topic in sorted( self.topics ):
            ol = '-' * len( topic )
            print ol +  '\n' + topic + '\n' + ol + '\n'
            self.topic = topic

            for pid in sorted( self.topics.get( topic, [] ), order ):
                if pid not in printed:
                    slug = self.problems[ pid ].slug
                    print '\n**%d %s**\n' % ( pid, slug )
                    self.pid = pid
                    self.do_ls()
                    printed.add( pid )
                    xout.write( '\r%d' % len( printed ) )
                    xout.flush()
        sys.stdout.close()

        self.topic, self.pid, sys.stdout = xtopic, xpid, xout

    def do_top( self, unused=None ):
        with self.count( self.problems.itervalues() ):
            pass

    def do_limit( self, limit ):
        if limit.isdigit():
            limit = int( limit )
            if limit > self.xlimit:
                self.load( force=True )
            self.limit( limit )
        elif self.xlimit:
            print self.xlimit

    def do_clear( self, unused ):
        os.system( 'clear' )

    def do_eof( self, arg ):
        return True

if __name__ == '__main__':
    shell = CodeShell()
    shell.do_login()
    shell.cmdloop()
