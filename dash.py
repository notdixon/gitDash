#!/usr/bin/env python3
"""
    GitDash - A Git Dashboard
    ============================================

    GitDash - A pretty frontend to the stupid content tracker.
    
    Copyright (C) 2022   notdixon <notdixon.alix@gmail.com>

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

import curses, sys, os, io
import subprocess
import webbrowser

## USER CONFIGURATION ##
HasPowerline = True                       # Are Powerline/Nerd Fonts installed and being used?

########################

isGitRepo = False
isBranchDirty = False
repo = ""
version="gitDash 1.0"
onBranch = " No Branch "
gitURL = ""

def initColors():
    # Initialize Colour
    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)

    # Last Commit Colours
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_MAGENTA) # Author
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_GREEN)   # Date
    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_YELLOW)  # Title

    # Warning Colour Pairs
    curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)     # Fatal
    curses.init_pair(6, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Warning
    curses.init_pair(7, curses.COLOR_GREEN, curses.COLOR_BLACK)   # Info

    # Branch Colour Pairs
    curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_GREEN)   # Synced
    curses.init_pair(9, curses.COLOR_BLACK, curses.COLOR_RED)     # Dirty
    curses.init_pair(10, curses.COLOR_BLACK, curses.COLOR_YELLOW) # New Branch

    # Status Bar
    curses.init_pair(11, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Inverted
    ############################################################################

def addStatusBar(screen, statusBar, width):
    screen.attron(curses.color_pair(11))
    screen.addstr(0, 0, statusBar)
    screen.addstr(0, len(statusBar) - 1, " " * (width - len(statusBar) + 1))
    screen.attroff(curses.color_pair(11))

def addRepoText(screen, repoName, colorPair):
    position = 8
    if (HasPowerline == True):
        position = 10
        screen.addstr(1, 1, f"{gitHostIcon} Origin: ")
    else:
        screen.addstr(1, 1, "Origin: ")

    screen.attron(curses.color_pair(colorPair))
    screen.addstr(1, position + 1, repoName)
    screen.attroff(curses.color_pair(colorPair))


def addBranchText(screen, branchName, colorPair):
    position = 9
    if (HasPowerline == True):
        screen.addstr(2, 1, " Branch: ")
        position = 11
    else:
        screen.addstr(2, 1, "Branch: ")

    if (isBranchDirty == True):
        colorPair = 9
        screen.attron(curses.color_pair(colorPair))
        if (HasPowerline == True):
            screen.addstr(2, position + 1, " ")
        else:
            screen.addstr(2, position + 1, "! ")
        screen.addstr(2, position + 3, branchName)
    else:
        screen.attron(curses.color_pair(colorPair))
        screen.addstr(2, position, branchName)
    screen.attroff(curses.color_pair(colorPair))

def addKeyHelp(screen, height):
    screen.attron(curses.color_pair(8))
    screen.addstr(height - 1, 1, " O ")
    screen.addstr(height - 1, 37, " W ")
    screen.addstr(height - 1, 62, " Q ")
    screen.attroff(curses.color_pair(8))
    screen.addstr(height - 1, 5, "Open Git Repository in Browser")
    screen.addstr(height - 1, 41, "View Commit History")
    screen.addstr(height - 1, 66, "Quit gitDash")

def getLastCommit(screen):
    global lastCommit_Hash
    global lastCommit_Author
    global lastCommit_Date
    global lastCommit_Title

    os.system("git show | head -n5 | sed 's/    //;s/  //;s/Author: //;s/Date: //;s/commit //' > /tmp/gitLastCommit_Full")
    commitFile = open('/tmp/gitLastCommit_Full', 'r')

    lines = commitFile.readlines()
    linelist = ["", "", "", "", ""]
    idx = 0

    for line in lines:
        linelist.insert(idx, line)
        idx += 1

    lastCommit_Hash = linelist[0]
    lastCommit_Author = linelist[1]
    lastCommit_Date = linelist[2]
    lastCommit_Title = linelist[4]
    displayLastCommit(screen, lastCommit_Author, lastCommit_Date, lastCommit_Title)

def cleanup():
    os.system("rm /tmp/git* /tmp/branch* /tmp/repo")
   
def displayLastCommit(screen, commitAuthor, commitDate, commitTitle):
    screen.addstr(4, 1, "Last Commit Information")
    screen.addstr(5, 1, "Author: ")
    screen.addstr(6, 1, "Dated: ")
    screen.addstr(7, 1, "Title: ")

    screen.attron(curses.color_pair(2))
    screen.addstr(5, 9, commitAuthor)
    screen.attron(curses.color_pair(3))
    screen.addstr(6, 9, commitDate)
    screen.attron(curses.color_pair(4))
    screen.addstr(7, 9, commitTitle)


def draw(screen):
    k = 0
    cur_x = 0
    cur_y = 1

    screen.clear()
    screen.refresh()

    initColors()

    while (k != ord('q')):
        screen.clear()
        height, width = screen.getmaxyx()


        # Arrow + Vim Keys
        if k == curses.KEY_DOWN or k == ord('j'):
            cur_y = cur_y + 1

        elif k == curses.KEY_UP or k == ord('k'):
            cur_y = cur_y - 1

        elif k == curses.KEY_LEFT or k == ord('h'):
            cur_x = cur_x - 1

        elif k == curses.KEY_RIGHT or k == ord('l'):
            cur_x = cur_x + 1

        elif k == ord('o') or k == ord('O'):
            webbrowser.open(gitURL)

        elif k == ord('w') or k == ord('W'):
            curses.endwin()
            os.system("git whatchanged")

        cur_x = max(0, cur_x)
        cur_x = min(width - 1, cur_x)
        
        cur_y = max(1, cur_y)
        cur_y = min(height - 1, cur_y)
        
        if (HasPowerline == True):
            addStatusBar(screen, f" {version} | Press 'q' to quit | {gitHostIcon}  {gitURL}", width)
        else:
            addStatusBar(screen, f" {version} | Press 'q' to quit", width)

        addRepoText(screen, repo, 2)
        addBranchText(screen, onBranch, 8)

        if (isGitRepo == True):
            getLastCommit(screen)
    
        addKeyHelp(screen, height)
        screen.move(cur_y, cur_x)
        screen.refresh()
        k = screen.getch()
    cleanup()

def main():
    global repo
    global isGitRepo
    global onBranch
    global isBranchDirty
    global gitURL
    global gitHostIcon

    # I use ZSH with different cursors for different modes, so use the BLOCK cursor
    os.system("tput reset")

    if (os.path.isdir(".git/") == True):
        isGitRepo = True

        # Get the information about the Repository - Could be cleaner and not using pipes, makes it sort
        # of platform specific to the UNIX-Like OSes.
        os.system("cat .git/config | awk '/url/ {print $3}' | sed 's/.*://g' > /tmp/repo")
        os.system("cat .git/config | awk '/url/ {print $3}' | sed 's/git@/https:\/\//;s/m:/m\//;s/\.git//' > /tmp/gitURL")
        os.system("cat .git/HEAD | awk -F/ '{print $3}' > /tmp/gitBranch")

        os.system("git status | grep 'clean' | wc -l > /tmp/branchStatus")

        # Open the files made above
        originURL = open('/tmp/repo', 'r')
        branchName = open('/tmp/gitBranch', 'r')
        branchStatus = open('/tmp/branchStatus', 'r')
        gitURL_File = open('/tmp/gitURL', 'r')
        
        branchAsText = "".join(branchStatus.readlines())
        branchAsText = branchAsText.replace('\n', '')
        if (branchAsText == "0"):
            isBranchDirty = True

        # Read the files into variables
        repo = "".join(originURL.readlines())
        onBranch = "".join(branchName.readlines())
        gitURL = "".join(gitURL_File.readlines())

        if ("github" in gitURL):
            gitHostIcon = ""
        elif ("gitlab" in gitURL):
            gitHostIcon = ""
        elif ("git.kernel.org" in gitURL):
            gitHostIcon = ""
        else:
            gitHostIcon = ""
    else:
        # This is not a repository, so we can't make the files and get info from them
        repo = " Not a Git Repo "
        onBranch = " No Branch "
        gitHostIcon = ""
    curses.wrapper(draw)

if __name__ == "__main__":
    main()

#--- LICENSE: GPL-2
