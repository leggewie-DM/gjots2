import os, sys
import gtk.glade
import gnome.ui
import gobject
import tempfile
import gconf
import pango
import time # for strftime
import pipes
import inspect
import gettext

from file import *
from prefs import *
from general import *
from common import *
from find import *
#from sort import *
from printDialog import *
from sortDialog import *
from version import *

"""

Notes:

Recall that a GtkTreeStore implements GtkTreeModel - so all treemodel
methods apply to treestore

According to file:/usr/share/gtk-doc/html/gtk/GtkTreeModel.html,
tree_row_references are not necessary as "some models guarantee that
an iterator is valid for as long as the node it refers to is valid
(most notably the GtkTreeStore and GtkListStore)."

Note that every selection is constrained to be of siblings only at the
time the selection changes - so we can always make that assumption.

"""

class gjots_gui:

	def _start_of_para(self):
		"""
		Para marker is \n\n or Unicode equiv (I suppose ???)
		"""
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		cursor_mark = self.textBuffer.get_insert()
		start_iter = self.textBuffer.get_iter_at_mark(cursor_mark)
		back_one = self.textBuffer.get_iter_at_mark(cursor_mark)
		if not back_one.backward_char():
			return start_iter
		if start_iter.ends_line() and back_one.ends_line():
			return start_iter

		back_one = self.textBuffer.get_iter_at_mark(cursor_mark)
		back_two = self.textBuffer.get_iter_at_mark(cursor_mark)
		back_two.backward_char()
		while 1:
			if not back_one.backward_char():
				return start_iter
			if not back_two.backward_char():
				return back_one
			if back_one.ends_line() and back_two.ends_line():
				return start_iter
			start_iter.backward_char()

	def _end_of_para(self):
		"""
		Para marker is \n\n or Unicode equiv (I suppose ???)
		"""
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		cursor_mark = self.textBuffer.get_insert()
		next_iter = self.textBuffer.get_iter_at_mark(cursor_mark)
		end_iter = self.textBuffer.get_iter_at_mark(cursor_mark)
		if end_iter.ends_line():
			return end_iter
		while 1:
			if not next_iter.forward_char():
				return end_iter
			if end_iter.ends_line() and next_iter.ends_line():
				return end_iter
			end_iter.forward_char()
			
	def _start_of_url(self):
		"""
		Look for a continuous sequence of characters in a single line
		that might be a url. Word marker is \n \t or space. Returns a
		TextBuffer iterator.
		"""
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		cursor_mark = self.textBuffer.get_insert()
		start_iter = self.textBuffer.get_iter_at_mark(cursor_mark)
		this_char = start_iter.get_char()
		if this_char == ' ' or this_char == '\t' or this_char == '\n':
			return start_iter

		while 1:
			if start_iter.starts_line():
				return start_iter
			if not start_iter.backward_char():
				return start_iter
			this_char = start_iter.get_char()
			if this_char == ' ' or this_char == '\t' or this_char == '\n':
				start_iter.forward_char()
				return start_iter

	def _end_of_url(self):
		"""
		Word marker is \n \t or space
		"""
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		cursor_mark = self.textBuffer.get_insert()
		end_iter = self.textBuffer.get_iter_at_mark(cursor_mark)
		next_char = end_iter.get_char()
		if next_char == ' ' or next_char == '\t' or next_char == '\n':
			return end_iter
		while 1:
			if end_iter.ends_line():
				return end_iter
			if not end_iter.forward_char():
				return end_iter
			next_char = end_iter.get_char()
			if next_char == ' ' or next_char == '\t' or next_char == '\n':
				return end_iter
			
	def do_format_paragraph(self):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]

		text_formatter=self.client.get_string(self.text_formatter_path)
		r = text_formatter.find(" ")
		if r:
			bin = text_formatter[0:r]
		else:
			bin = text_formatter
		if os.system("type %s >/dev/null 2>&1" % bin):
			self.err_msg(_("External formatter \"%s\" is not installed - can't format") % bin)
			return
		
		start_iter = self._start_of_para()
		end_iter = self._end_of_para()

		para = self.textBuffer.get_text(start_iter, end_iter)
		t = pipes.Template()
		if text_formatter.find("%d") >= 0:
			runstring = text_formatter % self.client.get_int(self.line_length_path)
		else:
			runstring = text_formatter
		t.append(runstring, "--")
		scratch = tempfile.mktemp()
		f = t.open(scratch, "w")
		f.write(para)
		f.close()
		para = open(scratch, "r").read()
		if para and para[-1] == '\n':
			para = para[0:-1]
		if self.trace:
			print ("\"%s\"\n" % para)
		self.textBuffer.place_cursor(start_iter)
		self.textBuffer.delete(start_iter, end_iter)
		self.textBuffer.insert(start_iter, para, len(para))

		# move to next para:
		if start_iter.forward_char():
			start_iter.forward_char()
		self.textBuffer.place_cursor(start_iter)
		return
	
	def do_time_stamp(self):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		format = self.client.get_string(self.date_format_path)
		newstring = time.strftime(format)
		self.textBuffer.insert_at_cursor(newstring, len(newstring))
		return
	
	def on_gconf_line_length_changed(self, client, cnxn_id, entry, label):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		if self.trace:
			print "line_length=", client.get_int(self.line_length_path)
		return
	
	def on_gconf_text_formatter_changed(self, client, cnxn_id, entry, label):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		if self.trace:
			print "text_formatter=", client.get_int(self.text_formatter_path)
		return
	
	def on_gconf_external_editor_changed(self, client, cnxn_id, entry, label):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		if self.trace:
			print "external_editor = ",client.get_string(self.external_editor_path)
		return

	def on_gconf_date_format_changed(self, client, cnxn_id, entry, label):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		if self.trace:
			print "date_format=", client.get_string(self.date_format_path)
		return

	def on_gconf_print_command_changed(self, client, cnxn_id, entry, label):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		if self.trace:
			print "print_command=", client.get_string(self.print_command_path)
		return

	def on_gconf_text_font_changed(self, client, cnxn_id, entry, label):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		if self.trace:
			print "text_font=", client.get_string(self.text_font_path)
		font_desc = pango.FontDescription(self.client.get_string(self.text_font_path))
		self.textView.modify_font(font_desc)
		return

	def on_gconf_top_toolbar_changed(self, client, cnxn_id, entry, label):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		value = self.client.get_bool(self.top_toolbar_path)
		w = self.xml.get_widget("topDockItem")
		if w:
			if value:
				w.show()
			else:
				w.hide()

		# how come this doesn't create an infinit loop - doesn't the
		# GtkMenuChecklist item get a notification?
		w = self.xml.get_widget("topToolbarCheckMenuItem")
		if w:
			w.set_active(value)
		return
	
	def on_gconf_side_toolbar_changed(self, client, cnxn_id, entry, label):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		value = self.client.get_bool(self.side_toolbar_path)
		w = self.xml.get_widget("treeDockItem")
		if w:
			if value:
				w.show()
			else:
				w.hide()

		# how come this doesn't create an infinit loop - doesn't the
		# GtkMenuChecklist item get a notification?
		w = self.xml.get_widget("treeToolbarCheckMenuItem")
		if w:
			w.set_active(value)
		return
	
	def on_gconf_show_icon_text_changed(self, client, cnxn_id, entry, label):
		if self.client.get_bool(self.show_icon_text_path):
			self.xml.get_widget("topToolbar").set_style(gtk.TOOLBAR_BOTH)
			self.xml.get_widget("treeToolbar").set_style(gtk.TOOLBAR_BOTH)
		else:
			self.xml.get_widget("topToolbar").set_style(gtk.TOOLBAR_ICONS)
			self.xml.get_widget("treeToolbar").set_style(gtk.TOOLBAR_ICONS)

		self.xml.get_widget("showIconTextCheckMenuItem").set_active(self.client.get_bool(self.show_icon_text_path))
		return

	def on_gconf_status_bar_changed(self, client, cnxn_id, entry, label):
		if self.client.get_bool(self.status_bar_path):
			self.xml.get_widget("appbar").show()
		else:
			self.xml.get_widget("appbar").hide()

		self.xml.get_widget("statusBarMenuItem").set_active(self.client.get_bool(self.status_bar_path))
		return

	def on_gconf_pane_position_changed(self, client, cnxn_id, entry, label):
		self.xml.get_widget("treeTextPane").set_position(client.get_int(self.pane_position_path))
		return

	def _setup_gconf(self):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.base_path = "/apps/" + self.progName

		self.line_length_path = self.base_path + "/line_length"
		self.text_formatter_path = self.base_path + "/text_formatter"
		self.external_editor_path = self.base_path + "/external_editor"
		self.date_format_path = self.base_path + "/date_format"
		self.text_font_path = self.base_path + "/text_font"
		self.top_toolbar_path = self.base_path + "/top_toolbar"
		self.side_toolbar_path = self.base_path + "/side_toolbar"
		self.show_icon_text_path = self.base_path + "/show_icon_text"
		self.status_bar_path = self.base_path + "/status_bar"

		self.pane_position_path = self.base_path + "/pane_position"

		self.initialised_path = self.base_path + "/initialised"

		self.find_text_path = self.base_path + "/find_text"
		self.replace_text_path = self.base_path + "/replace_text"
		self.find_match_case_path = self.base_path + "/find_match_case"
		self.find_global_path = self.base_path + "/find_global"
		self.find_regex_path = self.base_path + "/find_regex"
		self.find_backwards_path = self.base_path + "/find_backwards"

		self.width_path = self.base_path + "/width"
		self.height_path = self.base_path + "/height"

		self.print_page_path = self.base_path + "/print_page"
		self.print_selection_path = self.base_path + "/print_selection"
		self.print_all_path = self.base_path + "/print_all"
		self.print_command_path = self.base_path + "/print_command"
		self.print_page_feed_path = self.base_path + "/print_page_feed"
		self.print_bold_title_path = self.base_path + "/print_bold_title"

		self.sort_ascending_path = self.base_path + "/sort_ascending"
		self.sort_alpha_path = self.base_path + "/sort_alpha"
		self.sort_items_path = self.base_path + "/sort_items"
		self.sort_sublevels_path = self.base_path + "/sort_sublevels"
		
		self.client = gconf.client_get_default()
		self.client.add_dir(self.base_path, gconf.CLIENT_PRELOAD_NONE)

		# handle startup defaults:
		
		if not self.client.get_int(self.line_length_path):
			self.client.set_int(self.line_length_path, 70)

		if not self.client.get_string(self.text_formatter_path):
			self.client.set_string(self.text_formatter_path, "fmt -w %d")

		if not self.client.get_string(self.print_command_path):
			self.client.set_string(self.print_command_path, "gjots2lpr $1")

		if not self.client.get_string(self.external_editor_path):
			if os.system("type nedit >/dev/null 2>&1") == 0:
				self.client.set_string(self.external_editor_path, "nedit %s")
			elif os.system("type xedit >/dev/null 2>&1") == 0:
				self.client.set_string(self.external_editor_path, "xedit %s")
			else:
				self.client.set_string(self.external_editor_path, "xterm -e vi %s")

		if not self.client.get_string(self.date_format_path):
			self.client.set_string(self.date_format_path, "%F" )

		if not self.client.get_string(self.text_font_path):
			self.client.set_string(self.text_font_path, "Courier 10 Pitch 10")

		if not self.client.get_string(self.find_text_path):
			self.client.set_string(self.find_text_path, "")

		if not self.client.get_string(self.replace_text_path):
			self.client.set_string(self.replace_text_path, "")

		if not self.client.get_int(self.pane_position_path):
			self.client.set_int(self.pane_position_path, 211)

		font_desc = pango.FontDescription(self.client.get_string(self.text_font_path))
		self.textView.modify_font(font_desc)
		
		if not self.client.get_int(self.sort_sublevels_path):
			self.client.set_int(self.sort_sublevels_path, 1)

		# There is no get_bool_with_default() so we have to test for first invocation:
		if not self.client.get_bool(self.initialised_path):
			print _("not initialised")
			self.client.set_bool(self.top_toolbar_path, 1)
			self.client.set_bool(self.side_toolbar_path, 1)
			self.client.set_bool(self.show_icon_text_path, 0)
			self.client.set_bool(self.initialised_path, 1)
			self.client.set_bool(self.find_match_case_path, 0)
			self.client.set_bool(self.find_global_path, 0)
			self.client.set_bool(self.find_regex_path, 0)
			self.client.set_bool(self.find_backwards_path, 0)
			self.client.set_bool(self.print_page_path, 1)
			self.client.set_bool(self.print_selection_path, 0)
			self.client.set_bool(self.print_all_path, 0)
			self.client.set_bool(self.print_page_feed_path, 0)
			self.client.set_bool(self.print_bold_title_path, 0)
			self.client.set_bool(self.sort_ascending_path, 1)
			self.client.set_bool(self.sort_alpha_path, 1)
			self.client.set_bool(self.sort_items_path, 1)
			
		self.on_gconf_top_toolbar_changed(self.client, 0, 0, 0)
		self.on_gconf_side_toolbar_changed(self.client, 0, 0, 0)
		self.on_gconf_show_icon_text_changed(self.client, 0, 0, 0)
		self.on_gconf_status_bar_changed(self.client, 0, 0, 0)
		self.on_gconf_pane_position_changed(self.client, 0, 0, 0)

		# setup notifiers:
		
		self.client.notify_add(self.line_length_path, self.on_gconf_line_length_changed, self.gjots)
		self.client.notify_add(self.text_formatter_path, self.on_gconf_text_formatter_changed, self.gjots)
		self.client.notify_add(self.external_editor_path, self.on_gconf_external_editor_changed, self.gjots)
		self.client.notify_add(self.date_format_path, self.on_gconf_date_format_changed, self.gjots)
		self.client.notify_add(self.text_font_path, self.on_gconf_text_font_changed, self.gjots)
		self.client.notify_add(self.top_toolbar_path, self.on_gconf_top_toolbar_changed, self.gjots)
		self.client.notify_add(self.side_toolbar_path, self.on_gconf_side_toolbar_changed, self.gjots)
		self.client.notify_add(self.show_icon_text_path, self.on_gconf_show_icon_text_changed, self.gjots)
		self.client.notify_add(self.status_bar_path, self.on_gconf_status_bar_changed, self.gjots)
		self.client.notify_add(self.pane_position_path, self.on_gconf_pane_position_changed, self.gjots)
		self.client.notify_add(self.print_command_path, self.on_gconf_print_command_changed, self.gjots)
		return
	
	def _create_empty_tree(self):
		# create an empty tree:
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.gjotsfile = gjotsfile(self)
		self.flush_tree()
		self.new_node(None, None, self.progName, "")
		self.show_tree(self.progName)

	def flush_tree(self):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.treestore = gtk.TreeStore(gobject.TYPE_STRING, # title == first line of body except for root, which is filename
									   gobject.TYPE_STRING, # body
									   gobject.TYPE_INT)    # body_temp_flag - used after creating new items
		
	def set_title(self, basename):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()
		self.gjots.set_title(self.progName + ": %s" % basename)
		
	def show_tree(self, basenanme):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()
		# remove the old column, if there:
		column = self.treeView.get_column(0)
		if column:
			self.treeView.remove_column(column)

		self.treeView.set_model(self.treestore)
		renderer = gtk.CellRendererText()

		column = gtk.TreeViewColumn(self.progName, renderer, text=0)
		self.column = column
		self.treeView.append_column(column)
		self.set_title(basenanme)
		self.treeView.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
		self.treeView.show()
		self.root = self.treestore.get_iter_first()

		return

	def get_node_value(self, treeiter):
		"Get the text value of the node at location 'treeiter'"
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		return self.treestore.get_value(treeiter, 1)

	def get_node_title(self, treeiter):
		"Get the title value of the node at location 'treeiter'"
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		body = self.treestore.get_value(treeiter, 1)
		eol = body.find("\n")
		if eol >= 0:
			title = body[0:eol]
		else:
			title = body
		return title

	def get_first_child(self, treeiter):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		return self.treestore.iter_nth_child(treeiter, 0)

	def get_root(self):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		return self.treestore.get_iter_first()
	
	def get_next(self, treeiter):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		return self.treestore.iter_next(treeiter)

	def get_linear_next(self, iter):
		"""

		Get the very next tree item - if current has a child, return
		it. Otherwise, return the next sibling. If no more siblings,
		get the next sibling of the parent recursively.

		"""

		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		next = self.treestore.iter_children(iter)
		if next:
			return next

		next = self.treestore.iter_next(iter)
		if next:
			return next

		while 1:
			iter = self.treestore.iter_parent(iter)
			if not iter:
				return None
			next = self.treestore.iter_next(iter)
			if next:
				return next
		
	def new_node(self, parent, sibling, title, body):
		# bit too verbose to trace:
		#if self.trace:
		#	print inspect.getframeinfo(inspect.currentframe())[2], vars()
		if sibling:
			treeiter = self.treestore.insert_after(parent, sibling)
		else:
			treeiter = self.treestore.insert_before(parent, None) # None means insert at end!
		self.treestore.set_value(treeiter, 0, title)
		self.treestore.set_value(treeiter, 1, body)
		self.treestore.set_value(treeiter, 2, 0) # temp_flag
		return treeiter

	def _do_new_page(self):
		"""
		Inserts a new blank item into the tree after the last one selected. Make the new item the selection.
		"""
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		sibling = self.get_last_selected_iter()
		if not sibling or self.same_iter(sibling, self.get_root()):
			# nothing selected or tree is empty or root is selected - insert at end
			parent = self.get_root()
			newnode = self.treestore.insert_before(parent, None)
		else:
			parent = self.treestore.iter_parent(sibling)
			newnode = self.treestore.insert_after(parent, sibling)
		self.treestore.set_value(newnode, 0, self.temp_text)
		self.treestore.set_value(newnode, 1, self.temp_text)
		self.treestore.set_value(newnode, 2, 1) # body is temporary

		# Make sure new item is visible:
		# self.treeView.expand_to_path(self.treestore.get_path(newnode)) ... not in pygtk-2.0
		parent_path = self.treestore.get_path(parent)
		self.treeView.expand_row(parent_path, 0)

		# narrow the selection to the new item:
		self._warp(newnode)

		# Now put the cursor into the right place
		self.textView.grab_focus()
		self.dirtyflag = "* "

	def _do_new_child(self):
		"""
		Inserts a new blank item as a child of the last one selected.
		"""
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.dirtyflag = "* "
		parent = self.get_last_selected_iter()
		if not parent:
			# nothing selected or tree is empty - just add an new page
			self._do_new_page()
			return
		new_child = self.treestore.insert_before(parent, None)
		self.treestore.set_value(new_child, 0, self.temp_text)
		self.treestore.set_value(new_child, 1, self.temp_text)
		self.treestore.set_value(new_child, 2, 1) # body is temporary

		# Make sure new item is visible: 
		parent_path = self.treestore.get_path(parent)
		self.treeView.expand_row(parent_path, 0)

		# narrow the selection to the new child:
		self._warp(new_child)

		# Now put the cursor into the right place
		self.textView.grab_focus()

	def _do_move_up(self):
		"""
		Move the current selection before the first's sibling, if any.
		"""
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		first_selected = self.get_first_selected_iter()
		if not first_selected:
			self.msg(_("Nothing selected"))
			return
		parent = self.treestore.iter_parent(first_selected)
		if not parent:
			self.msg(_("No parent!"))
			return
		this = self.treestore.iter_children(parent) # returns first sibling of first_selected
		if not this:
			self.msg(_("No child!"))
			return
		if self.same_iter(this, first_selected):
			self.msg(_("Can't go any further"))
			return

		# scan the siblings until we get to the first_selected:
		while (this):
			next = self.treestore.iter_next(this)
			if not next:
				self.msg(_("Internal error!"))
				return
			if self.same_iter(next, first_selected):
				pivot = this
				# now scan again, this time looking for selected items and moving before pivot
				this = self.treestore.iter_children(parent) # returns first child
				while this:
					if self.treeView.get_selection().iter_is_selected(this):
						self.treestore.move_before(this, pivot) # gtk 2.2 only
					this = self.treestore.iter_next(this)
				self.dirtyflag = "* "
				return
			this = next
			
	def _do_move_down(self):
		"""
		Move the current selection after the last's sibling, if any.
		"""
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		first_selected = self.get_first_selected_iter()
		if not first_selected:
			self.msg(_("Nothing selected"))
			return
		last_selected = self.get_last_selected_iter()
		if not last_selected:
			self.msg(_("Nothing selected"))
			return

		parent = self.treestore.iter_parent(last_selected)
		if not parent:
			self.msg(_("No parent!"))
			return

		pivot = self.treestore.iter_next(last_selected)
		if not pivot:
			self.msg(_("Can't go any further"))
			return

		# now scan siblings looking for selected items and moving after pivot
		this = self.treestore.iter_children(parent) # returns first sibling of last_selected
		if not this:
			self.msg(_("No child!"))
			return

		while this:
			next = self.treestore.iter_next(this)
			if self.treeView.get_selection().iter_is_selected(this):
				self.treestore.move_after(this, pivot) # gtk 2.2 only
				self.dirtyflag = "* "
			this = next
			
	def _do_move_left(self):
		"""

		"Promote" - selection becomes a sibling of its parent -
		treestore.move_after() only operates within one level so we
		can't use it here - instead, it looks like we have to write
		all items out to disc and then read them back in at the right
		position. Sigh.
		
		"""
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		self.sync_text_buffer()
		first_selected = self.get_first_selected_iter()
		if not first_selected:
			self.msg(_("Nothing selected"))
			return
		last_selected = self.get_last_selected_iter()
		if not last_selected:
			self.msg(_("Nothing selected"))
			return
		parent = self.treestore.iter_parent(last_selected)
		if not parent:
			self.msg(_("No parent!"))
			return
		grandparent = self.treestore.iter_parent(parent)
		if not grandparent:
			self.msg(_("Can't go further!"))
			return

		# temporarily disconnect selection updating as structure is unstable (bug 1250753):
		self.treeView.get_selection().disconnect(self.on_tree_selection_changed_handler)
		f = tempfile.TemporaryFile()
		this = first_selected
		while this:
			next = self.treestore.iter_next(this)
			if self.same_iter(this, last_selected):
				next = None
			self.gjotsfile.writeItem(f, this, 0)
			if not self.treestore.remove(this): # returns false if at end
				next = None
			this = next
				
		f.seek(0, 0)
		last_selected = self.gjotsfile.readItem(f, start=parent, parent=grandparent)

		# Now, reselect the items (on_tree_selection_changed is
        # disabled, so we also need to manually set self.current_item!):
		self.current_item = None
		this = self.treestore.iter_next(parent)
		while this:
			if not self.current_item: self.current_item = this
			next = self.treestore.iter_next(this)
			if self.same_iter(this, last_selected):
				next = None
			self.treeView.get_selection().select_iter(this)
			this = next

		self.on_tree_selection_changed_handler = self.treeView.get_selection().connect("changed", self.on_tree_selection_changed)
		self.dirtyflag = "* "

	def _do_move_right(self):
		"""

		"Demote" - selected items become children of the previous
		item, if any. treestore.move_after() only operates within one
		level so we can't use it here - instead, it looks like we have
		to write all items out to disc and then read them back in at
		the right position. Sigh.

		"""
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		
		self.msg("")
		self.sync_text_buffer()
		first_selected = self.get_first_selected_iter()
		if not first_selected:
			self.msg(_("Nothing selected"))
			return
		
		last_selected = self.get_last_selected_iter()
		if not last_selected:
			self.msg(_("Nothing selected"))
			return
		
		parent = self.treestore.iter_parent(last_selected)
		if not parent:
			self.msg(_("No parent!"))
			return

		newParent = self.treestore.iter_children(parent) # returns first sibling of selected items
		if self.same_iter(first_selected, newParent):
			# create a new node for this lot to sit under:
			newParent = self.treestore.insert_after(parent, None)
			self.treestore.set_value(newParent, 0, self.temp_text)
			self.treestore.set_value(newParent, 1, self.temp_text)
			self.treestore.set_value(newParent, 2, 1) # temp_flag
		else: # scan forward for prior item:
			while newParent:
				next = self.treestore.iter_next(newParent)
				if self.same_iter(next, first_selected):
					break;
				newParent = next

		if not newParent:
			self.msg(_("Internal error!"))
			return
		
		# write out items to temporary file: 
		f = tempfile.TemporaryFile()
		this = first_selected
		# temporarily disconnect selection updating as structure is unstable (bug 1250753):
		self.treeView.get_selection().disconnect(self.on_tree_selection_changed_handler)
		while this:
			next = self.treestore.iter_next(this)
			if self.same_iter(this, last_selected):
				next = None
			self.gjotsfile.writeItem(f, this, 0)
			if not self.treestore.remove(this): # returns false if no more items
				next = None
			this = next

		# Now read them into the right place:
		f.seek(0, 0)

		# what is last item in newParent? Used to compute new selection.
		last_item = None
		num_children = self.treestore.iter_n_children(newParent)
		if num_children > 0:
			last_item = self.treestore.iter_nth_child(newParent, num_children - 1)
			
		# read into end of newParent
		last_selected = self.gjotsfile.readItem(f, None, newParent)
		
		# make sure new parent is visible:
		parent_path = self.treestore.get_path(newParent)
		self.treeView.expand_row(parent_path, 0)

		# Now, reselect the items (on_tree_selection_changed is
        # disabled, so we also need to manually set self.current_item!):
		if last_item:
			this = self.treestore.iter_next(last_item)
		else:
			this = self.treestore.iter_children(newParent)

		self.current_item = None
		while this:
			if not self.current_item: self.current_item = this
			next = self.treestore.iter_next(this)
			if self.same_iter(this, last_selected):
				next = None
			self.treeView.get_selection().select_iter(this)
			this = next
			
		self.on_tree_selection_changed_handler = self.treeView.get_selection().connect("changed", self.on_tree_selection_changed)
		self.dirtyflag = "* "
	
	def _new_tree_cut_buffer(self):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		if self.tree_cutbuffer:
			self.tree_cutbuffer.close()
		# TODO: How do I enable/disable the paste button for both tree and
		# text operations???
		#self._disable_tree_paste()
		self.tree_cutbuffer = tempfile.TemporaryFile()

	def _iter_prev(self, this):
		"""
		This is not provided by gtk2 !!

		This is the obvious implementation but it doesn't work -
		this_path.prev() barfs with: AttributeError: 'tuple' object
		has no attribute 'prev'

		this_path = self.treestore.get_path(this)
		if this_path.prev():
			return self.treestore.get_iter(this_path)
		else:
			return None
		"""

		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]

		if not this:
			return None
		
		parent = self.treestore.iter_parent(this)
		if not parent:
			self.msg(_("No parent!"))
			return
		
		iter = self.treestore.iter_children(parent)
		if iter == None or self.same_iter(iter, this):
			return None

		while iter:
			next = self.treestore.iter_next(iter)
			if not next:
				return None
			if self.same_iter(next, this):
				return iter
			iter = next
		return None

	def get_selected_text(self):
		"""

		Returns (text, insert, selection_bound)

		"""
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		insert = self.textBuffer.get_iter_at_mark(self.textBuffer.get_insert())
		selection_bound = self.textBuffer.get_iter_at_mark(self.textBuffer.get_selection_bound())
		if insert and selection_bound:
			return (self.textBuffer.get_text(insert, selection_bound), insert, selection_bound)
		else:
			return (None, None, None)
			
	def _do_text_cut(self):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		text, insert, select_bound = self.get_selected_text()
		if text and len(text):
			if self.clipboard:
				self.textBuffer.cut_clipboard(self.clipboard, self.textView.get_editable())
				self.msg(_("Text cut"))
		return
		
	def _do_text_copy(self):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		text, insert, select_bound = self.get_selected_text()
		if text and len(text):
			if self.clipboard:
				self.textBuffer.copy_clipboard(self.clipboard)
				self.msg(_("Text copied"))
		return

	def _do_text_paste(self):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		display = self.display
		if self.clipboard:
			cursor_mark = self.textBuffer.get_insert()
			insert_iter = self.textBuffer.get_iter_at_mark(cursor_mark)
			self.textBuffer.paste_clipboard(self.clipboard, insert_iter, self.textView.get_editable())
			self.msg(_("Text pasted"))
		return

	def _do_text_select_all(self):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		self.textBuffer.select_range(self.textBuffer.get_start_iter(),
			self.textBuffer.get_end_iter())
		self.msg(_("All text selected"))
		return

	def _do_tree_select_all(self):
		self.msg("")
		self.treeView.get_selection().select_all()
		self.msg(_("All tree items selected"))

	def _do_split_item(self):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		body, start_iter, end_iter = self.get_selected_text()
		if not body:
			self.msg(_("Nothing selected!"))
			return
		self.textBuffer.delete(start_iter, end_iter)
		self.sync_text_buffer()
		eol = body.find("\n")
		if eol >= 0:
			title = body[0:eol]
		else:
			title = body
		self._do_new_page()
		self.textBuffer.insert_at_cursor(body, len(body))
		self.dirtyflag = "* "
		return

	def _do_merge_items(self):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		first_selected = self.get_first_selected_iter()
		if not first_selected:
			self.msg(_("Nothing selected"))
			return

		if self.same_iter(first_selected, self.get_root()):
			self.msg(_("Can't merge the root item"))
			return
		
		last_selected = self.get_last_selected_iter()
		if not last_selected:
			self.msg(_("Nothing selected"))
			return

		if self.same_iter(first_selected, last_selected):
			self.msg(_("Nothing to merge"))
			return

		# First, make sure nothing has a child:
		this = first_selected
		while this:
			if self.treestore.iter_children(this):
				self.msg(_("Can't merge items that have children"))
				return
			if self.same_iter(this, last_selected):
				break
			this = self.treestore.iter_next(this)

		# Copy the text into the first one selected:
		this = first_selected
		count = 0
		this = self.treestore.iter_next(this)
		while this:
			count = count + 1
			body = self.treestore.get_value(first_selected, 1) + "\n" + self.get_node_value(this)
			self.treestore.set_value(first_selected, 1, body)
			if self.same_iter(this, last_selected):
				break
			this = self.treestore.iter_next(this)

		# Now delete all except the first one selected:
		this = first_selected
		this = self.treestore.iter_next(this)
		while this:
			next = self.treestore.iter_next(this)
			if self.same_iter(this, last_selected):
				next = 0
			if not self.treestore.remove(this): # returns false if no more items
				break
			this = next
		
		self.dirtyflag = "* "
		self.msg(_("%d items merged") % count)
		return

	def _show_all(self, item):
		"""
		Recursively open child below this point.
		"""
		if not item:
			return
		child = self.treestore.iter_children(item)
		if not child:
			return
		path = self.treestore.get_path(item)
		self.treeView.expand_row(path, 0)
		while child:
			self._show_all(child)
			child = self.get_next(child)
		
	def _do_show_all(self):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		if self.current_item:
			self._show_all(self.current_item)
		return

	def _do_hide_all(self):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		self.treeView.collapse_all()
		item = self.get_root()
		path = self.treestore.get_path(item)
		self.treeView.expand_row(path, 0)
		return
	
	def _do_tree_cut(self):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		first_selected = self.get_first_selected_iter()
		if not first_selected:
			self.msg(_("Nothing selected"))
			return

		if self.same_iter(first_selected, self.get_root()):
			self.msg(_("Can't delete the root item"))
			return
		
		last_selected = self.get_last_selected_iter()
		if not last_selected:
			self.msg(_("Nothing selected"))
			return

		new_selection = self.treestore.iter_next(last_selected)
		if not new_selection:
			new_selection = self._iter_prev(first_selected)
		if not new_selection:
			new_selection = self.treestore.iter_parent(first_selected)
			
		self._new_tree_cut_buffer()
		this = first_selected
		count = 0
		while this:
			count = count + 1
			next = self.treestore.iter_next(this)
			if self.same_iter(this, last_selected):
				next = None
			self.gjotsfile.writeItem(self.tree_cutbuffer, this, 0)
			if not self.treestore.remove(this): # returns false if no more items
				next = None
			this = next
		#self._enable_tree_paste()
		if new_selection:
			self.treeView.get_selection().select_iter(new_selection)
		self.dirtyflag = "* "
		self.msg(_("%d tree items cut") % count)

	def _do_tree_copy(self):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		first_selected = self.get_first_selected_iter()
		if not first_selected:
			self.msg(_("Nothing selected"))
			return
		
		last_selected = self.get_last_selected_iter()
		if not last_selected:
			self.msg(_("Nothing selected"))
			return
		
		self._new_tree_cut_buffer()
		this = first_selected
		count = 0
		while this:
			count = count + 1
			next = self.treestore.iter_next(this)
			if self.same_iter(this, last_selected):
				next = None
			self.gjotsfile.writeItem(self.tree_cutbuffer, this, 0)
			this = next
		#self._enable_tree_paste()
		self.msg(_("%d tree items copied") % count)
				
	def _do_tree_paste(self):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		if not self.tree_cutbuffer:
			self.msg(_("Nothing to paste"))
			return
		
		last_selected = self.get_last_selected_iter()
		if not last_selected:
			self.msg(_("Nothing selected"))
			return
		
		parent = self.treestore.iter_parent(last_selected)
		if not parent:
			self.msg(_("No parent!"))
			return

		self.tree_cutbuffer.seek(0, 0)
		last_selected = self.gjotsfile.readItem(self.tree_cutbuffer, last_selected, parent)
		self.dirtyflag = "* "
		self.msg(_("Tree items pasted"))

	def _do_external_edit(self):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		first_selected = self.get_first_selected_iter()
		if not first_selected:
			self.msg("Nothing selected")
			return
		self.sync_text_buffer()
		body = self.get_node_value(first_selected)
		if not body:
			return
		scratch = tempfile.mktemp()
		try:
			f = open(scratch, "w")
			f.write(body)
			f.close()
		except IOError:
			self.msg(_("Can't write ") + scratch)
			os.unlink(scratch)
			return

		external_editor = self.client.get_string(self.external_editor_path)
		if external_editor.find("%s") >= 0:
			ext_ed_string = (external_editor % scratch)
		else:
			ext_ed_string = (external_editor + " %s" % scratch)
		if os.system(ext_ed_string) != 0:
			self.err_msg(_("Can't run '%s'") % ext_ed_string)
			os.unlink(scratch)
			return
		try:
			f = open(scratch, "r")
			newbody = ''.join(f.readlines())
			f.close()
			os.unlink(scratch)
		except:
			self.msg(_("Can't read ") + scratch)
			f.close()
			os.unlink(scratch)
			return
		if newbody != body:
			self.textBuffer.set_text(newbody, len(newbody))
			self.current_dirty = 1
			self.dirtyflag = "* "
			self.msg(_("text changed by external editor"))
		else:
			self.msg(_("text not changed by external editor"))
			
	def msg(self, message):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()
		# print "msg: \"" + message + "\""
		# this optimisation really speeds up typing in the textbuffer - gui.msg("") is called for every keystroke
		message = self.dirtyflag + message
		if message == self.last_message:
			return
		
		self.appbar.pop()
		self.appbar.push(message)
		self.last_message = message

	def err_msg(self, message):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()
		general = general_dialog(self, self.progName + _(": Error"), message, OK)

	def set_readonly(self, readonly, quietly):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()
			
		if readonly:
			self.gjotsfile.unlock_file(self.gjotsfile.filename)
		else:
			failed, pid = self.gjotsfile.lock_file("")
			if failed:
				readonly = 1
				if not quietly:
					self.err_msg(_("Can't lock file %s: already locked by process %d") % (self.gjotsfile.filename, pid))

		self.readonly = readonly

		writeable = not readonly
		if writeable:
			self._enable_tree_paste()
		else:
			self._disable_tree_paste()
		w = self.xml.get_widget("cutButton")
		w.set_sensitive(writeable)
		w = self.xml.get_widget("wrapButton")
		w.set_sensitive(writeable)
		w = self.xml.get_widget("externalEditButton")
		w.set_sensitive(writeable)
		w = self.xml.get_widget("timeStampButton")
		w.set_sensitive(writeable)
		w = self.xml.get_widget("newChildButton")
		w.set_sensitive(writeable)
		w = self.xml.get_widget("newPageButton")
		w.set_sensitive(writeable)
		w = self.xml.get_widget("upButton")
		w.set_sensitive(writeable)
		w = self.xml.get_widget("downButton")
		w.set_sensitive(writeable)
		w = self.xml.get_widget("promoteButton")
		w.set_sensitive(writeable)
		w = self.xml.get_widget("demoteButton")
		w.set_sensitive(writeable)
		w = self.xml.get_widget("saveButton")
		w.set_sensitive(writeable)
		w = self.xml.get_widget("importMenuItem")
		w.set_sensitive(writeable)
		w = self.xml.get_widget("saveMenuItem")
		w.set_sensitive(writeable)
		w = self.xml.get_widget("newPageMenuItem")
		w.set_sensitive(writeable)
		w = self.xml.get_widget("upMenuItem")
		w.set_sensitive(writeable)
		w = self.xml.get_widget("downMenuItem")
		w.set_sensitive(writeable)
		w = self.xml.get_widget("newChildMenuItem")
		w.set_sensitive(writeable)
		w = self.xml.get_widget("promoteMenuItem")
		w.set_sensitive(writeable)
		w = self.xml.get_widget("demoteMenuItem")
		w.set_sensitive(writeable)
		w = self.xml.get_widget("undoMenuItem")
		if self.has_gtksourceview:
			w.set_sensitive(writeable)
		else:
			w.set_sensitive(False)
		w = self.xml.get_widget("redoMenuItem")
		if self.has_gtksourceview:
			w.set_sensitive(writeable)
		else:
			w.set_sensitive(False)
		w = self.xml.get_widget("undoMenuItem")
		w.set_sensitive(writeable)
		w = self.xml.get_widget("redoMenuItem")
		w.set_sensitive(writeable)
		w = self.xml.get_widget("cutMenuItem")
		w.set_sensitive(writeable)
		w = self.xml.get_widget("pasteMenuItem")
		w.set_sensitive(writeable)
		w = self.xml.get_widget("formatMenuItem")
		w.set_sensitive(writeable)
		w = self.xml.get_widget("externalEditMenuItem")
		w.set_sensitive(writeable)
		w = self.xml.get_widget("timeStampMenuItem")
		w.set_sensitive(writeable)
		w = self.xml.get_widget("splitItemButton")
		w.set_sensitive(writeable)
		w = self.xml.get_widget("mergeItemsButton")
		w.set_sensitive(writeable)
		w = self.xml.get_widget("sortButton")
		w.set_sensitive(writeable)
		w = self.xml.get_widget("splitItemMenuItem")
		w.set_sensitive(writeable)
		w = self.xml.get_widget("mergeItemsMenuItem")
		w.set_sensitive(writeable)
		w = self.xml.get_widget("sortTreeMenuItem")
		w.set_sensitive(writeable)
		w = self.xml.get_widget("sortTextMenuItem")
		w.set_sensitive(writeable)
		self.textView.set_editable(writeable)
		self.xml.get_widget("cutContextMenuItem").set_sensitive(writeable)
		self.xml.get_widget("pasteContextMenuItem").set_sensitive(writeable)
		self.xml.get_widget("newPageContextMenuItem").set_sensitive(writeable)
		self.xml.get_widget("newChildContextMenuItem").set_sensitive(writeable)
		self.xml.get_widget("upContextMenuItem").set_sensitive(writeable)
		self.xml.get_widget("downContextMenuItem").set_sensitive(writeable)
		self.xml.get_widget("promoteContextMenuItem").set_sensitive(writeable)
		self.xml.get_widget("demoteContextMenuItem").set_sensitive(writeable)
		self.xml.get_widget("mergeItemsContextMenuItem").set_sensitive(writeable)
		self.xml.get_widget("sortTreeContextMenuItem").set_sensitive(writeable)

		# Need to disconnect temporarily to prevent looping:
		self.readOnly_widget.disconnect(self.readOnly_handler)
		self.readOnly_widget.set_active(not writeable)
		self.readOnly_handler = self.readOnly_widget.connect("activate", self.on_readOnly_trigger)

	def _enable_tree_paste(self):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		w = self.xml.get_widget("pasteButton")
		w.set_sensitive(1)

	def _disable_tree_paste(self):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		w = self.xml.get_widget("pasteButton")
		w.set_sensitive(0)

	def _save_if_dirty(self):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		if self.trace:
			print "_save_if_dirty"
		if self.dirtyflag:
			general = general_dialog(self, self.progName + _(": Save?"),
									 _("Save current work?"), YES|NO|CANCEL,
									 0, 0, "",
									 "", "",
									 "",  "")
			if general.get_value() == CANCEL:
				return CANCEL
			if general.get_value() == YES:
				if self.gjotsfile.write_file(prompt="", exporting=0):
					self.dirtyflag = ""
		return OK

# File menu callbacks:
	def on_new_trigger(self, widget):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.sync_text_buffer()
		if self._save_if_dirty() == CANCEL:
			return

		self._create_empty_tree()
		self.dirtyflag = ""
		self.msg(_("New file"))
		
	def on_open_trigger(self, widget):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self._do_open()

	def _do_open(self):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		self.sync_text_buffer()
		if self._save_if_dirty() == CANCEL:
			return
		self.gjotsfile.close() # does python have a destructor mechanism?
		self.gjotsfile = gjotsfile(self)
		if self.gjotsfile.read_file(_("Open file ..."), None, self.readonly, import_after=None):
			self.dirtyflag = ""

	def _do_save(self):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		self.sync_text_buffer()
		if not self.dirtyflag:
			self.msg(_("No changes to save"))
			return
		if self.gjotsfile.write_file(prompt="", exporting=0):
			self.dirtyflag = ""
			self.msg(_("Saved."))
		else:
			self.msg(_("Not saved."))
		return

	def on_save_trigger(self, widget):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self._do_save()

	def on_saveAs_trigger(self, widget):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		self.sync_text_buffer()
		if not self.gjotsfile:
			self.msg(_("Nothing to save"))
			return
		if self.gjotsfile.write_file(_("Save as ..."), exporting=0):
			self.dirtyflag = ""
			self.msg(_("Saved."))
		else:
			self.msg(_("Not saved."))
		return

	def on_import_trigger(self, widget):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.sync_text_buffer()
		self.msg("")
		import_after = self.get_last_selected_iter()
		if import_after:
			if self.gjotsfile.read_file(_("Import from ..."), None, 1, import_after):
				self.dirtyflag = "* "
		else:
			self.msg(_("Nothing selected"))
		return

	def on_export_trigger(self, widget):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.sync_text_buffer()
		self.msg("")
		self.gjotsfile.write_file(_("Export to ..."), exporting=1)
		return

	def on_print_trigger(self, widget):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		# TODO: Which line is the right one???
		#print_dialog(self)
		print_d = print_dialog(self)

	def on_readOnly_trigger(self, widget):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		self.set_readonly(self.readOnly_widget.get_active(), quietly=0)
		return

	def on_quit_trigger(self, widget):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		self.sync_text_buffer()
		if self._save_if_dirty() == CANCEL:
			return gtk.TRUE
		self.gjotsfile.close()
		# Save the paned widget position
		self.client.set_int(self.pane_position_path, self.xml.get_widget("treeTextPane").get_position())
		gtk.main_quit()

	def delete_event(self, widget, event, data=None):
		"""
		Delete event signal sent by closing the gjots window through the
		window manager. This takes a different number of arguments than the
		quit signal emitted by a menu or button, so this method simply wraps
		the main 'on_quit_trigger'.
		"""
		return self.on_quit_trigger(widget)

# Edit menu callbacks:
	def on_undo_trigger(self, widget):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		if self.textView.is_focus():
			self.textBuffer.undo()

	def on_redo_trigger(self, widget):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		if self.textView.is_focus():
			self.textBuffer.redo()

	def on_cut_trigger(self, widget):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		self.sync_text_buffer()
		if self.textView.is_focus():
			self._do_text_cut()
		elif self.treeView.is_focus():
			self._do_tree_cut()

	def on_copy_trigger(self, widget):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		self.sync_text_buffer()
		if self.textView.is_focus():
			self._do_text_copy()
		elif self.treeView.is_focus():
			self._do_tree_copy()

	def on_paste_trigger(self, widget):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		if self.textView.is_focus():
			self._do_text_paste()
		elif self.treeView.is_focus():
			self._do_tree_paste()

	def on_selectAll_trigger(self, widget):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		if self.textView.is_focus():
			self._do_text_select_all()
		elif self.treeView.is_focus():
			self._do_tree_select_all()

	def on_find_trigger(self, widget):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		find = find_dialog(self)

	# FIXME: This is the same as 'on_find_trigger()'
	def on_findAgain_trigger(self, widget):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		find = find_dialog(self)

# View menu callbacks:
	def on_topToolbarCheck_trigger(self, widget):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		w = self.xml.get_widget("topToolbarCheckMenuItem")
		if w:
			value = w.get_active()
			self.client.set_bool(self.top_toolbar_path, value)
		return

	def on_treeToolbarCheck_trigger(self, widget):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		w = self.xml.get_widget("treeToolbarCheckMenuItem")
		if w:
			value = w.get_active()
			self.client.set_bool(self.side_toolbar_path, value)
		return

	def on_showIconText_trigger(self, widget):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		w = self.xml.get_widget("showIconTextCheckMenuItem")
		if w:
			value = w.get_active()
			self.client.set_bool(self.show_icon_text_path, value)
		return

	def on_statusBarMenuItem_trigger(self, widget):
		self.msg("")
		self.client.set_bool(self.status_bar_path,
				self.xml.get_widget("statusBarMenuItem").get_active())
		return

	def on_showAll_trigger(self, widget):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		self._do_show_all()

	def on_hideAll_trigger(self, widget):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		self._do_hide_all()

# Tree menu callbacks:
	def on_newPage_trigger(self, widget):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		self._do_new_page()

	def on_newChild_trigger(self, widget):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		self._do_new_child()

	def on_up_trigger(self, widget):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		self._do_move_up()

	def on_down_trigger(self, widget):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		self._do_move_down()

	def on_promote_trigger(self, widget):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		self._do_move_left()

	def on_demote_trigger(self, widget):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		self._do_move_right()

	def on_splitItem_trigger(self, widget):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("on_splitItem_trigger")
		self._do_split_item()

	def on_mergeItems_trigger(self, widget):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		self._do_merge_items()

	def on_sort_trigger(self, widget):
		"""
		This is a generic trigger that will auto-detect whether the text
		view or the tree view is focused, and it will call the more specific
		handler to open a sort dialog for the detected context.
		"""
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		if self.xml.get_widget("textView").is_focus():
			self.on_sortText_trigger(widget)
		elif self.xml.get_widget("treeView").is_focus():
			self.on_sortTree_trigger(widget)

	def on_sortTree_trigger(self, widget):
		self.msg("")
		sort_dialog(self, "tree")

	def on_sortText_trigger(self, widget):
		self.msg("")
		sort_dialog(self, "text")

# Text menu callbacks:
	def on_format_trigger(self, widget):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		self.do_format_paragraph()

	def on_timeStamp_trigger(self, widget):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		self.do_time_stamp()

	def on_externalEdit_trigger(self, widget):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		self._do_external_edit()
		return

# Settings menu callbacks:
	def on_prefs_trigger(self, widget):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		prefs = prefs_dialog(self)

# Help menu callbacks:
	def on_readManual_trigger(self, widget):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		# Check to see if we are running from the tarball, cvs, or system.
		# Determine the gjots2 binary path.
		if os.access("./gjots2", os.R_OK | os.X_OK):
			gjots_cmd = "./gjots2 -r "
		elif os.access("./bin/gjots2", os.R_OK | os.X_OK):
			gjots_cmd = "./bin/gjots2 -r "
		else:  # run from system share directory
			gjots_cmd = "gjots2 -r "

		# Determine the path for the gjots2.gjots documentation file to
		# open.
		gjots_file = ""
		if os.access("./gjots2.gjots", os.R_OK):
			gjots_file = "./gjots2.gjots"
			sys.stderr.write(_("%s: Warning: opening gjots2 manual from %s\n") % ("gjots2", gjots_file))
		elif os.access("./doc/gjots2.gjots", os.R_OK):
			gjots_file = "./doc/gjots2.gjots"
			sys.stderr.write(_("%s: Warning: opening gjots2 manual from %s\n") % ("gjots2", gjots_file))
		else:  # run from the system share directory - try to find a locale version:
			gjots_file_base = self.prefix + "/share/doc/gjots2-" + gjots_version + "/gjots2"
			for env in "LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG":
				locale_lang = ""
				try:
					locale = os.environ[env]
					locale_lang = locale[0:2]
					gjots_file = gjots_file_base + "." + locale + ".gjots"
					if os.access(gjots_file, os.R_OK):
						break
					else:
						gjots_file=""
				except KeyError:
					gjots_file=""
					pass
				try:
					gjots_file = gjots_file_base + "." + locale_lang + ".gjots"
					if os.access(gjots_file, os.R_OK):
						break
					else:
						gjots_file=""
				except KeyError:
					gjots_file=""
					pass
				
			if gjots_file == "":
				gjots_file = gjots_file_base + ".gjots"

		# Execute gjots to open its documentation.
		if os.access(gjots_file, os.R_OK):
			gjots_cmd += gjots_file + "&"
			os.system(gjots_cmd)
		return

	def on_about_trigger(self, widget):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")
		about = gtk.glade.XML(self.gui_filename, "about", domain="gjots2")
		w = about.get_widget("about")
		w.set_property('name', 'Gjots2')
		w.set_property('version', gjots_version)

# Text display callbacks:
	def on_textView_key_press_event(self, widget, key_event):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
			print "keyval=", key_event.keyval
			print "state=", key_event.state
		self.msg("")
		if key_event.keyval == gtk.keysyms.F12:
			self.treeView.grab_focus()
			return 1
		return 0 # allow further signal propagation

	def _get_browser(self):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		if self.browser:
			return self.browser
		browser_list = [ "firefox", "konqueror", "epiphany", "opera", "dillo", None ]
		browser = os.getenv("BROWSER")
		if not browser:
			# see if there's one already running:
			for browser in browser_list:
				if browser and os.system("ps -ef |grep " + browser + " | grep -v grep >/dev/null 2>&1") == 0:
					break
		if not browser:
			# see if there's an executable one:
			for browser in browser_list:
				if browser and os.system("type " + browser + " >/dev/null 2>&1") == 0:
					break
		self.browser = browser
		return browser
	
	def _run_browser_on(self, url):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		browser = self._get_browser()
		if browser:
			os.system(browser + " '" + url + "' &")
		else:
			self.msg("Can't run a browser")
		return 0
		
	def on_textView_button_press_event(self, widget, key_event):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
			print "keyval=", key_event.keyval
			print "state=", key_event.state
		if key_event.type == gtk.gdk._2BUTTON_PRESS:
			cursor_mark = self.textBuffer.get_insert()
			start_iter = self._start_of_url()
			end_iter = self._end_of_url()
			word = self.textBuffer.get_text(start_iter, end_iter)
			# print ("word=\"%s\"\n" % word)
			matchobj = re.compile("^https*://").search(word)
			if matchobj:
				self.textBuffer.select_range(end_iter, start_iter)
					
				self._run_browser_on(word)
				return 1
		return 0 # allow further signal propagation

	# button_press is not caught here
	def on_textView_button_release_event(self, widget, event):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")

	def on_textView_move_cursor(self, widget, event, x, y):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.msg("")

	def same_iter(self, treeiter1, treeiter2):
		"Check if 2 iterators point to the same item"
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		if treeiter1 == None or treeiter2 == None:
			return 1
		return self.treestore.get_path(treeiter1) == self.treestore.get_path(treeiter2)

	def _check_title(self, treeiter, body):
		"""
		Make sure the title and the first line of the text are in sync. But don't change the root title - it is the filename.
		"""
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		if self.same_iter(treeiter, self.get_root()):
			return
		eol = body.find("\n")
		if eol >= 0:
			title = body[0:eol]
		else:
			title = body
		#old_title = self.get_node_value(treeiter)
		#if not title == old_title
		self.treestore.set_value(treeiter, 0, title)

	def _foreach_findfirst(self, model, path, iter, self2):
		if self.first_selected == None:
			self.first_selected = iter
			
	def get_first_selected_iter(self):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.first_selected = None
		selection = self.treeView.get_selection()
		if not selection: return None
		selection.selected_foreach(self._foreach_findfirst, self)
		return self.first_selected

	def get_cursor_iter(self):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		path, column = self.treeView.get_cursor()
		print "get_cursor_iter: path = ", path
		if not path: return None
		return self.treestore.get_iter(path)

	def _foreach_findlast(self, model, path, iter, self2):
		self.last_selected = iter
			
	def get_last_selected_iter(self):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.last_selected = None
		self.treeView.get_selection().selected_foreach(self._foreach_findlast, self)
		return self.last_selected
	
	def on_textBuffer_changed(self, widget):
		"""
		If temp flag is set on this item then erase all the text except for the new stuff
		"""
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.dirtyflag = "* "
		self.msg("")
		self.current_dirty = 1
		if not self.current_item:
			return

		body = self.textBuffer.get_text(self.textBuffer.get_start_iter(), self.textBuffer.get_end_iter(), 0)
		
		temp_flag = self.treestore.get_value(self.current_item, 2)
		if temp_flag:
			# body = [left]New...[right]
			temp_text_pos = body.find(self.temp_text)
			if temp_text_pos >= 0:
				if temp_text_pos > 0:
					left = body[0:temp_text_pos]
				else:
					left = ""
				right = body[temp_text_pos + len(self.temp_text):]
				body = left + right
			self.treestore.set_value(self.current_item, 2, 0) # temp_flag

			if self.textBuffer_changed_handler:
				self.textBuffer.disconnect(self.textBuffer_changed_handler)
			self.textBuffer.set_text(body, len(body))
			self.textBuffer_changed_handler = self.textBuffer.connect("changed", self.on_textBuffer_changed)

			self.treestore.set_value(self.current_item, 1, body)
		self._check_title(self.current_item, body)

	def sync_text_buffer(self):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		if self.current_item and self.current_dirty:
			if self.trace:
				print "sync_text_buffer: syncing dirty data"
			body = self.textBuffer.get_text(self.textBuffer.get_start_iter(), self.textBuffer.get_end_iter(), 0)
			self.treestore.set_value(self.current_item, 1, body)
			self.current_dirty = 0
		
	def on_tree_selection_changed(self, widget):
		"""
		Save off any changes.
		Always display the first one selected
		Always put the cursor at the start of text.
		Check that selection is legal - ie all are siblings of first_selected
		"""
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
			print "widget =", widget
			print "rows =", self.treeView.get_selection().count_selected_rows()
		self.msg("")
		self.sync_text_buffer()
			
		treeiter = self.get_first_selected_iter()
			
		if treeiter:
			if self.trace:
				print "Title =", self.treestore.get_value(treeiter, 0)
			text = self.treestore.get_value(treeiter, 1)
			if self.textBuffer_changed_handler:
				self.textBuffer.disconnect(self.textBuffer_changed_handler)
			self.textBuffer.set_text(text, len(text))
			self.textBuffer_changed_handler = self.textBuffer.connect("changed", self.on_textBuffer_changed)
			
			# Now enforce the rule that all other selected items must be siblings:
			# NB with 2 items selected, selection_list is:
			# (<gtk.TreeStore object (GtkTreeStore) at 0x404f14b4>, [(0, 1), (0, 2)])
			first_selected = self.get_first_selected_iter()
			if not first_selected: return
			selection = self.treeView.get_selection()
			try:
				selection_list = selection.get_selected_rows()
			except AttributeError:
				self.err_msg(_("pygtk-2.2 is required for this application!"))
				gtk.main_quit()
				return
			# Bug fix to check for a null selection list to prevent GTK from
			# segfaulting.
			if selection_list == None or selection_list[1] == None:
				print _("gjots2: warning: selection list is NULL. Skipping tree selection changed \nevent.")
				return
			path_list = selection_list[1]
			parent = self.treestore.iter_parent(first_selected)
			for path in path_list:
				iter = self.treestore.get_iter(path)
				iter_parent = self.treestore.iter_parent(iter)
				if not self.same_iter(iter_parent, parent):
					selection.unselect_iter(iter)
			self.current_item = treeiter
			self.current_dirty = 0

		# Now put the cursor into the right place
		#self.textView.grab_focus()
		#startIter = self.textBuffer.get_start_iter()
		#self.textBuffer.place_cursor(startIter)

	def on_tree_drag_drop(self, widget, drag_context, x, y, time):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()
		self.dirtyflag = "* "
		return

	def _warp(self, iter):
		"""

		Make iter the only selected row and the cursor. Also scroll so
		that it's visible. For some reason the scrolling is not
		working whether or not we set use_align.

		Maybe we should also expand iter's parent ...?
		
		"""
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()
		if not iter:
			return
		path = self.treestore.get_path(iter)
		selection = self.treeView.get_selection()
		selection.unselect_all()
		selection.select_path(path)
		self.treeView.set_cursor(path, None, 0)
		self.treeView.scroll_to_cell(path, None, 1, 0.5, 0.5)
		
	def _do_goto_first_sibling(self):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()

		first_selected = self.get_first_selected_iter()
		if not first_selected:
			self.msg(_("Nothing selected"))
			return
		parent = self.treestore.iter_parent(first_selected)
		if not parent:
			self.msg(_("No parent!"))
			return
		iter = self.treestore.iter_children(parent)
		if iter == None or self.same_iter(iter, first_selected):
			self.msg(_("Can't go further"))
			return None

		self._warp(iter)

	def _do_goto_last_sibling(self):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()

		last_selected = self.get_last_selected_iter()
		if not last_selected:
			self.msg(_("Nothing selected"))
			return

		iter = last_selected
		while iter:
			next = iter
			next = self.treestore.iter_next(next)
			if not next:
				self._warp(iter)
				return
			iter = next
			
	def _do_goto_root(self):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()

		iter = self.treestore.get_iter_first()
		if not iter:
			self.msg(_("Tree is empty!"))
			return
		
		self._warp(iter)

	def _do_goto_last_visible(self):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()

		last_selected = self.get_last_selected_iter()
		if not last_selected:
			self.msg(_("Nothing selected"))
			return

		iter = last_selected
		while 1:
			next = iter
			next = self.treestore.iter_next(next)
			if not next:
				if self.treestore.iter_children(iter):
					path = self.treestore.get_path(iter)
					if self.treeView.row_expanded(path):
						iter = self.treestore.iter_children(iter)
						continue
				self._warp(iter)
				return
			iter = next

	def _do_toggle_expand(self):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()

		iter = self.current_item
		if not iter:
			self.msg(_("Nothing selected"))
			return
		path = self.treestore.get_path(iter)
		if self.treeView.row_expanded(path):
			self.treeView.collapse_row(path)
		else:
			self.treeView.expand_row(path, 0)
			
	def on_tree_key_press_event(self, widget, key_event):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()
			print "key_event.keyval=", key_event.keyval
			print "key_event.state=", key_event.state

		modifier =  key_event.state & gtk.gdk.MODIFIER_MASK
		if modifier == gtk.gdk.CONTROL_MASK:
			if key_event.keyval == gtk.keysyms.Up:
				self._do_move_up()
				return 1
			if key_event.keyval == gtk.keysyms.Down:
				self._do_move_down()
				return 1
			if key_event.keyval == gtk.keysyms.Left:
				self._do_move_left()
				return 1
			if key_event.keyval == gtk.keysyms.Right:
				self._do_move_right()
				return 1
			if key_event.keyval == gtk.keysyms.Home:
				self._do_goto_root()
				return 1
			if key_event.keyval == gtk.keysyms.End:
				self._do_goto_last_visible()
				return 1

			# hmmm - these never get a chance because of the 'global' accelerators:
			if key_event.keyval == gtk.keysyms.X:
				self._do_tree_cut()
				return 1
			if key_event.keyval == gtk.keysyms.C:
				self._do_tree_cut()
				return 1
			if key_event.keyval == gtk.keysyms.V:
				self._do_tree_paste()
				return 1
		elif modifier == 0: # plain keys
			if key_event.keyval == gtk.keysyms.Home:
				self._do_goto_first_sibling()
				return 1
			if key_event.keyval == gtk.keysyms.End:
				self._do_goto_last_sibling()
				return 1
			if key_event.keyval == gtk.keysyms.F12:
				self.textView.grab_focus()
				return 1
			if key_event.keyval == gtk.keysyms.Return or key_event.keyval == gtk.keysyms.KP_Enter:
				self._do_toggle_expand()
				return 1
		return 0 # allow further signal propagation
			
	def on_tree_button_press_event(self, treeview, event):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()
			print "event.button=", event.button
			print "event.state=", event.state
		# event.button 1 left-click
		# event.button 2 middle-click
		# event.button 3 right-click
		# Need to popup menu on right-click -  also on Shift-F10 apparently
		if event.button == 3:
			x = int(event.x)
			y = int(event.y)
			time = event.time
			pthinfo = treeview.get_path_at_pos(x, y)
			if pthinfo != None:
				path, col, cellx, celly = pthinfo
				# If $path is not in current selection. De-select current
				# selection and select $path, which is what the user just
				# right-clicked on.
				selection = treeview.get_selection()
				model, selected = selection.get_selected_rows()
				for row in selected:
					if row == path:
						treeview.grab_focus()
						self.xml.get_widget("treeContextMenu").popup(None, None, None, event.button, time)
						return 1
				# If we get here, then we need to de-select the current
				# selection and select the path that has been right-clicked.
				selection.unselect_all()
				selection.select_path(path)
				treeview.grab_focus()
				self.xml.get_widget("treeContextMenu").popup(None, None, None, event.button, time)
			return 1
		return 0 # allow further signal propagation

	def on_gjots_configure_event(self, arg2, arg3):
		if self.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		if not self.has_set_size:
			self.has_set_size = 1
			width = height = 0
			if self.geometry and len(self.geometry) > 0:
				m = re.match(r"(\d+)x(\d+)", self.geometry)
				if m and m.group:
					width = long(m.group(1))
					height = long(m.group(2))
				else:
					sys.stderr.write(_("%s: bad geometry specification: %s\n") % (self.progName, self.geometry))
					sys.exit(1)
				self.geometry = ""
			if height == 0 and width == 0 and self.client:
				width = self.client.get_int(self.width_path)
				height = self.client.get_int(self.height_path)
			if height > 0 and width > 0:
				#print width, height
				self.gjots.resize(width, height)
		else:
			width, height = self.gjots.get_size()
			self.client.set_int(self.width_path, width)
			self.client.set_int(self.height_path, height)
		return
	
	def _init_icons(self):
		"""
		Registers all of the required images as stock items for easy use
		within the gjots2 glade file.
		"""
		for stock_name, file in self.icons.iteritems():
			factory = gtk.IconFactory()
			pixbuf = gtk.gdk.pixbuf_new_from_file(file)
			iconset = gtk.IconSet(pixbuf)
			factory.add(stock_name, iconset)
			factory.add_default()

	def __init__(self, prefix, progName, geometry, filename, readonly, debug, purge_password):
		"""
		In this init we are going to display the main
		gjots window
		"""

		if debug:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()
			self.trace = 1
			#sys.settrace(self.tracefunc)
		else:
			self.trace = 0

		self.purge_password = purge_password
			
		callbacks = {
			# Main window:
			"on_gjots_configure_event":     self.on_gjots_configure_event,
			
			# File menu:
			"on_new_trigger":               self.on_new_trigger,
			"on_open_trigger":              self.on_open_trigger,
			"on_save_trigger":              self.on_save_trigger,
			"on_saveAs_trigger":            self.on_saveAs_trigger,
			"on_import_trigger":            self.on_import_trigger,
			"on_export_trigger":            self.on_export_trigger,
			"on_print_trigger":             self.on_print_trigger,

			# do this one manually:
			# "on_readOnly_trigger":         self.on_readOnly_trigger,
			"on_quit_trigger":              self.on_quit_trigger,

			# Edit menu:
			"on_undo_trigger":              self.on_undo_trigger,
			"on_redo_trigger":              self.on_redo_trigger,
			"on_cut_trigger":               self.on_cut_trigger,
			"on_copy_trigger":              self.on_copy_trigger,
			"on_paste_trigger":             self.on_paste_trigger,
			"on_selectAll_trigger":         self.on_selectAll_trigger,
			"on_find_trigger":              self.on_find_trigger,
			"on_findAgain_trigger":         self.on_findAgain_trigger,
			
			# View menu:
			"on_topToolbarCheck_trigger":   self.on_topToolbarCheck_trigger,
			"on_treeToolbarCheck_trigger":  self.on_treeToolbarCheck_trigger,
			"on_showIconText_trigger":      self.on_showIconText_trigger,
			"on_statusBarMenuItem_trigger": self.on_statusBarMenuItem_trigger,
			"on_showAll_trigger":           self.on_showAll_trigger,
			"on_hideAll_trigger":           self.on_hideAll_trigger,

			# Tree menu:
			"on_newPage_trigger":           self.on_newPage_trigger,
			"on_newChild_trigger":          self.on_newChild_trigger,
			"on_up_trigger":                self.on_up_trigger,
			"on_down_trigger":              self.on_down_trigger,
			"on_promote_trigger":           self.on_promote_trigger,
			"on_demote_trigger":            self.on_demote_trigger,
			"on_splitItem_trigger":         self.on_splitItem_trigger,
			"on_mergeItems_trigger":        self.on_mergeItems_trigger,
			"on_sortTree_trigger":          self.on_sortTree_trigger,

			# Text menu:
			"on_format_trigger":            self.on_format_trigger,
			"on_timeStamp_trigger":         self.on_timeStamp_trigger,
			"on_externalEdit_trigger":      self.on_externalEdit_trigger,
			"on_sortText_trigger":          self.on_sortText_trigger,
			
			# Setting menu:
			"on_prefs_trigger":             self.on_prefs_trigger,

			# Help menu:
			"on_readManual_trigger":        self.on_readManual_trigger,
			"on_about_trigger":             self.on_about_trigger,

			# Special, context-sensitive triggers:
			"on_sort_trigger":              self.on_sort_trigger,

			# text display callbacks:
			"on_textView_key_press_event":  self.on_textView_key_press_event,
			"on_textView_button_release_event": self.on_textView_button_release_event,
			"on_textView_button_press_event": self.on_textView_button_press_event,
			"on_textView_move_cursor":					self.on_textView_move_cursor,

			# tree callbacks
			"on_tree_selection_changed":    self.on_tree_selection_changed,
			"on_tree_drag_drop":            self.on_tree_drag_drop,
			"on_tree_key_press_event":      self.on_tree_key_press_event,
			"on_tree_button_press_event":   self.on_tree_button_press_event,
		}

		# create widget tree ...
		self.has_set_size = 0
		self.progName = progName
		self.geometry = geometry
		
		gladefile = "gjots.glade3"
		self.gui_filename = gladefile
		self.password = ""
		
		self.prefix = prefix
		
		# Try ./ first (if one local development file exists, then assume
		# all others exists) - developer's version, else goto site-packages.
		self.gui_filename = "./" + gladefile
		# Format is 'stock-name':'file-name'
		self.icons = { 'gjots2-new-page':'./gjots2-new-page.png',
		               'gjots2-new-child':'./gjots2-new-child.png',
		               'gjots2-merge-items':'./gjots2-merge-items.png',
		               'gjots2-split-item':'./gjots2-split-item.png',
		               'gjots2-hide-all':'./gjots2-hide-all.png',
		               'gjots2-show-all':'./gjots2-show-all.png', }
		# Perform more developer checks. If running from CVS or local
		# tarball, then register local icons, otherwise look in the system
		# data directory (e.g. /usr/share/gjots2).
		if not os.access(self.gui_filename, os.F_OK):
			datadir = prefix + "/share/gjots2/"
			self.gui_filename = datadir + gladefile
			for name, file in self.icons.iteritems():
				self.icons[name] = datadir + self.icons[name]
		if os.access("pixmaps", os.F_OK):
			for name, file in self.icons.iteritems():
				self.icons[name] = "./pixmaps/" + self.icons[name]

		override = {}
		try:
			import gtksourceview
			override["GtkTextView"] = gtksourceview.SourceView
			override["GtkTextBuffer"] = gtksourceview.SourceBuffer
			self.has_gtksourceview = True
		except:
			self.has_gtksourceview = False
			pass
		self.xml = gtk.glade.XML(self.gui_filename, "gjots", "gjots2", override)
		self.xml.signal_autoconnect(callbacks)
		self.treestore = None
		self.gjots = self.xml.get_widget("gjots")

		# Connect the window manager close window event to our callback
		self.gjots.connect("delete_event", self.delete_event)

		self.textView = self.xml.get_widget("textView")
		self.treeView = self.xml.get_widget("treeView")
		self.appbar = self.xml.get_widget("appbar")
		self.treeRightClickMenu = self.xml.get_widget("treeRightClickMenu")
		#self.xmlMenu = gtk.glade.XML(self.gui_filename, "treeRightClickWindow", domain="gjots2")
		self.last_message = ""
		self.appbar.set_default(self.last_message)
		self.dirtyflag = ""
		self._create_empty_tree()
		self.temp_text = _("New...>>>") # must be odd enough to never be in the user's text - problem when documenting gjots itself??
		self.tree_cutbuffer = None
		self.current_item = None

		# this flag is used to reduce overhead on every keystroke - it
		# is set when the textBuffer is out of sync with the current
		# treestore item. It needs to be checked and sync'd
		# (sync_text_buffer()) before the current item is used eg in
		# any save, cut, copy, export and before exit. It is auto
		# sync'd on change of selection. There must be a nicer way to
		# do this with signals ...
		self.current_dirty = 0
		
		try:
			import gtksourceview
			self.textBuffer = gtksourceview.SourceBuffer()
			self.textBuffer.set_text = lambda *args: not not (
				self.textBuffer.begin_not_undoable_action(),
				apply(gtksourceview.SourceBuffer.set_text, [self.textBuffer] + list(args)),
				self.textBuffer.end_not_undoable_action(),
			)
		except:
			self.textBuffer = gtk.TextBuffer()
		self.textView.set_buffer(self.textBuffer)
		self.textBuffer.set_text("", 0)
		self.textBuffer_changed_handler = self.textBuffer.connect("changed", self.on_textBuffer_changed)
		self.on_tree_selection_changed_handler = self.treeView.get_selection().connect("changed", self.on_tree_selection_changed)
		self.readOnly_widget = self.xml.get_widget("readOnlyMenuItem")
		self.readOnly_handler = self.readOnly_widget.connect("activate", self.on_readOnly_trigger)
		self._setup_gconf()
		self.cut_text = None
		self.browser = None
		
		# not working ... any clues? ... anyone? ...
		#icon = gtk.IconSource()
		#icon.set_filename("gjots.png")
		#iconset = gtk.IconSet()
		#iconset.add_source(icon)
		#self.gjots.set_icon_list(iconset)

		# not working ... any clues? ... anyone? ...
		#image = gtk.Image()
		#image.set_from_file("gjots.png")
		#self.gjots.set_icon(image)

		self._init_icons()

		# Hide the right-click tree context menu (stored on the menu bar)
		#self.xml.get_widget("treeContextMenuItem").hide()

		self.display = gtk.gdk.display_manager_get().get_default_display()

		# Init the clipboard to use the system default "CLIPBOARD"
		self.clipboard = gtk.Clipboard(self.display, "CLIPBOARD")
		if not self.clipboard:
			print "No clipboard"
			sys.exit(3)

		self.gjotsfile.read_file("", filename, readonly, import_after=None)

		self._disable_tree_paste()
		root_path = self.treestore.get_path(self.root)
		self.treeView.expand_row(root_path, 0)
		self._warp(self.root)
		#self.treeView.get_selection().select_path(root_path)

		self.msg(progName + _(": version ") + gjots_version)
		self.set_readonly(readonly, quietly=1)

		self.treeView.grab_focus()
		return

# Local variables:
# eval:(setq compile-command "cd ..; ./gjots2 j")
# End:
