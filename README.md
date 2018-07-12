# LeetCode CLI

Start `tmux`, `VIM` and `cli.py`. Practice as many questions as you can:-)

This tool is not affiliated with [LeetCode](https://leetcode.com).

## Download and Install

```
git clone https://github.com/chenpengcheng/cli.git
```

### Linux

```
sudo apt install nodejs
sudo pip install requests bs4 PyExecJS ascii_graph
```

### Mac OSX

```
brew install openssl
sudo easy_install pip
env LDFLAGS="-L$(brew --prefix openssl)/lib" CFLAGS="-I$(brew --prefix openssl)/include" sudo pip install cryptography
sudo easy_install requests[security] bs4 PyExecJS ascii_graph
```

## Usage

The most common commands are: `cd`, `ls`, `cat`, `check`, `push`, `cheat`, `clear` and `/`.

```
$ ./cli.py

Username: student
Password:
Welcome student!
 (\_/)
=(^.^)=
(")_(")
243 solved 17 failed 523 todo

#:/> ?
cat                     - Show test case(s).
cd      <tag|number>    - Change problem(s).
cheat   <number>        - C.H.E.A.T.
check                   - Test the solution.
chmod   <language>      - Change programming language.
clear                   - Clear screen.
find    <keyword>       - Find problems by keyword. Alias: /<keyword>.
limit   <number>        - Limit the number of problems.
login                   - Login into the online judge.
ls                      - Show problem(s).
print   [keyword]       - Print problems by keyword in HTML.
pull    [*]             - Pull latest solution(s). '*': all problems.
push                    - Submit the solution.
su      <session>       - Change session.

A tag can refer to a topic (e.g. array) or a company (e.g. amazon).
A keyword can be anything (including a tag).
Commands and options can be completed by <TAB>.
```
Control+D to exit.

## Demo

```
#:/> ls
     29 #
     81 array
     28 backtracking
      5 binary-indexed-tree
     35 binary-search
     12 binary-search-tree
     26 bit-manipulation
      3 brainteaser
     31 breadth-first-search
     60 depth-first-search
...
     13 sort
     14 stack
     62 string
      3 topological-sort
     53 tree
     12 trie
     21 two-pointers
      9 union-find
242 solved 18 failed 523 todo
```

```
#:/> cd heap
#:/heap> ls
     355 design-twitter
    *719 find-k-th-smallest-pair-distance
    *836 race-car
      23 merge-k-sorted-lists
    *218 the-skyline-problem
    *803 cheapest-flights-within-k-stops

     295 find-median-from-data-stream
    *895 shortest-path-to-get-all-keys
     373 find-k-pairs-with-smallest-sums
...
     215 kth-largest-element-in-an-array
    *692 top-k-frequent-words
    *794 swim-in-rising-water

     378 kth-smallest-element-in-a-sorted-matrix
     347 top-k-frequent-elements
     451 sort-characters-by-frequency
    *761 employee-free-time
11 solved 0 failed 17 todo
```

```
#:/heap> cd 23
#:/heap/23-merge-k-sorted-lists> ls
[Linked-List, Heap, Divide-And-Conquer, 8/20]

Merge k sorted linked lists and return it as one sorted list. Analyze and describe its complexity.
Example:

Input:
[
 1->4->5,
 1->3->4,
 2->6
]
Output: 1->1->2->3->4->4->5->6


#:/heap/23-merge-k-sorted-lists> cat
ws/23.py << ["WordDictionary","addWord","addWord","addWord","search","search","search","search"], [[],["bad"],["dad"],["mad"],["pad"],["bad"],[".ad"],["b.."]]

#:/heap/23-merge-k-sorted-lists> pull
,___,
[O.o]  Replace working copy? (y/N)
/)__)
-"--"-y
ws/23.py
```

Now that we have the problem description and the sample test case, start coding the solution and test it locally. Once the solution passed the sample test case, we can `check` it with or `push` it to the online judge.

```
#:/heap/23-merge-k-sorted-lists> check
Input:  [[1,4,5],[1,3,4],[2,6]]
Result: [1,1,2,3,4,4,5,6]
Runtime: 20 ms

#:/heap/23-merge-k-sorted-lists> push
Runtime                                                                  N  ms
###############################################################################
***********************************                                     0  64*
**********************************************************************  0  7621
***********************************                                     0  7611
***********************************                                     0  7606
***********************************                                     0  7594
***********************************                                     0  7592
***********************************                                     0  7586
***********************************                                     0  7584
***********************************                                     0  7576
***********************************                                     0  7574
***********************************                                     0  7566
***********************************                                     0  7563
***********************************                                     0  7560
***********************************                                     0  7552
***********************************                                     0  7546
***********************************                                     0  7541
***********************************                                     0  7540
***********************************                                     0  7537
***********************************                                     0  7519
***********************************                                     0  7513
***********************************                                     0  7505
**********************************************************************  0  7500
***********************************                                     0  7485
***********************************                                     0  7466
***********************************                                     0  7462
Result: 131/131 tests passed
Runtime: 64 ms
```

```
#:/heap/23-merge-k-sorted-lists> cd ..
#:/heap> /airbnb
     220 contains-duplicate-iii
      68 text-justification
      10 regular-expression-matching
    x212 word-search-ii
     269 alien-dictionary
    *336 palindrome-pairs
       2 add-two-numbers
      23 merge-k-sorted-lists
    *190 reverse-bits
    *803 cheapest-flights-within-k-stops

     227 basic-calculator-ii
     160 intersection-of-two-linked-lists
    *221 maximal-square
     385 mini-parser
     219 contains-duplicate-ii
      20 valid-parentheses
    *756 pour-water
      42 trapping-rain-water
       1 two-sum
     198 house-robber
     251 flatten-2d-vector
     415 add-strings
     202 happy-number

     108 convert-sorted-array-to-binary-search-tree
    *787 sliding-puzzle
    *757 pyramid-transition-matrix
     217 contains-duplicate
    *752 ip-to-cidr
    *761 employee-free-time
     136 single-number
20 solved 1 failed 9 todo
```
