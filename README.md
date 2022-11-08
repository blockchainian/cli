# LeetCode CLI

Start `tmux`, `vim` and `leetcode-cli`. Practice as many questions as you can:-)

This tool is not affiliated with [LeetCode](https://leetcode.com).

## Install

### Mac OS X

```
brew install node
sudo easy_install leetcode-cli
```

### Linux

```
sudo apt install nodejs
sudo pip install leetcode-cli
```

## Usage

The most common commands are: `cd`, `ls`, `pull`, `cat`, `check`, `push`, `cheat`, `clear` and `/`.

```
$ leetcode-cli

 (\_/)
=(^.^)=
(")_(")
243 solved 17 failed 523 todo

#:/> ?
cat                     - Show test case(s).
cd      <tag|number>    - Change problem(s).
cheat   <number>        - Find the best solution.
check                   - Test the solution.
chmod   <language>      - Change programming language.
clear                   - Clear screen.
find    <keyword>       - Find problems by keyword. Alias: /<keyword>.
limit   <number>        - Limit the number of problems.
login                   - Login into the online judge.
ls                      - Show problem(s).
print   [keyword]       - Print problems by keyword in HTML.
pull    [*]             - Pull latest solution(s). '*': all solved problems.
push                    - Submit the solution.
su      <session>       - Change session.

A tag can refer to a topic (e.g. array) or a company (e.g. amazon).
A keyword can be anything (including a tag).
Commands and options can be completed via <TAB>.

#:/>
```

Control+D to exit.

## Demo

At the root (`/`) level. `ls` lists all the topics. `#` is for problems without a topic.

```
#:/> ls
     29 #
     81 array
     28 backtracking            <- 28 problems todo in backtracking
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

`cd <topic>` changes the current topic.

```
#:/> cd heap
#:/heap>
```

At the topic level, `ls` lists the problems by difficulty level and acceptance rate. Levels are seperated by a blank line. At each level, the problems are listed in the order of acceptance rate.
The marks: `*` means `todo`, `x` `failed`, none means `solved`.

```
#:/heap> ls
     355 design-twitter                             <- the hardest
    *719 find-k-th-smallest-pair-distance
    *836 race-car
      23 merge-k-sorted-lists
    *218 the-skyline-problem
    *803 cheapest-flights-within-k-stops

     295 find-median-from-data-stream               <- medium level
    *895 shortest-path-to-get-all-keys
     373 find-k-pairs-with-smallest-sums
...
     215 kth-largest-element-in-an-array
    *692 top-k-frequent-words
    *794 swim-in-rising-water

     378 kth-smallest-element-in-a-sorted-matrix    <- easy level
     347 top-k-frequent-elements
     451 sort-characters-by-frequency
    *761 employee-free-time                         <- the easiest
11 solved 0 failed 17 todo
```

`cd <number>` changes the current problem. Then `ls` shows the description.

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
```

`pull` downloads the latest solution and sample test case from the online judge. If no solution was submitted, a boiler plate is used. The solution/boilerplate is saved in `./ws/<number>.<ext>` and can be edited.

```
#:/heap/23-merge-k-sorted-lists> pull
,___,
[O.o]  Replace working copy? (y/N)
/)__)
-"--"-y
ws/23.py
```
`cat` show the sample test case. It is saved in `./ws/tests.dat`. Test cases can be added to it and be used by `check`.

```
#:/heap/23-merge-k-sorted-lists> cat
ws/23.py << [[1,4,5],[1,3,4],[2,6]]
```

Now that we have the problem description and the sample test case, start coding and test the solution locally.

```
$ vim ./ws/23.py
$ python ./ws/23.py
```

The default programming language is `Python`. To change it, use `chmod <language>`. Once the solution passes tests locally, we can `check` it with or `push` it to the online judge. `push` reports the runtime and number of tests passed.

```
#:/heap/23-merge-k-sorted-lists> check
Input:  [[1,4,5],[1,3,4],[2,6]]
Result: [1,1,2,3,4,4,5,6]
Runtime: 20 ms

#:/heap/23-merge-k-sorted-lists> push
Runtime                                                                  %  ms
###############################################################################
**                                                                       0  48
*****                                                                    1  52
*****************                                                        2  56
**********************************************************************   8  60
***********************************************************************  8  64*
****************************************                                 5  68
***********************************************                          6  72
***************************************************************          7  76
**************************************                                   4  80
************************                                                 3  84
****************                                                         2  88
**************                                                           2  92
************                                                             1  96
****************                                                         2  100
*****************                                                        2  104
****************                                                         2  108
***********************                                                  3  112
********************************                                         4  116
************************                                                 3  120
***********************                                                  3  124
***********************                                                  3  128
******************                                                       2  132
**********                                                               1  136
*********                                                                1  140
Rank: 20.51%
Result: 131/131 tests passed
Runtime: 64 ms
```

`/<keyword>` searches for problems matching a tag (`airbnb`) or a keyword (e.g. `palindrome`)

```
#:/heap/23-merge-k-sorted-lists> cd ..
#:/heap> cd ..
#:/> /airbnb
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

#:/>
```

The solutions are saved in the `./ws/` directory.

`print` generates a syntax-highlighted [HTML](http://www.spiderman.ly/all.html).
