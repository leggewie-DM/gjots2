#!/usr/bin/env python

# TODO:
#   1) Add option to generate the html file in chunks
#   2) Increase number of levels to max supported by HTML (9?)
#      --> Is this a bit extreme?
#   3) -r N, --rule=N: <HR> for all levels up to N
#      --> I am not sure what this is???
#   4) -t title: Provide centered title before toc
#      --> This should also be simple, just add a branch for a centered
#           title.
#
# http://www.python.org/doc/current/lib/module-textwrap.html
# import textwrap requires Python >= 2.3

"""
From: "Munoz, Gabriel Aneceto" <MUNOZGA@uwec.edu>
To: <bhepple@freeshell.org>
Subject: Gjots2 - inquire about development status
Date: Wed, 9 Jun 2004 22:26:31 -0500

Hello again,

I sent an email last week about the status of Gjots2, and now I have
re-worked gjots2html while I was learning Python. I attached a current
version of it to this email. I do not know if you, or anyone else was
also working on changing this program, but hopefully no work is
duplicated.

The attached version of gjots2html is coded in Python, and has all the
functionality that the previous version had, plus a few more things. I
added the following functionality: embedding the output into an
existing HTML template, no table of contents (from your development
notes), '-o file' for output to a specified file, adding a link to a
cascading style sheet, and wrapping the text at a specified length
without requiring the source gjots file to be wrapped. The HTML output
is in valid XHTML v1.1. I also added the functionality to allow for an
arbitrary number of levels in the hierarchy to be supported.

You can see examples of these formats here:
http://blackhole.cs.uwec.edu/~munozga/docs/

I have successfully used this program to convert a rather large gjots
file to html, one which was not fully convertible by the old version
(I think due to the number of levels my gjots file had).

Please let me know any thoughts and concerns. I would like to add the
functionality for the other options you mentioned in the development
notes, but I would need some more explanation as to what exactly is
wanted.

Gabe
"""

import re, os, getopt, sys, textwrap

# Global variables for program preferences
VERSION = '0.1'
CONTENTS = CHUNKS = LINE = False
PRINT_TOC = True
EMBED = OUTPUT = WRAP = None
FILENAME = STYLESHEET = ''
WRAPPER = None
TITLE = "Contents"
STDOUT = sys.stdout

# Regular expressions for parsing the gjots file format
newEntry = re.compile('^\\\NewEntry$')
newFolder = re.compile('^\\\NewFolder$')
endFolder = re.compile('^\\\EndFolder$')

# Reg ex's for replacing special characters
trailDot = re.compile('\.$')  # For printNode() number beautification
link = re.compile('\s|\/|,|\+|"|=|~|\(|\)|>|<|&')
amp = re.compile('&')
quot = re.compile('"')
lt = re.compile('<')
gt = re.compile('>')
fslash = re.compile('/')
gjotsEmbed = re.compile('^INSERT GJOTS TEXT HERE$')

#
# Prints out usage information to stdout
#
def usage():
	global STDOUT
	print >>STDOUT, 'Usage: ' + os.path.basename(sys.argv[0]) + \
""" [-c] [-e template] [-h] [-k] [-l] [-n] [-o out]
                     [-s css] [-t title] [-v] [-w length] gjots_file
  -c, --contents                 Adds a link to the Table Of Contents
                                 after each section. Turned off by
                                 default.
  -e template, --embed template  Embed the output of this program
                                 a pre-existing HTML template file.
  -h, --help                     Prints this usage information.
  -k, --chunks                   Output the HTML file in chunks. The
                                 default is a single HTML file.
  -l, --lines                    Adds <HR> lines after each section.
  -n, --no-toc                   Suppress the table of contents.
  -o out, --output out           Output the HTML to specified file/dir.
  -s css, --style-sheet css      Add a link to the specified Cascading
                                 Style Sheet (in relation to your HTML
                                 root).
  -t title, --title title        Adds a title to the page. The default
                                 is the name of the gjots file.
  -v, --version                  Prints the version of this utility.
  -w length, --wrap length       Wrap the HTML output at the specified
                                 character length.

Description: Converts a gjots file to html (on stdout)"""

#
# Shifts off the last number in `node', and increments the new last
# number in the list by one. The current HTML heading is reduced (if
# necessary) to the next level lower and returned by this function.
#
def removeNode(node):
	node.pop()
	node[len(node) - 1] = node[len(node) - 1] + 1
	return headingValue(node)

#
# Pushes a new node number (default 1) onto the node list. A new HTML
# heading is incremented (if necessary) and returned.
#
def addNode(node):
	node.append(1)
	return headingValue(node)

#
# Increments the last number in the list `node' by one.
#
def incrementNode(node):
	node[len(node) - 1] = node[len(node) - 1] + 1

#
# Returns the current HTML heading level based upon the node list. This
# function keeps the range between 2 (based on our discretion) and 6
# (based on the lowest level by the HTML standard).
#
def headingValue(node):
	if len(node) + 1 > 6:
		result = 6
	else:
		result = len(node) + 1
	return result

#
# Returns a string representation of a the current node number. `node'
# is a list of numbers, and the string returned consists of each element
# seperated by a period (e.g. 1.1, 2.3.4, etc).
#
def printNode(node):
	result = ''
	for n in node:
		result += str(n) + '.'
	if len(node) > 1:
		result = trailDot.sub('', result)
	return result

#
# Formats the plain text in buffer by changing special characters to
# their HTML format (see an ascii table for values).
#
def format(buffer):
	buffer = amp.sub('&amp;', buffer)
	buffer = quot.sub('&quot;', buffer)
	buffer = lt.sub('&lt;', buffer)
	buffer = gt.sub('&gt;', buffer)
	buffer = fslash.sub('&#47;', buffer)
	return buffer

#
# Formats a string to be a valid link
#
def formatLink(l):
	return link.sub('', l)
	

def main():
	global STDOUT, WRAPPER
	global VERSION, CONTENTS, CHUNKS, LINE, EMBED, OUTPUT, TITLE, WRAP
	global FILENAME, STYLESHEET, PRINT_TOC
	# Parse the command line options
	try:
		opts, args = getopt.getopt(sys.argv[1:], 'ce:hklno:s:t:vw:', \
			['contents', 'embed=', 'help', 'chunks', 'line', 'no-toc=', \
			'output=', 'style-sheet=', 'title=', 'version', 'wrap='])
	except getopt.GetoptError:
		STDOUT = sys.stderr
		print >>STDOUT, 'error: Invalid Option(s)'
		usage()
		sys.exit(1)
	for o, a in opts:
		if o in ('-c', '--contents'):
			CONTENTS = True
		elif o in ('-e', '--embed'):
			EMBED = a
		elif o in ('-h', '--help'):
			usage()
			sys.exit()
		elif o in ('-k', '--chunks'):
			CHUNKS = True
		elif o in ('-l', '--lines'):
			LINE = True
		elif o in ('-n', '--no-toc'):
			PRINT_TOC = False
		elif o in ('-o', '--output'):
			OUTPUT = a
		elif o in ('-s', '--style-sheet'):
			STYLESHEET = a
		elif o in ('-t', '--title'):
			TITLE = a
		elif o in ('-v', '--version'):
			print os.path.basename(sys.argv[0]) + ' version ' + VERSION
			sys.exit()
		elif o in ('-w', '--wrap'):
			WRAP = a
			WRAPPER = textwrap.TextWrapper(width=int(WRAP), \
				expand_tabs=False, replace_whitespace=False, \
				initial_indent='', subsequent_indent='', \
				fix_sentence_endings=False, break_long_words=False)

	# Make sure the last argument exists (should be a gjots file)
	if not os.path.isfile(sys.argv[len(sys.argv) - 1]) or \
		len(sys.argv) <= 1:
		STDOUT = sys.stderr
		print >>STDOUT, 'error: You must specify a gjots file to convert'
		usage()
		sys.exit(1)
	FILENAME = sys.argv[len(sys.argv) - 1]
	# Set the title if not specified at the command line
	if not TITLE:
		TITLE = os.path.basename(FILENAME)
	# Re-direct output to a file if specified at the command line
	if OUTPUT:
		if not os.path.isfile(OUTPUT):
			STDOUT = open(OUTPUT, 'w')
		else:
			STDOUT = sys.stderr
			print >>STDOUT, 'error: Invalid output file - file already exists'
			usage()
			sys.exit(1)
	# Read in the HTML from a specified template file and output the new
	# file with text before and after the marked region (INSERT GJOTS TEXT
	# HERE).
	before = ''
	after = None
	if EMBED:
		if not os.path.isabs(EMBED):
			EMBED = os.path.abspath(EMBED)
		if os.path.isfile(EMBED):
			embedfile = open(EMBED, 'r')
			for line in embedfile:
				if gjotsEmbed.match(line):
					after = ''
				elif after != None:
					after += line
				else:
					before += line
			embedfile.close()
			print >>STDOUT, before
		else:
			STDOUT = sys.stderr
			print >>STDOUT, "error: Invalid output file - file doesn't exist"
			usage()
			sys.exit(1)

	# Pre-parse file for keyword order - NOTE: This is not efficient
	keywords = ['\NewEntry', '\NewFolder', '\EndFolder']
	keys = []
	file = open(FILENAME, 'r')
	for line in file:
		line = line.rstrip()
		if line in keywords: keys.append(line)
	file.close()

	# Print the header HTML information
	if not EMBED:
		print >>STDOUT, '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1 Strict//EN"'
		print >>STDOUT, '  "http://www.w3.org/TR/xhtml1/DTD/xhtml11-strict.dtd">'
		print >>STDOUT, '<html>\n<head>\n<title>' + TITLE + '</title>'
		if STYLESHEET:
			print >>STDOUT, '<link rel="stylesheet" href="' + STYLESHEET + \
				'" type="text/css"/>'
		print >>STDOUT, '</head>\n<body>\n'
	print >>STDOUT, '<p><a name="Contents">' + TITLE + '</a>\n</p>'
	if PRINT_TOC: print >>STDOUT, '<ul>'

	# Parse file for the actual conversion
	node = [1]   # Start at node number 1
	body = ''    # Holds the persistent, formatted HTML output until end
	buffer = ''  # Holds temporary parsed buffer
	H = 2        # The HTML heading level (default)
	file = open(FILENAME, 'r')
	line = (file.readline()).rstrip()
	for lookahead in file:
		lookahead = lookahead.rstrip()
		if line == '\NewEntry' and lookahead not in keywords:
			buffer = format(buffer)
			body += '<pre class="gjots-pre">\n' + buffer + '</pre>\n\n'
			if CONTENTS: body += '<a href="#Contents">Contents</a>'
			if LINE: body += '<hr/>'
			body += '<h' + str(H) + ' class="gjots-heading">' + \
				'<a class="gjots-anchor" name="' + printNode(node) + '-' + \
				formatLink(lookahead) + '">' + printNode(node) + ' ' + \
				format(lookahead) + '</a></h' + str(H) + '>\n'
			buffer = ''
			if PRINT_TOC:
				print >>STDOUT, '<li class="gjots-li"><a class="gjots-contents"' \
					+ ' href="#' + printNode(node) + '-' + formatLink(lookahead) + \
					'">' + printNode(node) + ' ' + format(lookahead) + '</a>'
			keys.pop(0)
			if PRINT_TOC and len(keys) != 0 and keys[0] != '\NewFolder':
				print >>STDOUT, '</li>'
			if len(keys) != 0 and keys[0] == '\NewEntry':
				incrementNode(node)
		elif line == '\NewFolder':
			if PRINT_TOC: print >>STDOUT, '<ul>'
			H = addNode(node)
			keys.pop(0)
		elif line == '\EndFolder':
			if PRINT_TOC: print >>STDOUT, '</ul></li>'
			H = removeNode(node)
			keys.pop(0)
		elif lookahead not in keywords:
			if WRAP and len(lookahead) > 72:
				buffer += WRAPPER.fill(lookahead) + '\n'
			else:
				buffer += lookahead + '\n'

		line = lookahead
	file.close()

	# Process any valid keywords and flush the buffer
	if PRINT_TOC:
		print >>STDOUT, '</ul></li>\n</ul>\n<p></p>'
	if WRAP and len(lookahead) > 72:
		buffer += WRAPPER.fill(lookahead)
	buffer = format(buffer)
	body += '<pre>\n' + buffer + '</pre>\n'
	if CONTENTS: body += '<a href="#Contents">Contents</a>'

	# Output the previously formatted body of the gjots file
	print >>STDOUT, body
	if not EMBED: print >>STDOUT, '</body>\n</html>'

	if EMBED:
		print >>STDOUT, after
		STDOUT.close()
	elif OUTPUT:
		STDOUT.close()

if __name__ == "__main__":
	main()
