#!/usr/bin/env python

import cmd, getpass, json, os, re, requests, sys, time
from lxml import html
from bs4 import BeautifulSoup
import execjs

class Problem( object ):
    def __init__( self, pid, slug, level, status=None, desc='', code='', test='' ):
        self.pid = pid
        self.slug = slug
        self.level = level
        self.desc = desc
        self.code = code
        self.test = test
        self.status = status

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
    def fresh( self ):
        return not self.status

class Solution( object ):
    def __init__( self, pid, sid, code ):
        self.pid = pid
        self.sid = sid
        self.code = code

    def __str__( self ):
        s = '[%d ms]\n' % self.sid
        s += self.code
        return s

class Result( object ):
    def __init__( self, sid, result ):
        self.sid = sid
        self.success = False
        self.output = result.get( 'code_output', '' )
        if type( self.output ) in [ str, unicode ]:
            self.output = self.output.splitlines()
        self.runtime = result.get( 'status_runtime' )

        self.result = result.get( 'code_answer', [] )
        if not self.result:
            total = result.get( 'total_testcases' )
            passed = result.get( 'compare_result', '' ).count( '1' )
            if total:
                self.result.append( "%d/%d tests passed" % ( passed, total ) )

        self.errors = []
        for e in [ 'compile_error', 'runtime_error' ]:
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

    def __str__( self ):
        limit = 25
        s = '\n'.join( self.errors )

        if self.result:
            s += 'Result:'
            s += '\n' if len( self.result ) > 1 else ' '
            s += '\n'.join( self.result ) + '\n'

        if self.output:
            s += 'Output:'
            s += '\n' if len( self.output ) > 1 else ' '
            s += '\n'.join( self.output[ : limit ] ) + '\n'

        if not self.runtime in [ 'N/A', None ]:
            s += 'Time: ' + self.runtime
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
            print 'Welcome %s!\n' % username
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
            t = e.get( 'status' )
            problems[ i ] = Problem( pid=i, slug=s, level=l, status=t )

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
                if cs.get( 'text' ) == self.language:
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
            'lang' : self.lang,
            'test_mode' : False,
            'question_id' : str( p.pid ),
            'typed_code' : code,
            'data_input': p.test,
        }

        resp = self.session.post( url, json=data, headers=headers )
        try:
            sid = json.loads( resp.text ).get( sidKey )
            result = self.get_result( sid )
        except ValueError:
            result = None

        return result

class CodeShell( cmd.Cmd, OJMixin ):
    tags, problems, cheatsheet = {}, {}, {}
    tag = pid = sid = None
    test = '/tmp/test.dat'

    @property
    def prompt( self ):
        return self.cwd() + '> '

    def precmd( self, line ):
        return line.lower()

    def emptyline( self ):
        pass

    def cwd( self ):
        wd = '/'
        if self.tag:
            wd += self.tag
            if self.pid:
                wd += '/%d-%s' % ( self.pid, self.problems[ self.pid ].slug )
        return wd

    @property
    def pad( self ):
        if self.pid:
            return '/tmp/%d.%s' % ( self.pid, self.suffix )
        else:
            return None

    def do_login( self, unused=None ):
        self.login()
        self.tags = self.get_tags()
        self.problems = self.get_problems()
        self.tag = self.pid = self.sid = None
        if self.loggedIn:
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

    def do_ls( self, _filter ):
        if not self.tags:
            self.tags = self.get_tags()
        if not self.problems:
            self.problems = self.get_problems()

        if not self.tag:
            for t in sorted( self.tags.keys() ):
                print '   ', '%3d' % len( self.tags[ t ] ), t
        elif not self.pid:
            pl, pd = self.tags.get( self.tag ), {}
            for i in sorted( pl ):
                p = self.problems[ i ]

                if p.level not in pd:
                    pd[ p.level ] = []
                pd[ p.level ].append( p )

            solved = failed = fresh = 0
            for l in sorted( pd.keys(), reverse=True ):
                for p in pd[ l ]:
                    print '   ', p
                    if p.solved:
                        solved += 1
                    elif p.failed:
                        failed += 1
                    else:
                        fresh += 1
                print ''
            print '%d solved %d failed %d left' % ( solved, failed, fresh )
        else:
            p = self.problems[ self.pid ]
            if not ( p.desc and p.code ):
                p.desc, p.code, p.test = self.get_problem( p.slug )
            print p.desc

    def complete_cd( self, text, line, start, end ):
        if self.tag:
            keys = [ str( i ) for i in self.tags[ self.tag ] ]
        else:
            keys = self.tags.keys()
        prefix, suffixes = ' '.join( line.split()[ 1: ] ), []

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
        if os.path.isfile( self.pad ):
            print self.pad

    def do_pull( self, unused ):
        p = self.problems.get( self.pid )
        if p:
            if not ( p.desc and p.code ):
                p.desc, p.code, p.test = self.get_problem( p.slug )
            code = self.get_latest_solution( p )
            with open( self.pad, 'w' ) as f:
                f.write( code )
            with open( self.test, 'w' ) as f:
                f.write( p.test )

        print self.pad

    def do_check( self, unused ):
        p = self.problems.get( self.pid )
        if p and os.path.isfile( self.pad ):
            with open( self.pad, 'r' ) as f:
                code = f.read()
                result = self.test_solution( p, code )
                if result:
                    with open( self.test, 'r' ) as f:
                        print 'Input:', f.read()
                    print result

    def do_push( self, unused ):
        p = self.problems.get( self.pid )
        if p and os.path.isfile( self.pad ):
            with open( self.pad, 'r' ) as f:
                code = f.read()
                result = self.test_solution( p, code, full=True )
                if result:
                    self.sid = result.sid
                    if result.success:
                        p.solved = True
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

    def do_top( self, unused=None ):
        solved = failed = fresh = 0

        for p in self.problems.itervalues():
            if p.solved:
                solved += 1
            elif p.failed:
                failed += 1
            else:
                fresh += 1

        print '%d solved %d failed %d left' % ( solved, failed, fresh )

    def do_clear( self, unused ):
        os.system( 'clear' )

    def do_eof( self, arg ):
        return True

if __name__ == '__main__':
    shell = CodeShell()
    shell.do_login()
    shell.cmdloop()
