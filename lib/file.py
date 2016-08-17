import os, re
import tempfile, fcntl
import inspect
from gi.repository import Gtk

import gui
from general import *
from common import *
import time # for strftime
import shutil
import string

class PasswordError(Exception):
	def __init__(self):
		pass

class LockingError(Exception):
	def __init__(self):
		pass
	
class gjotsfile:

	def _make_lockfile_name(self, filename):
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()
		dirname, basename = os.path.split(filename)

		if dirname and len(dirname) and dirname[-1] != "/":
			dirname = dirname + "/"
		name = dirname + ".#" + basename
		return name
	
	def lock_file(self, filename):
		"""

		Returns (reason, pid) where reason is:
		0: OK
		1: no permission to create lockfile
		2: already locked by another process
		
		pid is the pid of the locking process or 0 on success

		"""
		
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()
			
		if not filename or len(filename) == 0:
			filename = self.filename

		lockfile = self._make_lockfile_name(filename)

		if self.gui.debug:
			print "lock_file: lockfile name =", lockfile
		pid = 0
		
		if os.access(lockfile, os.F_OK):
			# file already exists - see if it was ours
			if not os.access(lockfile, os.W_OK):
				return (1, 0)
			try:
				fd = file(lockfile, "r", 0644)
			except IOError:
				return (1, 0)

			# fcntl.flock() returns None!! Error through exception? IOError?
			fcntl.flock(fd, fcntl.LOCK_EX)
			try:
				line = fd.readline()
				m = re.match(r"(\d+)", line)
				if m and m.group:
					pid = long(m.group(1))
			except:
				pass
			
			if self.gui.debug:
				print "lock: pid = %d\n" % pid
			if pid > 0:
				if pid == os.getpid():
					# we already own this lock:
					fcntl.flock(fd, fcntl.LOCK_UN)
					fd.close()
					return (0, pid)
				
				# hmmm - there's no getpgid() call in python
				if os.system("ps -ef |awk '{print $2}'|grep %d >/dev/null 2>&1" % pid) == 0:
					# locking process still exists:
					fcntl.flock(fd, fcntl.LOCK_UN)
					fd.close()
					return (2, pid)

		# nothing read from lockfile or process no longer exists:
		if self.gui.debug:
			print "lock_file: locking to pid", os.getpid()
		try:
			fd = file(lockfile, "w")
			fd.write("%d\n" % os.getpid())
			fcntl.flock(fd, fcntl.LOCK_UN)
			fd.close()
		except IOError:
			return (1, 0)
		return (0, 0)
		
	def unlock_file(self, filename):
		"""
		Returns 0 on success, 1 on fail
		"""
		
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()

		if not filename or len(filename) == 0:
			return 1

		# make sure we locked this file:
		lockfile = self._make_lockfile_name(filename)
		try:
			fd = file(lockfile, "r")
		except IOError:
			return 0

		fcntl.flock(fd, fcntl.LOCK_EX)
		pid = 0
		try:
			line = fd.readline()
			m = re.match(r"(\d+)", line)
			if m and m.group:
				pid = long(m.group(1))
		except:
			# nothing read - harmless
			pass
		
		retval = 1
		if pid == 0 or pid == os.getpid():
			# yes - it's ours - or it's corrupt
			os.unlink(lockfile)
			retval = 0

		fcntl.flock(fd, fcntl.LOCK_UN)
		fd.close()
		return retval
	
	def wrapItem(self, sibling, parent, title, body):
		"""
		
		Make new node after sibling. sibling=None means insert at end.
		"title" goes into the tree (left panel). "body" goes into the
		right panel.

		parent=None is a special case - it is creating the root of the tree
		
		"""

		# Too verbose to trace this
		#if self.gui.debug:
		#	print inspect.getframeinfo(inspect.currentframe())[2], vars()

		newNode = None
		if title or body:
			if title and title[-1] == '\n':
				title = title[0:-1]
			newNode = self.gui.new_node(parent, sibling, title, ''.join(body))
		return newNode

	def readItem(self, f, start, parent, title = ""):
		"""
		
		Read lines from f, populating parent, starting after "start"
		or at the end of parent if null. "title" is used to override
		the title of the first item - generally because it's the
		filename.

		If parent=None then we're creating the root item - further
		items are inserted there.

		Return the last item inserted.

		"""
		
		# Too verbose to trace this
		#if self.gui.debug:
		#	print inspect.getframeinfo(inspect.currentframe())[2], vars()

		body = []
		while 1:
			line = f.readline()
			if not line or line == "": # ie EOF
				break

			if line.find(r"\NewEntry") == 0:
				if title or body:
					start = self.wrapItem(start, parent, title, body)
					if parent == None: # we created the root item - put everything else inside there
						parent = start
						start = None
				title = ""
				body = []
				continue

			if line.find(r"\NewFolder") == 0:
				if title or body:
					start = self.wrapItem(start, parent, title, body)
					if parent == None:
						parent = start
						start = None
				title = ""
				body = []
				self.readItem(f, start=None, parent=start)
				continue

			if line.find(r"\EndFolder") == 0:
				break

			# Normal (non-special) lines:
			if not title:
				title = line
			body.append(line)
		if title or body:
			start = self.wrapItem(start, parent, title, body)
		return start

	def writeItem(self, f, treeiter, first):
		"""
		Write node to file f recursively.
		first=suppress printing first level \NewEntry and \NewFolder - we're doing root
		"""
		# Too verbose to trace this
		#if self.gui.debug:
		#	print inspect.getframeinfo(inspect.currentframe())[2], vars()

		if not first:
			f.write("\\NewEntry\n")
		body = self.gui.get_node_value(treeiter)
		if body:
			f.write(body)
			if not body[-1] == '\n':
				f.write('\n')
		treeiter = self.gui.get_first_child(treeiter)
		if treeiter:
			if not first:
				f.write("\\NewFolder\n")
			while treeiter:
				self.writeItem(f, treeiter, 0)
				treeiter = self.gui.get_next(treeiter)
			if not first:
				f.write("\\EndFolder\n")

	def get_password(self, num_fields, filename, mode, password):
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()
		secretp = 1
		feedback = " "
		confirm = password
		dirname, basename = os.path.split(filename)
		prompt = _("Enter password for ") + basename
		while 1:
			general = general_dialog(self.gui, self.gui.progName + _(": Enter Password"), prompt, OK|CANCEL,
									 num_fields, secretp, feedback,
									 _("Password: "), password,
									 _("Confirm: "),  confirm)
			if not general.get_value() == OK:
				raise PasswordError
			
			password = general.get_field1()
			confirm = general.get_field2()
			if mode == "r" or password == confirm:
				break
			feedback = _("Password was not confirmed")
		return password
	
	def ccrypt_open(self, filename, mode = "r", reuse_password = 0):
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()
		if os.system("type ccdecrypt >/dev/null 2>&1") != 0:
			self.gui.err_msg(_("Could not find the ccrypt program - please install it and try again"))
			raise PasswordError
		
		# get a password:
		if mode == "w":
			num_fields = 2
		else:
			num_fields = 1

		if not reuse_password or self.gui.password == None or self.gui.password == "":
			self.gui.password = self.get_password(num_fields, filename, mode, self.gui.password)
		envname = "DH665" # or anything you like!
		os.environ[envname] = self.gui.password
		if mode == "r":
			f = os.popen("ccdecrypt -c -E " + envname + " " + filename, "r")
		else:
			f = os.popen("ccencrypt -E " + envname + ">" + filename, "w")

		# Note - I don't think the following actually scrubs the memory for local variables - need something mutable...
		blank = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
		os.environ[envname] = blank
		if self.gui.purge_password:
			self.gui.password = blank
			self.gui.password = ""
		return f

	def gpg_open(self, filename, mode = "r", reuse_password = 0):
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()
		prog = "gpg2"
		if os.system("type " + prog + " >/dev/null 2>&1") != 0:
			prog = "gpg"
			if os.system("type " + prog + " >/dev/null 2>&1") != 0:
				self.gui.err_msg(_("Neither gpg2 nor gpg are available - please install one (perhaps package gnupg2) and try again"))
				raise PasswordError
		
		# allow agent to provide password if available:
		if os.environ["GPG_AGENT_INFO"]:
			prefix = ""
			option = ""
		else:
			if (mode == "r"):
				num_fields = 1
			else:
				num_fields = 2
			if not reuse_password or self.gui.password == None or self.gui.password == "":
				self.gui.password = self.get_password(num_fields, filename, mode, self.gui.password)
			prefix = "echo \"" + self.gui.password + "\" | "
			option = "--passphrase-fd 0 "

		if mode == "r":
			f = os.popen(prefix + prog + " --batch --no-tty --decrypt --use-agent " + option + filename + " 2>/dev/null", "r")
		else:
			scratch = tempfile.mktemp()
			cmd = "cat > " + scratch + "; " + prefix + prog + " --batch --no-tty -o - --symmetric " + option + scratch + "> " + filename + " 2>/dev/null; rm " + scratch

			f = os.popen(cmd, "w")
		blank = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
		if self.gui.purge_password:
			self.gui.password = blank
			self.gui.password = ""
		return f
	
	def ssl_open(self, filename, mode = "r", reuse_password = 0):
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()
		if os.system("type openssl >/dev/null 2>&1") != 0:
			self.gui.err_msg(_("No openssl program - please install it and try again"))
			raise PasswordError
		
		# get a password:
		if mode == "w":
			num_fields = 2
		else:
			num_fields = 1

		if not reuse_password or self.gui.password == None or self.gui.password == "":
			self.gui.password = self.get_password(num_fields, filename, mode, self.gui.password)
		if mode == "r":
			f = os.popen("echo \"" + self.gui.password + "\" | openssl des3 -d -pass stdin -in " + filename + " 2>&1", "r")
		else:
			scratch = tempfile.mktemp()
			f = os.popen("cat > " + scratch + "; echo \"" + self.gui.password + "\" | openssl des3 -pass stdin -in " + scratch + " -out " + filename + " 2>&1; rm " + scratch, "w")
		blank = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
		if self.gui.purge_password:
			self.gui.password = blank
			self.gui.password = ""
		return f
	
	def org_open(self, filename, mode = "r", reuse_password = 0):
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()
		if os.system("type org2gjots >/dev/null 2>&1") != 0:
			self.gui.err_msg(_("No org2gjots program - please install it and try again"))
			raise PasswordError

		if mode == "r":
			f = os.popen("org2gjots " + filename + " 2>&1", "r")
		else:
			f = os.popen("gjots2org " + filename + " 2>&1", "w")
		return f

	def close(self):
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2]

		if self.filename:
			self.unlock_file(self.filename)
		
	def _general_open(self, filename, mode, reuse_password = 0):
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()

		self.last_file = filename
		if mode == "w":
			try:
				backup_file = filename + "~"
				s = os.stat(filename)
				os.system("cp -f " + filename + " " + backup_file)
				os.utime(backup_file, (s.st_atime, s.st_mtime))
				os.chmod(backup_file, s.st_mode)
				# os.chown(backup_file, s.st_uid, s.st_gid) ... not permitted!!
			except OSError:
				pass
			
		exti = filename.rfind(".cpt")
		if not exti == -1:
			return self.ccrypt_open(filename, mode = mode, reuse_password = reuse_password)
		exti = filename.rfind(".gpg2")
		if not exti == -1:
			return self.gpg_open(filename, mode = mode, reuse_password = reuse_password)
		exti = filename.rfind(".gpg")
		if not exti == -1:
			return self.gpg_open(filename, mode = mode, reuse_password = reuse_password)
		exti = filename.rfind(".ssl")
		if not exti == -1:
			return self.ssl_open(filename, mode = mode, reuse_password = reuse_password)
		exti = filename.rfind(".org")
		if not exti == -1:
			return self.org_open(filename, mode = mode, reuse_password = reuse_password)
		return open(filename, mode)
		
	def _do_load(self, filename, import_after):
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()

		dirname, basename = os.path.split(filename)
			
		try:
			f = self._general_open(filename, "r")
		except IOError:
			self.gui.msg(_('Can\'t open "') + basename + '"')
			return ""
		except PasswordError:
			self.gui.msg(_("Bad password"))
			return ""
		except LockingError:
			self.gui.err_msg(_("File cannot be locked"))
			return ""

		if import_after:
			self.readItem(f, None, import_after, None)
		else:
			self.gui.flush_tree()
			# needs a try/except:
			self.readItem(f, None, None, basename)
			self.filename = filename
			self.gui.show_tree(basename)
			
		if f.close() != None:
			self.gui.err_msg(_("failed!"))
			return ""
		return self.filename
	
	def _do_store(self, filename, selection, reuse_password = 0):
		"""

		Internal storage routine - no prompting, locking or other
		checking. Save entire tree unless selection is set - in which
		we are "exporting".

		Return filename on success, "" on error

		"""
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()

		if not filename:
			return ""
		dirname, basename = os.path.split(filename)

		try:
			f = self._general_open(filename, "w", reuse_password = reuse_password)
		except IOError:
			dirname, basename = os.path.split(filename)
			self.gui.msg(_("Not saved."))
			self.gui.err_msg(_("Can't write to ") + basename)
			return ""
		except LockingError:
			self.gui.err_msg(_("Can't lock file"))
			return ""

		if selection:
			first_selected = self.gui.get_first_selected_iter()
			if not first_selected:
				self.gui.err_msg(_("Nothing selected"))
				return ""

			last_selected = self.gui.get_last_selected_iter()
			if not last_selected:
				self.gui.err_msg(_("Nothing selected"))
				return ""

			this = first_selected
			count = 0
			while this:
				count = count + 1
				next = self.gui.treestore.iter_next(this)
				if self.gui.same_iter(this, last_selected):
					next = None
				self.writeItem(f, this, 0)
				this = next
		else:
			treeiter = self.gui.get_root()
			# needs a try/except: for IO errors, eg. out of space, network failed ...
			self.writeItem(f, treeiter, 1)
		
		if f.close() != None:
			self.gui.err_msg(_("failed!"))
			return ""
		return filename
	
	def destroy(self):
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.file_get_widget(self.name).destroy()

	def on_fileselection_key_press_event(self, widget, event):
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2]
		# Nothing is needed here - return & escape work as expected
		pass
	
	def on_fileselectionCancelButton_clicked(self, widget):
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.prompt_filename = None
		self.fileselectionValue = CANCEL
		
	def on_fileselectionOkButton_clicked(self, widget):
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.prompt_filename = self.fileselection_dialog.get_filename()
		self.fileselectionValue = OK
		self.fileselection_readonly = self.file_get_widget("fileselectionReadonly").get_active()

	def get_value(self):
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2]
		return self.prompt_filename
	
	def _file_dialog(self, title, mode):
		"""
		File selection dialog
		"""
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()

		callbacks = {
			# File selector popup:
			"on_fileselection_key_press_event":     self.on_fileselection_key_press_event,
			"on_fileselectionCancelButton_clicked": self.on_fileselectionCancelButton_clicked,
			"on_fileselectionOkButton_clicked":     self.on_fileselectionOkButton_clicked,
		}

		self.name = "fileselection"
		self.gui.builder.add_from_file(self.gui.sharedir + "ui/fileDialog.ui")
		self.gui.builder.connect_signals(callbacks)
		self.file_get_widget = self.gui.gui_get_widget
			
		self.fileselection_dialog = self.file_get_widget(self.name)
		self.fileselection_dialog.set_title(title)

		self.fileselection_dialog.add_filter(self.gui.file_filter)

		if self.last_file == None:
			self.last_file = os.environ["HOME"]
		self.last_file = self.gui.backtick("readlink -n -m " + self.last_file)
		self.fileselection_dialog.set_filename(self.last_file)

		all_filter = Gtk.FileFilter()
		all_filter.add_pattern("*")
		all_filter.set_name("All files")
		self.fileselection_dialog.add_filter(all_filter)

		self.fileselection_dialog.set_action(mode)
		self.fileselection_dialog.show()
		self.fileselectionValue = WAITING
		if mode == Gtk.FileChooserAction.SAVE:
			self.fileselection_dialog.set_do_overwrite_confirmation(True)
			self.file_get_widget("fileselectionReadonly").hide()

		self.gui.builder.connect_signals(callbacks)

		while self.fileselectionValue == WAITING:
			Gtk.main_iteration()

		self.fileselection_dialog.destroy()

	def read_file(self, prompt, filename, readonly, import_after):
		"""

		Top level file reading - with prompting and locking of files.
		Reads items in after "import_after" if set, otherwise to root.

		Returns filename read in or ""

		"""
		
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()

		if prompt and not filename:
			self._file_dialog(prompt, Gtk.FileChooserAction.OPEN)
			if self.fileselectionValue != OK or not self.prompt_filename:
				return ""
		else:
			if not filename:
				filename = os.environ["HOME"]+"/.gjotsfile"
			self.prompt_filename = filename

		dirname, basename = os.path.split(self.prompt_filename)
		if import_after or self.fileselection_readonly:
			readonly = 1
			
		if not os.access(self.prompt_filename, os.R_OK):
			self.gui.err_msg(_("%s is not readable") % basename)
			return ""

		rd = Gtk.RecentData()
		rd.mime_type = "application/gjots"
		rd.app_name = "gjots2"
		rd.app_exec = "gjots2"
		Gtk.RecentManager.get_default().add_full("file://" + self.prompt_filename, rd)

		# lock the file
		while not readonly:
			reason, pid = self.lock_file(self.prompt_filename)
			if reason == 0:
				# it's locked, all in order...
				break
			if reason == 1:
				msg = _("%s: no permission") % basename
			else:
				msg = _("%s: locked by process number %d") % (basename, pid)
			general = general_dialog(self.gui,
									 title = self.gui.progName + _(": can't lock file."),
									 prompt = msg,
									 buttons = TRYAGAIN | CANCEL | READONLY,
									 secretp = 0,
									 feedback = "",
									 field1_label = "",
									 field1_default = "",
									 field2_label = "",
									 field2_default = "")
			if general.get_value() == CANCEL:
				raise LockingError
			if general.get_value() == READONLY:
				self.gui.set_readonly(1, quietly=1)
				readonly = 1
				
		retval = self._do_load(self.prompt_filename, import_after)
		self.filename_timestamp = 0
		if retval:
			if not import_after:
				self.filename = self.prompt_filename
				self.filename_timestamp = os.stat(self.filename).st_mtime
				if readonly:
					self.gui.set_readonly(1, quietly=1)
		else:
			self.unlock_file(self.prompt_filename)
			self.filename = ""
			self.gui.set_readonly(0, quietly=1)
		return retval

	# see if the file has changed since we read it - maybe something else wrote to it:
	def _check_timestamp(self):
		if self.filename_timestamp:
			dirname, basename = os.path.split(self.filename)
			try:
				s = os.stat(self.filename)
			except:
				return 0

			if s.st_mtime > self.filename_timestamp:
				timestamp = time.strftime("%Y%m%d%H%M%S", time.localtime(s.st_mtime))
				c = string.split(basename, ".gjots")
				newfilename = string.join([ c[0], timestamp, "gjots" ], ".")
				if len(c) > 1: newfilename += c[1] # add suffix, if any
					
				newfilename = os.path.join(dirname, newfilename)
				shutil.copy(self.filename, newfilename)
				if self.gui.debug: print "copied %s to %s\n" % ( basename, newfilename)
				return newfilename
		return 0
	
	def write_file(self, prompt = "", exporting=0, reuse_password=1):
		"""
		
		Top level file writing - with prompting if necessary. If no
		prompt just use the default file and don't check about
		overwriting it.

		Always lock the file before writing - leave it locked (and
		remove any other locks) unless exporting.
		
		If exporting then only write the current selection - no need
		to change the default filename to this one; otherwise, write
		the root item and change the default filename to this one.

		If we already know the password and reuse_password is 0 then
		just save the sucker.

		Return filename on success, "" on error
		
		"""
		
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()

		if self.gui.readonly or not self.filename:
			if not prompt or len(prompt) == 0:
				prompt = _("Save as ...")

		retval = ""
		while 1: # use 'while' simply so that we can use break:
			if prompt:
				self._file_dialog(prompt, Gtk.FileChooserAction.SAVE)
				if self.fileselectionValue == OK and self.prompt_filename:
					dirname, basename = os.path.split(self.prompt_filename)

					# we may need to use "fully expanded name" here:
					if self.filename == self.prompt_filename:
						if exporting:
							self.gui.err_msg(_("That file is already open!"))
							return ""
						timestamped_file = self._check_timestamp()
						
						retval = self._do_store(self.filename, 
												selection = exporting, 
												reuse_password = reuse_password)
						if timestamped_file:
							general_dialog(self.gui, self.gui.progName + _(": file has changed"),
										   _("File changed since it was read - copied to %s ") % timestamped_file,
										   OK,
										   0, 0, "",
										   "", "",
										   "",  "")
							
						if not exporting:
							try:
								s = os.stat(self.filename)
								self.filename_timestamp = s.st_mtime
							except:
								pass
						break

					reason, pid = self.lock_file(self.prompt_filename)

					if reason == 2:
						self.gui.err_msg(_("%s is locked by pid %d") % 
										 (basename, pid))
						return ""
					if reason == 1:
						self.gui.err_msg(_("Can't make a lockfile in ") + 
										 dirname)
						return ""

					# We know that the directory is writable, so we can
					# create a file here. See if it already exists, if so,
					# is it writable, if so should we overwrite it?:
					try:
						f = open(self.prompt_filename)
						f.close()

						if not os.access(self.prompt_filename, os.W_OK):
							self.unlock_file(self.prompt_filename)
							self.gui.err_msg(_("%s is not writable") % basename)
							return ""
						general = general_dialog(self.gui, 
												 self.gui.progName + _(": %s already exists.") % basename,
												 _("overwrite %s?") % basename, YES|CANCEL,
												 0, 0, "",
												 "", "",
												 "",  "")
						if not general.get_value() == OK:
							self.unlock_file(self.prompt_filename)
							return ""
					except IOError:
						pass

					retval = self._do_store(self.prompt_filename, 
											selection = exporting, 
											reuse_password = reuse_password)
					if exporting:
						self.unlock_file(self.prompt_filename)
					else:
						if retval:
							self.close()
							self.filename = self.prompt_filename
							self.gui.set_title(basename)
							try:
								s = os.stat(self.filename)
								self.filename_timestamp = s.st_mtime
							except:
								pass
					break
				else:  # self.fileselectionValue != OK
					return ""
			else: # just save the sucker
				# assert exporting == 0
				timestamped_file = self._check_timestamp()
				retval = self._do_store(self.filename, 
										selection = exporting, 
										reuse_password = reuse_password)
				if timestamped_file:
					general_dialog(self.gui, self.gui.progName + _(": file has changed"),
								   _("File changed since it was read - so it was copied to %s ") % timestamped_file,
								   OK,
								   0, 0, "",
								   "", "",
								   "",  "")
				try:
					s = os.stat(self.filename)
					self.filename_timestamp = s.st_mtime
				except:
					pass
				break

# developers may want to enable this to check the before & after file images:
#		if self.gui.dev:
#			os.system("meld " + self.prompt_filename + " " + self.prompt_filename + "~")
		
		rd = Gtk.RecentData()
		rd.mime_type = "application/gjots"
		rd.app_name = "gjots2"
		rd.app_exec = "gjots2"
		Gtk.RecentManager.get_default().add_full("file://" + self.filename, rd)
		return retval
			
	def __init__(self, gui):
		self.gui = gui
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.prompt_filename = ""
		self.filename = ""
		self.fileselectionValue = OK
		self.fileselection_readonly = False
		self.file_filter = None
		self.last_file = None

# Local variables:
# eval:(setq compile-command "cd ..; ./gjots2 test.gjots")
# eval:(setq indent-tabs-mode t)
# eval:(setq tab-width 4)
# eval:(setq python-indent 4)
# End:
