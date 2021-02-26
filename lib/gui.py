# -*- coding: utf-8 -*-

import os, sys
import gi
gi.require_version('GtkSource', '3.0')
gi.require_version("Gtk", "3.0")
from gi.repository import GObject, Gio, Gtk, Gdk, GdkPixbuf, GLib
import tempfile
from gi.repository import Pango
import time # for strftime
import pipes
import inspect

from file import *
from prefs import *
from general import *
from common import *
from find import *
from printDialog import *
from sortDialog import *
from version import *

"""

Notes:

Recall that a GtkTreeStore implements GtkTreeModel - so all treemodel
methods apply to treestore

According to file:///usr/share/gtk-doc/html/gtk/GtkTreeModel.html,
tree_row_references are not necessary as "some models guarantee that
an iterator is valid for as long as the node it refers to is valid
(most notably the GtkTreeStore and GtkListStore)."

Note that every selection is constrained to be of siblings only at the
time the selection changes - so we can always make that assumption.

"""

def _insert_primary_callback(clipboard, text, user_data):
    self, x, y = user_data
    if text and not self.readonly:
        result, hit_iter = self.textView.get_iter_at_location(x, y)
        self.textBuffer.place_cursor(hit_iter)
        self.textBuffer.insert_at_cursor(text)
        clipboard.set_text(text, -1)
        self.msg(_("Text pasted"))

def _autosave_alarm_handler(myself):
    if myself.debug: print("autosave alarm!")
    if myself.dirtyflag:
        myself._do_save(reuse_password = 1)
    myself.set_readonly(1, 1)
    myself.autosave_timeout_tag = False
    return False

class gjots_gui:

    def set_autosave_timeout(self):
        if self.autosave_timeout_tag:
            self._cancel_autosave_timeout()
        timeout = self.settings.get_int("auto-save-interval")
        if timeout > 0:
            if self.debug: print("autosave alarm set at %i sec" % timeout)
            self.autosave_timeout_tag = GObject.timeout_add(timeout * 1000, _autosave_alarm_handler, self)

    def _cancel_autosave_timeout(self):
        if self.autosave_timeout_tag:
            GObject.source_remove(self.autosave_timeout_tag)
        self.autosave_timeout_tag = False

    def _set_dirtyflag(self):
        self.dirtyflag = "* "
        self.set_autosave_timeout()

    def _start_of_para(self):
        """
        Para marker is \n\n
        """
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
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
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
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
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
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
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
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
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])

        text_formatter=self.settings.get_string("text-formatter")
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

        para = self.textBuffer.get_text(start_iter, end_iter, False)
        t = pipes.Template()
        if text_formatter.find("%d") >= 0:
            runstring = text_formatter % self.settings.get_int("line-length")
        else:
            runstring = text_formatter
        t.append(runstring, "--")
        scratch = tempfile.NamedTemporaryFile(mode='r+', delete = False)
        f = t.open(scratch.name, "w")
        f.write(para)
        f.close()
        para = open(scratch.name, "r").read()
        os.unlink(scratch.name)
        scratch.close()
        if para and para[-1] == '\n':
            para = para[0:-1]
        if self.debug:
            print(("\"%s\"\n" % para))
        self.textBuffer.place_cursor(start_iter)
        self.textBuffer.delete(start_iter, end_iter)
        self.textBuffer.insert(start_iter, para, len(para))

        # move to next para:
        if start_iter.forward_char():
            start_iter.forward_char()
        self.textBuffer.place_cursor(start_iter)
        return

    def do_time_stamp(self):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        format = self.settings.get_string("date-format")
        newstring = time.strftime(format)
        self.textBuffer.insert_at_cursor(newstring, len(newstring))
        return

    def on_settings_find_text_changed(self, settings, key, label):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
            print("find_text=", list(settings.get_value("find-text")))
        self.update_combobox_from_settings()
        return

    def on_gjots_focus_out_event(self, arg1, arg2):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])

    def on_combobox_changed(self, combobox):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.update_settings_from_combobox()
        return 0

    def on_settings_text_font_changed(self, settings, key, label):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
            print("text_font=", settings.get_string("text-font"))
        font_desc = Pango.FontDescription(settings.get_string("text-font"))
        self.textView.modify_font(font_desc)
        return

    def on_settings_top_toolbar_changed(self, settings, key, label):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        value = settings.get_boolean("top-toolbar")
        w = self.gui_get_widget("topToolbar")
        if w:
            if value:
                w.show()
            else:
                w.hide()

        # how come this doesn't create an infinite loop - doesn't the
        # GtkMenuChecklist item get a notification?
        w = self.gui_get_widget("topToolbarCheckMenuItem")
        if w:
            w.set_active(value)
        return

    def on_settings_side_toolbar_changed(self, settings, key, label):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        value = settings.get_boolean("side-toolbar")
        w = self.gui_get_widget("treeToolbar")
        if w:
            if value:
                w.show()
            else:
                w.hide()

        # how come this doesn't create an infinite loop - doesn't the
        # GtkMenuChecklist item get a notification?
        w = self.gui_get_widget("treeToolbarCheckMenuItem")
        if w:
            w.set_active(value)
        return

    def on_settings_show_icon_text_changed(self, settings, key, label):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        if settings.get_boolean("show-icon-text"):
            self.gui_get_widget("topToolbar").set_style(Gtk.ToolbarStyle.BOTH)
            self.gui_get_widget("treeToolbar").set_style(Gtk.ToolbarStyle.BOTH)
        else:
            self.gui_get_widget("topToolbar").set_style(Gtk.ToolbarStyle.ICONS)
            self.gui_get_widget("treeToolbar").set_style(Gtk.ToolbarStyle.ICONS)

        self.gui_get_widget("showIconTextCheckMenuItem").set_active(self.settings.get_boolean("show-icon-text"))
        return

    def on_settings_status_bar_changed(self, settings, key, label):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        if settings.get_boolean("status-bar"):
            self.gui_get_widget("appbar").show()
        else:
            self.gui_get_widget("appbar").hide()

        self.gui_get_widget("statusBarMenuItem").set_active(settings.get_boolean("status-bar"))
        return

    def on_settings_pane_position_changed(self, settings, key, label):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.gui_get_widget("treeTextPane").set_position(settings.get_int("pane-position"))
        return

    def _initialise_settings(self):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])

        self.settings = Gio.Settings.new("org.gtk.gjots2")

        # handle startup defaults:

        self.update_combobox_from_settings()

        font_desc = Pango.FontDescription(self.settings.get_string("text-font"))
        self.textView.modify_font(font_desc)

        # set this off at startup:
        self.settings.set_boolean("find-backwards", 0)

        self.on_settings_top_toolbar_changed(self.settings, 0, 0)
        self.on_settings_side_toolbar_changed(self.settings, 0, 0)
        self.on_settings_show_icon_text_changed(self.settings, 0, 0)
        self.on_settings_status_bar_changed(self.settings, 0, 0)
        self.on_settings_pane_position_changed(self.settings, 0, 0)

        # setup notifiers:

        self.global_find_index = 0
        return

    def _create_empty_tree(self):
        # create an empty tree:
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.gjotsfile = gjotsfile(self)
        self.flush_tree()
        self.new_node(None, None, self.progName, "")
        self.show_tree()

    def flush_tree(self):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.treestore = Gtk.TreeStore(
            GObject.TYPE_STRING, # title == first line of body except for root, which is filename
            GObject.TYPE_STRING, # body
            GObject.TYPE_INT)    # body_temp_flag - used after creating new items

    def set_title(self, message):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2], vars())
        dirname, basename = os.path.split(self.gjotsfile.filename)
        self.gjots.set_title(self.progName + ": " + basename + ": " + message)

    def show_tree(self):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2], vars())
        # remove the old column, if there:
        column = self.treeView.get_column(0)
        if column:
            self.treeView.remove_column(column)

        self.treeView.set_model(self.treestore)
        renderer = Gtk.CellRendererText()

        column = Gtk.TreeViewColumn(self.progName, renderer, text=0)
        self.column = column
        self.treeView.append_column(column)
        self.set_title("")
        self.treeView.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)
        self.treeView.show()
        return

    def get_node_value(self, treeiter):
        "Get the text value of the node at location 'treeiter'"
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        return self.treestore.get_value(treeiter, 1)

    def get_node_title(self, treeiter):
        "Get the title value of the node at location 'treeiter'"
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        body = self.treestore.get_value(treeiter, 1)
        eol = body.find("\n")
        if eol >= 0:
            title = body[0:eol]
        else:
            title = body
        return title

    def get_first_child(self, treeiter):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        return self.treestore.iter_nth_child(treeiter, 0)

    def get_root(self):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        return self.treestore.get_iter_first()

    def get_next(self, treeiter):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        return self.treestore.iter_next(treeiter)

    def _get_deepest_child(self, iter):
        """
        if current has no children return it. Otherwise recurse down
        the tree and return the last (deepest) child
        """
        while 1:
            num_children = self.treestore.iter_n_children(iter)
            if num_children == 0:
                return iter
            iter = self.treestore.iter_nth_child(iter, num_children - 1)

    def get_linear_prev(self, iter):
        """

        Get the previous tree item - if current has a previous
        sibling, return its last (deepest) child. If no more
        siblings, get the last (deepest) child of the previous sibling
        of the parent.

        """

        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])

        prev = self._iter_prev(iter)
        if prev:
            return self._get_deepest_child(prev)

        while iter:
            iter = self.treestore.iter_parent(iter)
            if not iter:
                return None
            prev = self._iter_prev(iter)
            if prev:
                return self._get_deepest_child(prev)
        return iter

    def get_linear_next(self, iter):
        """

        Get the very next tree item - if current has a child, return
        it. Otherwise, return the next sibling. If no more siblings,
        get the next sibling of the parent recursively.

        """

        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        next = self.treestore.iter_children(iter)
        if next:
            return next

        next = self.treestore.iter_next(iter)
        if next:
            return next

        while iter:
            iter = self.treestore.iter_parent(iter)
            if not iter:
                return None
            next = self.treestore.iter_next(iter)
            if next:
                return next
        return iter

    def new_node(self, parent, sibling, title, body):
        # bit too verbose to trace:
        #if self.debug:
        #   print inspect.getframeinfo(inspect.currentframe())[2], vars()
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
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
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
        self._set_dirtyflag()

    def _do_new_child(self):
        """
        Inserts a new blank item as a child of the last one selected.
        """
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self._set_dirtyflag()
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
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
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
            # we're at the end of this level - see if we can push into
            # the parents prev sibling:
            new_parent = self._iter_prev(parent)
            if not new_parent:
                self.msg(_("Can't go any further"))
                return

            this = first_selected
            new_selection_start = new_selection_end = None
            while this:
                if not self.treeView.get_selection().iter_is_selected(this):
                    break
                next = self.treestore.iter_next(this)
                new_selection_end = self._copy_subtree(self.treestore, this, self.treestore, new_parent, -1)
                if not new_selection_start:
                    new_selection_start = new_selection_end
                self._set_dirtyflag()
                this = next

            # do the removal backwards as there is breakage in gtk3-3.16.7-1.fc22.x86_64:
            this = self.get_last_selected_iter()
            while this:
                if not self.treeView.get_selection().iter_is_selected(this):
                    break
                prev = self._iter_prev(this)
                self.treestore.remove(this)
                self._set_dirtyflag()
                this = prev

            parent_path = self.treestore.get_path(new_parent)
            self.treeView.expand_row(parent_path, 0)

            self._select_range(new_selection_start, new_selection_end)

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
                        self.treestore.move_before(this, pivot) # gtk 2.2+ only
                    this = self.treestore.iter_next(this)
                self._set_dirtyflag()
                return
            this = next

    def _copy_subtree(self, from_treestore, from_iter, to_treestore, to_parent, position, after = False):
        """
        position = 0 means to the start
        position =-1 means to the end
        position = otherwise _before_ that position (or _after_ if 'after' is set)
        """
        title = from_treestore.get_value(from_iter, 0)
        text = from_treestore.get_value(from_iter, 1)
        if (type(position) == type(to_parent)):
            if after:
                new = to_treestore.insert_after(to_parent, position)
            else:
                new = to_treestore.insert_before(to_parent, position)
        else:
            if position == -1:
                position = to_treestore.iter_n_children(to_parent) + 1
            new = to_treestore.insert(to_parent, position)
        to_treestore.set_value(new, 0, title)
        to_treestore.set_value(new, 1, text)
        this = from_treestore.iter_nth_child(from_iter, 0)
        while this:
            self._copy_subtree(from_treestore, this, to_treestore, new, -1)
            this = from_treestore.iter_next(this)
        return new

    def _select_range(self, start, end):
        # temporarily disconnect selection updating as structure is unstable (bug 1250753):
        self.treeView.get_selection().handler_block(self.on_tree_selection_changed_handler)

        self.treeView.get_selection().select_range(self.treestore.get_path(start),
                                                   self.treestore.get_path(end))
        # disabled, so we also need to manually set self.current_item!):
        self.current_item = start
        self.treeView.get_selection().handler_unblock(self.on_tree_selection_changed_handler)
        #self.on_tree_selection_changed_handler = self.treeView.get_selection().connect("changed", self.on_tree_selection_changed)

    def _do_move_down(self):
        """
        Move the current selection after the last's sibling, if any.
        """
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
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
            # we're at the end of this level - see if we can push into
            # the parents next sibling:
            new_parent = self.treestore.iter_next(parent)
            if not new_parent:
                self.msg(_("Can't go any further"))
                return

            this = last_selected
            new_selection_start = new_selection_end = None
            while this:
                prev = self._iter_prev(this)
                if self.same_iter(this, first_selected):
                    prev = None
                new_selection_start = self._copy_subtree(self.treestore, this, self.treestore, new_parent, 0)
                if not new_selection_end:
                    new_selection_end = new_selection_start
                self.treestore.remove(this)
                self._set_dirtyflag()
                this = prev

            parent_path = self.treestore.get_path(new_parent)
            self.treeView.expand_row(parent_path, 0)

            self._select_range(new_selection_start, new_selection_end)

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
                self._set_dirtyflag()
            this = next

    def _do_move_left(self):
        """

        "Promote" - selection becomes a sibling of its parent -
        treestore.move_after() only operates within one level so we
        can't use it here - instead, it looks like we have to write
        all items out to disc and then read them back in at the right
        position. Sigh.

        """
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
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
        # self.treeView.get_selection().disconnect(self.on_tree_selection_changed_handler)
        self.treeView.get_selection().handler_block(self.on_tree_selection_changed_handler)
        f = tempfile.TemporaryFile(mode='r+')
        this = first_selected
        while this:
            next = self.treestore.iter_next(this)
            if self.same_iter(this, last_selected):
                next = None
            self.gjotsfile.writeItem(f, this, 0)
            if not self.treestore.remove(this): # returns false if at end
                next = None
            this = next

        f.flush()
        f.seek(0, 0)
        last_selected = self.gjotsfile.readItem(f, start=parent, parent=grandparent)
        f.close()

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

        #self.on_tree_selection_changed_handler = self.treeView.get_selection().connect("changed", self.on_tree_selection_changed)
        self.treeView.get_selection().handler_unblock(self.on_tree_selection_changed_handler)
        self._set_dirtyflag()

    def _do_move_right(self):
        """

        "Demote" - selected items become children of the previous
        item, if any. treestore.move_after() only operates within one
        level so we can't use it here - instead, it looks like we have
        to write all items out to disc and then read them back in at
        the right position. Sigh.

        """
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])

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
        f = tempfile.TemporaryFile(mode='r+')
        this = first_selected
        # temporarily disconnect selection updating as structure is unstable (bug 1250753):
        #self.treeView.get_selection().disconnect(self.on_tree_selection_changed_handler)
        self.treeView.get_selection().handler_block(self.on_tree_selection_changed_handler)
        while this:
            next = self.treestore.iter_next(this)
            if self.same_iter(this, last_selected):
                next = None
            self.gjotsfile.writeItem(f, this, 0)
            if not self.treestore.remove(this): # returns false if no more items
                next = None
            this = next

        # Now read them into the right place:
        f.flush()
        f.seek(0, 0)

        # what is last item in newParent? Used to compute new selection.
        last_item = None
        num_children = self.treestore.iter_n_children(newParent)
        if num_children > 0:
            last_item = self.treestore.iter_nth_child(newParent, num_children - 1)

        # read into end of newParent
        last_selected = self.gjotsfile.readItem(f, None, newParent)
        f.close()

        # make sure new parent is visible:
        parent_path = self.treestore.get_path(newParent)
        self.treeView.expand_row(parent_path, 0)

        # Now, reselect the items (on_tree_selection_changed is
        # disabled, so we also need to manually set self.current_item!):
        if last_item:
            this = self.treestore.iter_next(last_item)
        else:
            this = self.treestore.iter_children(newParent)

        self.treeView.get_selection().unselect_all()

        self.current_item = None
        while this:
            if not self.current_item: self.current_item = this
            next = self.treestore.iter_next(this)
            if self.same_iter(this, last_selected):
                next = None
            self.treeView.get_selection().select_iter(this)
            this = next

        self.treeView.get_selection().handler_unblock(self.on_tree_selection_changed_handler)
        #self.on_tree_selection_changed_handler = self.treeView.get_selection().connect("changed", self.on_tree_selection_changed)
        self._set_dirtyflag()

    def _new_tree_cutbuffer(self):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        # TODO: How do I enable/disable the paste button for both tree and
        # text operations???
        #self._disable_tree_paste()
        self.tree_cutbuffer = Gtk.TreeStore(
            GObject.TYPE_STRING, # title == first line of body except for root, which is filename
            GObject.TYPE_STRING, # body
            GObject.TYPE_INT)    # body_temp_flag - used after creating new items
        # create a root:
        self.tree_cutbuffer_root = self.tree_cutbuffer.insert(None, 0)

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

        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])

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
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        insert = self.textBuffer.get_iter_at_mark(self.textBuffer.get_insert())
        selection_bound = self.textBuffer.get_iter_at_mark(self.textBuffer.get_selection_bound())
        if insert and selection_bound:
            return (self.textBuffer.get_text(insert, selection_bound, False), insert, selection_bound)
        else:
            return (None, None, None)

    def _do_text_cut(self):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")
        text, insert, select_bound = self.get_selected_text()
        if text and len(text):
            if self.clipboard:
                self.textBuffer.cut_clipboard(self.clipboard, self.textView.get_editable())
                self.msg(_("Text cut"))
        return

    def _do_text_copy(self):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")
        text, insert, select_bound = self.get_selected_text()
        if text and len(text):
            if self.clipboard:
                self.textBuffer.copy_clipboard(self.clipboard)
                self.msg(_("Text copied"))
        return

    def _do_text_paste(self, clipboard):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        if not self.readonly:
            self.msg("")
            if clipboard:
                cursor_mark = self.textBuffer.get_insert()
                insert_iter = self.textBuffer.get_iter_at_mark(cursor_mark)
                self.textBuffer.paste_clipboard(clipboard, insert_iter, self.textView.get_editable())
                self.msg(_("Text pasted"))
        return

    def _do_text_select_all(self):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
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
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
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
        self._set_dirtyflag()
        return

    def _do_merge_items(self):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
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

        self._set_dirtyflag()
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
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")
        if self.current_item:
            self._show_all(self.current_item)
        return

    def _do_hide_all(self):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")
        self.treeView.collapse_all()
        item = self.get_root()
        path = self.treestore.get_path(item)
        self.treeView.expand_row(path, 0)
        return

    def _do_tree_cut(self):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        if self.readonly:
            return

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

        self._new_tree_cutbuffer()
        this = first_selected
        count = 0
        while this:
            count = count + 1
            next = self.treestore.iter_next(this)
            if self.same_iter(this, last_selected):
                next = None
            self._copy_subtree(
                self.treestore, this,
                self.tree_cutbuffer, self.tree_cutbuffer_root,
                -1)
            if not self.treestore.remove(this): # returns false if no more items
                next = None
            this = next
        #self._enable_tree_paste()
        if new_selection:
            self.treeView.get_selection().select_iter(new_selection)
        self._set_dirtyflag()
        self.msg(_("%d tree items cut") % count)

    def _do_tree_copy(self):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")
        first_selected = self.get_first_selected_iter()
        if not first_selected:
            self.msg(_("Nothing selected"))
            return

        last_selected = self.get_last_selected_iter()
        if not last_selected:
            self.msg(_("Nothing selected"))
            return

        self._new_tree_cutbuffer()
        this = first_selected
        count = 0
        while this:
            count = count + 1
            next = self.treestore.iter_next(this)
            if self.same_iter(this, last_selected):
                next = None
            self._copy_subtree(
                self.treestore, this,
                self.tree_cutbuffer, self.tree_cutbuffer_root,
                -1)
            this = next
        #self._enable_tree_paste()
        self.msg(_("%d tree items copied") % count)

    def _do_tree_paste(self):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        if self.readonly:
            return
        self.msg("")
        if not self.tree_cutbuffer:
            self.msg(_("Nothing to paste"))
            return

        insertion_point = self.get_first_selected_iter()
        if not insertion_point:
            self.msg(_("Nothing selected"))
            return

        parent = self.treestore.iter_parent(insertion_point)
        if not parent:
            self.msg(_("No parent!"))
            return

        this = self.tree_cutbuffer.iter_children(self.tree_cutbuffer_root)
        after = False
        while this:
            insertion_point = self._copy_subtree(self.tree_cutbuffer, this,
                                                 self.treestore, parent,
                                                 insertion_point, after)
            this = self.tree_cutbuffer.iter_next(this)
            after = True

        self._set_dirtyflag()
        self.msg(_("Tree items pasted"))

    def _do_external_edit(self):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")
        first_selected = self.get_first_selected_iter()
        if not first_selected:
            self.msg("Nothing selected")
            return
        self.sync_text_buffer()
        body = self.get_node_value(first_selected)
        if not body:
            return

        try:
            f = tempfile.NamedTemporaryFile(mode='r+', delete = False)
            f.write(body)
            scratch = f.name
            f.close()
        except IOError:
            self.msg(_("Can't write tempfile"))
            return

        external_editor = self.settings.get_string("external-editor")
        if external_editor.find("%s") >= 0:
            ext_ed_string = (external_editor % scratch)
        else:
            ext_ed_string = (external_editor + " %s" % scratch)
        if self.debug: print("Running: '%s'" % ( ext_ed_string ))
        import subprocess
        self.msg("Waiting for external editor: '%s'" %( ext_ed_string ))
        self.gjots.set_sensitive(0)
        p = subprocess.Popen(ext_ed_string, shell = True)
        while p.poll() == None:
            Gtk.main_iteration()
        stat = p.returncode
        self.gjots.set_sensitive(1)
        self.gjots.present()

        if stat != 0:
            self.err_msg(_("Can't run '%s'") % ext_ed_string)
            return

        try:
            f = open(scratch, "r")
            newbody = ''.join(f.readlines())
            f.close()
            os.unlink(scratch)
        except:
            self.msg(_("Can't read tempfile " + scratch))
            return
        if newbody != body:
            self.textBuffer.set_text(newbody, len(newbody))
            self.current_dirty = 1
            self._set_dirtyflag()
            self.msg(_("text changed by external editor"))
        else:
            self.msg(_("text not changed by external editor"))

    def msg(self, message):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2], vars())
        # print "msg: \"" + message + "\""
        # this optimisation really speeds up typing in the textbuffer - gui.msg("") is called for every keystroke
        message = self.dirtyflag + message
        if message == self.last_message:
            return

        self.appbar.pop(self.appbar.get_context_id("main"))
        self.appbar.push(self.appbar.get_context_id("main"), message)
        self.set_title(message)
        self.last_message = message

    def err_msg(self, message):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2], vars())
        general = general_dialog(self, self.progName + _(": Error"), message, OK)

    def set_readonly(self, readonly, quietly):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2], vars())

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
        w = self.gui_get_widget("cutButton")
        if writeable:
            w.show()
        else:
            w.hide()
        w = self.gui_get_widget("pasteButton")
        if writeable:
            w.show()
        else:
            w.hide()
        w = self.gui_get_widget("wrapButton")
        if writeable:
            w.show()
        else:
            w.hide()
        w = self.gui_get_widget("externalEditButton")
        if writeable:
            w.show()
        else:
            w.hide()
        w = self.gui_get_widget("timeStampButton")
        if writeable:
            w.show()
        else:
            w.hide()
        w = self.gui_get_widget("newChildButton")
        if writeable:
            w.show()
        else:
            w.hide()
        w = self.gui_get_widget("newPageButton")
        if writeable:
            w.show()
        else:
            w.hide()
        w = self.gui_get_widget("upButton")
        if writeable:
            w.show()
        else:
            w.hide()
        w = self.gui_get_widget("downButton")
        if writeable:
            w.show()
        else:
            w.hide()
        w = self.gui_get_widget("promoteButton")
        if writeable:
            w.show()
        else:
            w.hide()
        w = self.gui_get_widget("demoteButton")
        if writeable:
            w.show()
        else:
            w.hide()
        w = self.gui_get_widget("saveButton")
        if writeable:
            w.show()
        else:
            w.hide()
        w = self.gui_get_widget("sortTreeButton")
        if writeable:
            w.show()
        else:
            w.hide()

        w = self.gui_get_widget("importMenuItem")
        w.set_sensitive(writeable)
        w = self.gui_get_widget("saveMenuItem")
        w.set_sensitive(writeable)
        w = self.gui_get_widget("newPageMenuItem")
        w.set_sensitive(writeable)
        w = self.gui_get_widget("upMenuItem")
        w.set_sensitive(writeable)
        w = self.gui_get_widget("downMenuItem")
        w.set_sensitive(writeable)
        w = self.gui_get_widget("newChildMenuItem")
        w.set_sensitive(writeable)
        w = self.gui_get_widget("promoteMenuItem")
        w.set_sensitive(writeable)
        w = self.gui_get_widget("demoteMenuItem")
        w.set_sensitive(writeable)
        w = self.gui_get_widget("undoMenuItem")
        if self.has_gtksourceview:
            w.set_sensitive(writeable)
        else:
            w.set_sensitive(0)
        w = self.gui_get_widget("redoMenuItem")
        if self.has_gtksourceview:
            w.set_sensitive(writeable)
        else:
            w.set_sensitive(0)
        w = self.gui_get_widget("cutMenuItem")
        w.set_sensitive(writeable)
        w = self.gui_get_widget("pasteMenuItem")
        w.set_sensitive(writeable)
        w = self.gui_get_widget("formatMenuItem")
        w.set_sensitive(writeable)
        w = self.gui_get_widget("externalEditMenuItem")
        w.set_sensitive(writeable)
        w = self.gui_get_widget("timeStampMenuItem")
        w.set_sensitive(writeable)
        w = self.gui_get_widget("splitItemButton")
        if writeable:
            w.show()
        else:
            w.hide()
        w = self.gui_get_widget("mergeItemsButton")
        if writeable:
            w.show()
        else:
            w.hide()
        w = self.gui_get_widget("sortButton")
        if writeable:
            w.show()
        else:
            w.hide()
        w = self.gui_get_widget("splitItemMenuItem")
        if writeable:
            w.show()
        else:
            w.hide()
        w = self.gui_get_widget("mergeItemsMenuItem")
        if writeable:
            w.show()
        else:
            w.hide()
        w = self.gui_get_widget("sortTreeMenuItem")
        if writeable:
            w.show()
        else:
            w.hide()
        w = self.gui_get_widget("sortTextMenuItem")
        if writeable:
            w.show()
        else:
            w.hide()
        self.textView.set_editable(writeable)
        self.gui_get_widget("cutContextMenuItem").set_sensitive(writeable)
        self.gui_get_widget("pasteContextMenuItem").set_sensitive(writeable)
        self.gui_get_widget("newPageContextMenuItem").set_sensitive(writeable)
        self.gui_get_widget("newChildContextMenuItem").set_sensitive(writeable)
        self.gui_get_widget("upContextMenuItem").set_sensitive(writeable)
        self.gui_get_widget("downContextMenuItem").set_sensitive(writeable)
        self.gui_get_widget("promoteContextMenuItem").set_sensitive(writeable)
        self.gui_get_widget("demoteContextMenuItem").set_sensitive(writeable)
        self.gui_get_widget("mergeItemsContextMenuItem").set_sensitive(writeable)
        self.gui_get_widget("sortTreeContextMenuItem").set_sensitive(writeable)
        self.gui_get_widget("importContextMenuItem").set_sensitive(writeable)

        # Need to disconnect temporarily to prevent looping:
        # self.readOnly_widget.disconnect(self.readOnly_handler)
        w = self.gui_get_widget("readOnlyMenuItem")
        if self.on_readOnly_handler: w.handler_block(self.on_readOnly_handler)
        w.set_active(not writeable)
        if self.on_readOnly_handler: w.handler_unblock(self.on_readOnly_handler)
        #self.readOnly_handler = self.readOnly_widget.connect("activate", self.on_readOnly_trigger)

    def _enable_tree_paste(self):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        w = self.gui_get_widget("pasteButton")
        w.set_sensitive(1)

    def _disable_tree_paste(self):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        w = self.gui_get_widget("pasteButton")
        w.set_sensitive(0)

    def _save_if_dirty(self):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        if self.dirtyflag:
            general = general_dialog(self, self.progName + _(": Save?"),
                                     _("Save current work?"), YES|NO|CANCEL,
                                     0, 0, "",
                                     "", "",
                                     "",  "")
            if general.get_value() == CANCEL:
                return CANCEL
            if general.get_value() == OK:
                if self.gjotsfile.write_file(prompt="", exporting=0):
                    self.dirtyflag = ""
        return OK

# File menu callbacks:
    def on_new_trigger(self, widget):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.sync_text_buffer()
        if self._save_if_dirty() == CANCEL:
            return

        self._create_empty_tree()
        self.dirtyflag = ""
        self.msg(_("New file"))

    def on_open_trigger(self, widget):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self._do_open(None)

    def on_recent_trigger(self, widget):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        uri = widget.get_current_item().get_uri()
        # Strip 'file://' from the beginning of the uri
        file_to_open = uri[7:]
        self._do_open(file_to_open)

    def _do_open(self, file_to_open):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")
        self.sync_text_buffer()
        if self._save_if_dirty() == CANCEL:
            return
        self.gjotsfile.close() # does python have a destructor mechanism?
        self.gjotsfile = gjotsfile(self)
        if self.gjotsfile.read_file(_("Open file ..."), file_to_open, self.readonly, import_after=None):
            self.dirtyflag = ""
            self._do_goto_root()
            self._do_tree_selection_changed()

    def _do_save(self, reuse_password = 0):
        self._cancel_autosave_timeout()
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")
        self.sync_text_buffer()
        if not self.dirtyflag:
            self.msg(_("No changes to save"))
            return
        if self.gjotsfile.write_file(prompt="", exporting=0, reuse_password=reuse_password):
            self.dirtyflag = ""
            self.msg(_("Saved."))
        else:
            self.msg(_("Not saved."))
        return

    def on_save_trigger(self, widget):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self._do_save()

    def on_saveAs_trigger(self, widget):
        self._cancel_autosave_timeout()
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
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
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.sync_text_buffer()
        self.msg("")
        import_after = self.get_last_selected_iter()
        if import_after:
            if self.gjotsfile.read_file(_("Import from ..."), None, 1, import_after):
                self._set_dirtyflag()
        else:
            self.msg(_("Nothing selected"))
        return

    def on_export_trigger(self, widget):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.sync_text_buffer()
        self.msg("")
        self.gjotsfile.write_file(_("Export to ..."), exporting=1)
        return

    def on_print_trigger(self, widget):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")
        # TODO: Which line is the right one???
        #print_dialog(self)
        print_d = print_dialog(self)

    def on_readOnly_trigger(self, widget):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")
        w = self.gui_get_widget("readOnlyMenuItem")
        self.set_readonly(w.get_active(), quietly=0)
        return

    def on_quit_trigger(self, widget):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")
        self.sync_text_buffer()
        if self._save_if_dirty() == CANCEL:
            return True
        self._wrangle_geometry()
        self.gjotsfile.close()
        # Save the paned widget position
        self.settings.set_int("pane-position", self.gui_get_widget("treeTextPane").get_position())
        Gtk.main_quit()

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
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")
        if self.textView.is_focus():
            self.textBuffer.undo()

    def on_redo_trigger(self, widget):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")
        if self.textView.is_focus():
            self.textBuffer.redo()

    def on_cut_trigger(self, widget):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        if self.readonly:
            return
        self.msg("")
        self.sync_text_buffer()
        if self.textView.is_focus():
            self._do_text_cut()
        elif self.treeView.is_focus():
            self._do_tree_cut()

    def on_copy_trigger(self, widget):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")
        self.sync_text_buffer()
        if self.textView.is_focus():
            self._do_text_copy()
        elif self.treeView.is_focus():
            self._do_tree_copy()

    def on_paste_trigger(self, widget):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        if self.readonly:
            return
        self.msg("")
        if self.textView.is_focus():
            self._do_text_paste(self.clipboard)
        elif self.treeView.is_focus():
            self._do_tree_paste()

    def on_selectAll_trigger(self, widget):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")
        if self.textView.is_focus():
            self._do_text_select_all()
        elif self.treeView.is_focus():
            self._do_tree_select_all()

    def on_find_trigger(self, widget):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")
        self.find_dialog = find_dialog(self)

    def on_findAgain_trigger(self, widget):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")
        self.settings.set_boolean("find-backwards", 0)
        w = self.gui_get_widget("menubar_find_entry")
        if w:
            w.select_region(0, -1)
            w.grab_focus()

        if self.find_next():
            self.msg("Found")
        else:
            self.msg("Not found")

    def on_findAgainBackwards_trigger(self, widget):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")
        self.settings.set_boolean("find-backwards", 1)
        w = self.gui_get_widget("menubar_find_entry")
        if w:
            w.select_region(0, -1)
            w.grab_focus()
        if self.find_next():
            self.msg("Found")
        else:
            self.msg("Not found")

    def on_menubar_find_entry_icon_press(self, widget, icon_pos, event):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
            print("icon_pos=", icon_pos)
        if icon_pos == Gtk.EntryIconPosition.PRIMARY:
            self.on_findAgainBackwards_trigger(widget)
        else:
            self.on_findAgain_trigger(widget)

    def on_menubar_find_entry_changed(self, widget):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
            print("changed to: " + widget.get_text())
        return 0

    def on_menubar_find_entry_activate(self, widget):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.add_string_to_combobox(widget.get_text(), prepend = True)
        self.update_settings_from_combobox()
        if self.find_next():
            self.msg("Found")
        else:
            self.msg("Not found")

    # View menu callbacks:
    def on_topToolbarCheck_trigger(self, widget):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")
        w = self.gui_get_widget("topToolbarCheckMenuItem")
        if w:
            value = w.get_active()
            self.settings.set_boolean("top-toolbar", value)
        return

    def on_treeToolbarCheck_trigger(self, widget):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")
        w = self.gui_get_widget("treeToolbarCheckMenuItem")
        if w:
            value = w.get_active()
            self.settings.set_boolean("side-toolbar", value)
        return

    def on_showIconText_trigger(self, widget):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")
        w = self.gui_get_widget("showIconTextCheckMenuItem")
        if w:
            value = w.get_active()
            self.settings.set_boolean("show-icon-text", value)
        return

    def on_statusBarMenuItem_trigger(self, widget):
        self.msg("")
        self.settings.set_boolean("status-bar",
                self.gui_get_widget("statusBarMenuItem").get_active())
        return

    def on_showAll_trigger(self, widget):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")
        self._do_show_all()

    def on_hideAll_trigger(self, widget):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")
        self._do_hide_all()

# Tree menu callbacks:
    def on_newPage_trigger(self, widget):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")
        self._do_new_page()

    def on_newChild_trigger(self, widget):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")
        self._do_new_child()

    def on_up_trigger(self, widget):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")
        self._do_move_up()

    def on_down_trigger(self, widget):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")
        self._do_move_down()

    def on_promote_trigger(self, widget):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")
        self._do_move_left()

    def on_demote_trigger(self, widget):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")
        self._do_move_right()

    def on_splitItem_trigger(self, widget):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("on_splitItem_trigger")
        self._do_split_item()

    def on_mergeItems_trigger(self, widget):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")
        self._do_merge_items()

    def on_sort_trigger(self, widget):
        """
        This is a generic trigger that will auto-detect whether the text
        view or the tree view is focused, and it will call the more specific
        handler to open a sort dialog for the detected context.
        """
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")
        if self.gui_get_widget("textView").is_focus():
            self.on_sortText_trigger(widget)
        elif self.gui_get_widget("treeView").is_focus():
            self.on_sortTree_trigger(widget)

    def on_sortTree_trigger(self, widget):
        self.msg("")
        sort_dialog(self, "tree")

    def on_sortText_trigger(self, widget):
        self.msg("")
        sort_dialog(self, "text")

# Text menu callbacks:
    def on_format_trigger(self, widget):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")
        self.do_format_paragraph()

    def on_timeStamp_trigger(self, widget):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")
        self.do_time_stamp()

    def on_externalEdit_trigger(self, widget):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")
        self._do_external_edit()
        return

# Settings menu callbacks:
    def on_prefs_trigger(self, widget):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")
        prefs = prefs_dialog(self)

# Help menu callbacks:
    def on_readManual_trigger(self, widget):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
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
        else:
            # run from the system share directory
            gjots_file_base = self.prefix + "/share/doc/gjots2/gjots2"
            for env in "LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG":
                locale_lang = ""
                try:
                    locale = os.environ[env]
                    locale_lang = locale[0:2]
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
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")
        dlg = Gtk.AboutDialog()
        dlg.set_version(gjots_version)
        dlg.set_name("Gjots2")
        dlg.set_authors(["Bob Hepple", "Gabriel Munoz"])
        dlg.set_copyright("Copyright Bob Hepple 2002-2020")
        dlg.set_website("http://bhepple.freeshell.org/gjots2")
        dlg.set_translator_credits("""Rui Nibau (fr) <rui.nibau@omacronides.com>
Robert Emil Berge (no, nb) <filoktetes@linuxophic.org>
Sergey Bezdenezhnyh (ru) <sib-mail@mtu-net.ru>
Raimondo Giammanco (it) <rongten@member.fsf.org>
Martin Sin (cs) <martin.sin@zshk.cz>
Cecilio Salmeron (es) <s.cecilio@gmail.com>
Aleksa Šušulić (sl) <susulic@gmail.com>
Uwe Steinmann (de) <uwe@steinmann.cx>
Morgan Antonsson (sv) <morgan.antonsson@gmail.com>""")
        def close(w, res):
            #if res == Gtk.ResponseType.CANCEL:
            w.hide()
        dlg.connect("response", close)
        dlg.show()

# Text display callbacks:
    def on_textView_key_press_event(self, widget, key_event):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
            print("keyval=", key_event.keyval)
            print("state=", key_event.get_state())
        self.msg("")
        if key_event.keyval == gi.repository.Gdk.KEY_F12:
            self.treeView.grab_focus()
            return 1
        if key_event.keyval == gi.repository.Gdk.KEY_Page_Up:
            if self.textBuffer.get_iter_at_mark(self.textBuffer.get_insert()).is_start():
                self.sync_text_buffer()
                current_item = self.get_linear_prev(self.current_item)
                if not current_item: return 0
                self.current_item = current_item
                current_tree_path = self.treestore.get_path(self.current_item)
                self.treeView.expand_to_path(current_tree_path)
                self.treeView.get_selection().unselect_all()
                self.treeView.get_selection().select_iter(self.current_item)
                self.treeView.scroll_to_cell(current_tree_path, None, 1,
                                             0.5, 0.5)
                return 1
        if key_event.keyval == gi.repository.Gdk.KEY_Page_Down:
            if self.textBuffer.get_iter_at_mark(self.textBuffer.get_insert()).is_end():
                self.sync_text_buffer()
                current_item = self.get_linear_next(self.current_item)
                if not current_item: return 0
                self.current_item = current_item
                current_tree_path = self.treestore.get_path(self.current_item)
                self.treeView.expand_to_path(current_tree_path)
                self.treeView.get_selection().unselect_all()
                self.treeView.get_selection().select_iter(self.current_item)
                self.treeView.scroll_to_cell(current_tree_path, None, 1,
                                             0.5, 0.5)
                self.textBuffer.place_cursor(self.textBuffer.get_start_iter())
                return 1
        if key_event.keyval == gi.repository.Gdk.KEY_Insert and key_event.get_state() & Gdk.ModifierType.SHIFT_MASK:
           if self.debug: print("Got Shift-Insert")
           self._do_text_paste(self.primary)

        #if key_event.keyval == gi.repository.Gdk.KEY_Insert and key_event.get_state() & Gdk.ModifierType.SHIFT_MASK:
        #   print "Got Shift-Insert"
        #   self._do_text_paste()
        #   widget.signal_emit_by_name("paste-cipboard")

        return 0 # allow further signal propagation

    def backtick(self, command):
        """
        Equivalent of Bourne shell's backtick
        See http://www.python.org/doc/2.5.1/lib/node534.html
        """
        from subprocess import Popen, PIPE
        #print "backtick: command='%s'\n" % command
        value = Popen(["sh", "-c", command], stdout=PIPE).communicate()[0].rstrip()
        #print "returning '%s'\n" % value
        return(value)

    def _get_browser(self):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        if self.browser:
            return self.browser
        browser_list = {
            # reminder: this list's order means nothing:
            # <name of executable>:<what to search for in ps -ef list>
            "firefox4":      "/[x]ulrunner-2/.*firefox-",
            "google-chrome": "[/]chrome ",
            "firefox":       "/[x]ulrunner/",
            "konqueror":     "[k]onqueror",
            "epiphany":      "[e]piphany",
            "opera":         "[o]pera",
            "dillo":         "[d]illo"
            }

        # see if there's one already running for this user:
        for browser in list(browser_list.keys()):
            if browser_list[browser]:
                if os.system("ps -U " + os.getenv("USER") + " -o args | grep -q " + browser_list[browser]) == 0:
                    self.browser = browser
                    if self.debug:
                        print("using a running browser: ", browser)
                        break

        # see if there's something we can use in $BROWSER
        if not self.browser:
            browser = os.getenv("BROWSER")
            if browser and os.system("type " + browser + " >/dev/null 2>&1") == 0:
                self.browser = browser
                if self.debug:
                    print("using the setting from BROWSER: ", browser)

        # see if there's a preferred one in gnome:
        if not self.browser:
            self.browser = self.backtick("xdg-open %s 2>/dev/null").split()[0]
            if self.debug:
                print("using xdg-preferred browser: ", self.browser)

        if not self.browser:
            # see if there's an executable one:
            for browser in list(browser_list.keys()):
                if os.system("type " + browser + " >/dev/null 2>&1") == 0:
                    self.browser = browser
                    if self.debug:
                        print("using executable browser: ", browser)
                    break
        return self.browser

    def _run_browser_on(self, url):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])

        open_list = [ "xdg-open", "gnome-open", "kde-open", "exo-open" ]
        for opener in open_list:
            if os.system("type " + opener + " >/dev/null 2>&1") == 0:
                os.system(opener + " '" + url + "' &")
                return 0

        browser = self._get_browser()
        if browser:
            os.system(browser + " '" + url + "' &")
        else:
            self.msg("Can't run a browser")
        return 0

    def on_textView_button_press_event(self, widget, key_event):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
            print(key_event)

        if key_event.button == 2:
            # "middle button" is paste - but (unlike GtkEntry, emacs,
            # firefox and kde apps like 'kate')
            # GtkTextView/GtkTextBuffer don't move the mark to the
            # location of the paste - also, the PRIMARY is wiped after
            # one use. This sucks majorly - so until they fix it
            # (logged as bug
            # https://bugzilla.gnome.org/show_bug.cgi?id=673760)
            # here's a little hack to place the cursor in the right
            # place and to remember the previous copy:
            x, y = self.textView.window_to_buffer_coords(
                self.textView.get_window_type(
                    self.textView.get_window(Gtk.TextWindowType.TEXT)),
                int(key_event.x),
                int(key_event.y))
            self.primary.request_text(_insert_primary_callback, (self, x, y))
            return 1

        if key_event.type == Gdk.EventType._2BUTTON_PRESS:
            cursor_mark = self.textBuffer.get_insert()
            start_iter = self._start_of_url()
            end_iter = self._end_of_url()
            word = self.textBuffer.get_text(start_iter, end_iter, False)
            # print ("word=\"%s\"\n" % word)
            matchobj = re.compile("^https*://").search(word)
            if matchobj:
                self.textBuffer.select_range(end_iter, start_iter)

                self._run_browser_on(word)
                return 1
        return 0 # allow further signal propagation

    def on_textView_button_release_event(self, widget, key_event):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        return 0 # allow further signal propagation

    def on_textView_move_cursor(self, widget, event, x, y):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.msg("")

    def same_iter(self, treeiter1, treeiter2):
        "Check if 2 iterators point to the same item"
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        if treeiter1 == None and treeiter2 == None:
            return 0
        if treeiter1 == None or treeiter2 == None:
            return 1
        return self.treestore.get_path(treeiter1) == self.treestore.get_path(treeiter2)

    def _check_title(self, treeiter, body):
        """
        Make sure the title and the first line of the text are in
        sync. But don't change the root title - it is the filename.
        """
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
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
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.first_selected = None
        selection = self.treeView.get_selection()
        if not selection: return None
        selection.selected_foreach(self._foreach_findfirst, self)
        return self.first_selected

    def get_cursor_iter(self):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        path, column = self.treeView.get_cursor()
        print("get_cursor_iter: path = ", path)
        if not path: return None
        return self.treestore.get_iter(path)

    def _foreach_findlast(self, model, path, iter, self2):
        self.last_selected = iter

    def get_last_selected_iter(self):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.last_selected = None
        self.treeView.get_selection().selected_foreach(self._foreach_findlast, self)
        return self.last_selected

    def on_textBuffer_changed(self, widget):
        """
        If temp flag is set on this item then erase all the text except for the new stuff
        """
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self._set_dirtyflag()
        self.msg("")
        self.current_dirty = 1
        if not self.current_item:
            return

        body = self.textBuffer.get_text(self.textBuffer.get_start_iter(), self.textBuffer.get_end_iter(), False)

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
                #self.textBuffer.disconnect(self.textBuffer_changed_handler)
                self.textBuffer.handler_block(self.textBuffer_changed_handler)
            self.textBuffer.set_text(body, len(body))
            #self.textBuffer_changed_handler = self.textBuffer.connect("changed", self.on_textBuffer_changed)
            self.textBuffer.handler_unblock(self.textBuffer_changed_handler)
            self.treestore.set_value(self.current_item, 1, body)
        body = self.textBuffer.get_text(self.textBuffer.get_start_iter(), self.textBuffer.get_end_iter(), False)
        self._check_title(self.current_item, body)

    def sync_text_buffer(self):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        if self.current_item and self.current_dirty:
            if self.debug:
                print("sync_text_buffer: syncing dirty data")
            body = self.textBuffer.get_text(self.textBuffer.get_start_iter(), self.textBuffer.get_end_iter(), False)
            self.treestore.set_value(self.current_item, 1, body)
            self.current_dirty = 0

    def on_tree_selection_changed(self, widget):
        """
        Save off any changes.
        Always display the first one selected
        Always put the cursor at the start of text.
        Check that selection is legal - ie all are siblings of first_selected
        """
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
            print("widget =", widget)
            print("rows =", self.treeView.get_selection().count_selected_rows())
        self.treeView.get_selection().handler_block(self.on_tree_selection_changed_handler)
        self._do_tree_selection_changed()
        self.treeView.get_selection().handler_unblock(self.on_tree_selection_changed_handler)

    def _do_tree_selection_changed(self):
        #self.msg("") # zaps startup message! Is it really needed here?
        self.sync_text_buffer()

        treeiter = self.get_first_selected_iter()

        if treeiter and self.treestore:
            if self.debug:
                print("treestore = ", self.treestore)
                print("treeiter = ", treeiter)
                print("Title = ", self.treestore.get_value(treeiter, 0))
            text = self.treestore.get_value(treeiter, 1)
            if self.textBuffer_changed_handler:
                #self.textBuffer.disconnect(self.textBuffer_changed_handler)
                self.textBuffer.handler_block(self.textBuffer_changed_handler)
            self.textBuffer.set_text(text, len(text))
            self.textBuffer.handler_unblock(self.textBuffer_changed_handler)
            #self.textBuffer_changed_handler = self.textBuffer.connect("changed", self.on_textBuffer_changed)

            # Now enforce the rule that all other selected items must be siblings:
            # NB with 2 items selected, selection_list is:
            # (<Gtk.TreeStore object (GtkTreeStore) at 0x404f14b4>, [(0, 1), (0, 2)])
            first_selected = self.get_first_selected_iter()
            if not first_selected: return
            selection = self.treeView.get_selection()
            selection_list = selection.get_selected_rows()
            # Bug fix to check for a null selection list to prevent GTK from
            # segfaulting.
            if selection_list == None or selection_list[1] == None:
                print(_("gjots2: warning: selection list is NULL. Skipping tree selection changed \nevent."))
                return
            path_list = selection_list[1]
            parent = self.treestore.iter_parent(first_selected)
            # unselect any that don't have the same parent:
            for path in path_list:
                iter = self.treestore.get_iter(path)
                if not self.same_iter(first_selected, iter):
                    iter_parent = self.treestore.iter_parent(iter)
                    if parent == None or not self.same_iter(iter_parent, parent):
                        selection.unselect_iter(iter)

            # this doesn't work as expected:
            #if parent == None:
            #    path = self.treestore.get_path(treeiter)
            #    self.treeView.set_cursor(path, None, 0)
            self.current_item = treeiter
            self.current_dirty = 0

        # Now put the cursor into the right place
        #self.textView.grab_focus()
        #startIter = self.textBuffer.get_start_iter()
        #self.textBuffer.place_cursor(startIter)

    def on_tree_drag_drop(self, widget, drag_context, x, y, time):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2], vars())
        path, position = self.treeView.get_dest_row_at_pos(x, y)
        # path = (0, 2) on non-root items and (0,) on the root item
        if len(path) < 2 and position == Gtk.TreeViewDropPosition.BEFORE:
            return 1

        self._set_dirtyflag()
        self.current_item = None
        return

    def _warp(self, iter):
        """

        Make iter the only selected row and the cursor. Also scroll so
        that it's visible. For some reason the scrolling is not
        working whether or not we set use_align.

        Maybe we should also expand iter's parent ...?

        """
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2], vars())
        if not iter:
            return
        path = self.treestore.get_path(iter)
        selection = self.treeView.get_selection()
        selection.unselect_all()
        selection.select_path(path)
        self.treeView.set_cursor(path, None, 0)
        self.treeView.scroll_to_cell(path, None, 1, 0.5, 0.5)

    def _do_goto_first_sibling(self):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2], vars())

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
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2], vars())

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
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2], vars())

        iter = self.treestore.get_iter_first()
        if not iter:
            self.msg(_("Tree is empty!"))
            return

        self._warp(iter)

    def _do_goto_last_visible(self):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2], vars())

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

    def _do_goto_last_absolute(self):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2], vars())

        self._do_show_all()
        self._do_goto_root()
        self._do_goto_last_visible()

    def _do_toggle_expand(self):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2], vars())

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
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2], vars())
            print("key_event.keyval=", key_event.keyval)
            print("key_event.get_state()=", key_event.get_state(), "gi.repository.Gdk.KEY_End=", gi.repository.Gdk.KEY_End)

        modifier =  key_event.get_state() & Gdk.ModifierType.MODIFIER_MASK
        # why is MOD2_MASK being set? It's 'hyper'. Ignore it. Hmmm,
        # this only happens on raita. wassup with that?
        modifier &= ~Gdk.ModifierType.MOD2_MASK
        if modifier & Gdk.ModifierType.CONTROL_MASK:
            if key_event.keyval == gi.repository.Gdk.KEY_Up:
                self._do_move_up()
                return 1
            if key_event.keyval == gi.repository.Gdk.KEY_Down:
                self._do_move_down()
                return 1
            if key_event.keyval == gi.repository.Gdk.KEY_Left:
                self._do_move_left()
                return 1
            if key_event.keyval == gi.repository.Gdk.KEY_Right:
                self._do_move_right()
                return 1
            if key_event.keyval == gi.repository.Gdk.KEY_Home:
                self._do_goto_root()
                return 1
            if key_event.keyval == gi.repository.Gdk.KEY_End:
                self._do_goto_last_absolute()
                return 1
            if key_event.keyval == gi.repository.Gdk.KEY_Page_Down:
                self._do_goto_last_sibling()
                return 1
            if key_event.keyval == gi.repository.Gdk.KEY_Page_Up:
                self._do_goto_first_sibling()
                return 1

            # hmmm - these never get a chance because of the 'global' accelerators:
            if key_event.keyval == gi.repository.Gdk.KEY_X:
                self._do_tree_cut()
                return 1
            if key_event.keyval == gi.repository.Gdk.KEY_C:
                self._do_tree_cut()
                return 1
            if key_event.keyval == gi.repository.Gdk.KEY_V:
                self._do_tree_paste()
                return 1
        elif modifier == 0: # plain keys
            if key_event.keyval == gi.repository.Gdk.KEY_Home:
                self._do_goto_first_sibling()
                return 1
            if key_event.keyval == gi.repository.Gdk.KEY_End:
                self._do_goto_last_sibling()
                return 1
            if key_event.keyval == gi.repository.Gdk.KEY_F12:
                self.textView.grab_focus()
                return 1
            if key_event.keyval == gi.repository.Gdk.KEY_Return or key_event.keyval == gi.repository.Gdk.KEY_KP_Enter:
                self._do_toggle_expand()
                return 1
        return 0 # allow further signal propagation

    def on_tree_button_press_event(self, treeview, event):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2], vars())
            print("event.button=", event.button)
            print("event.get_state()=", event.get_state())
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
                        self.treeContextMenu_get_widget("treeContextMenu").popup(None, None, None, event.button, time)
                        return 1
                # If we get here, then we need to de-select the current
                # selection and select the path that has been right-clicked.
                selection.unselect_all()
                selection.select_path(path)
                treeview.grab_focus()
                self.treeContextMenu_get_widget("treeContextMenu").popup(None, None, None, event.button, time)
            return 1
        return 0 # allow further signal propagation

    def remove_tag(self):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])

        if self.hit_end != -1 and self.hit_start != -1:
            hit_start_iter = self.textBuffer.get_iter_at_offset(
                self.start_offset + self.hit_start)
            hit_end_iter = self.textBuffer.get_iter_at_offset(
                self.start_offset + self.hit_end)
            self.textBuffer.remove_tag(self.found_tag, hit_start_iter,
                                       hit_end_iter)

    def add_string_to_combobox(self, s, prepend):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
            print("s=", s)
        combobox = self.gui_get_widget("menubar_find_combobox");
        if combobox:
            model = combobox.get_model() # liststore
            # see if it's already there
            iter = model.get_iter_first()
            num_items = 0
            while iter:
                if s == model.get_value(iter, 0):
                    # move it to first item
                    model.remove(iter)
                    break
                iter = model.iter_next(iter)
                num_items += 1
            if self.on_combobox_handler: combobox.handler_block(self.on_combobox_handler)
            if prepend:
                model.prepend([s])
            else:
                model.append([s])
            combobox.set_active(0)
            num_items += 1

            while model.iter_n_children(None) > self.combobox_max_lines_to_save:
                # trim them back
                model.remove(model.iter_nth_child(None, self.combobox_max_lines_to_save))
                num_items -= 1
            if self.on_combobox_handler: combobox.handler_unblock(self.on_combobox_handler)

    def update_combobox_from_settings(self):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        combobox = self.gui_get_widget("menubar_find_combobox");
        if combobox:
            model = combobox.get_model() # liststore
            iter = model.get_iter_first()
            if self.on_combobox_handler: combobox.handler_block(self.on_combobox_handler)
            while iter:
                model.remove(iter)
                iter = model.iter_next(iter)
            if self.on_combobox_handler: combobox.handler_unblock(self.on_combobox_handler)
        strings = list(self.settings.get_value("find-text"))
        for s in strings[0:self.combobox_max_lines_to_save]:
            self.add_string_to_combobox(s, prepend = False)

    def update_settings_from_combobox(self):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        combobox = self.gui_get_widget("menubar_find_combobox");
        if combobox:
            model = combobox.get_model() # liststore
            iter = model.get_iter_first()
            s = [ ]
            while iter:
                s += [ model.get_value(iter, 0) ]
                iter = model.iter_next(iter)
            # self.settings.handler_block(self.on_settings_handler)
            self.settings.set_value("find-text", GLib.Variant('as', s))
            # self.settings.handler_unblock(self.on_settings_handler)

    def find_next(self):
        """

        Returns textBuffer iters for the start and end of the next
        match within the text from the "insert" mark and the end (or
        beginning) of the element (or -1 if none).

        For regex matches, sets self.match

        May move to the next item in the tree if "global_bool" is set.

        Returns 1 if something found; else 0.

        """
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])

        self.remove_tag()
        self.hit_start = self.hit_end = -1
        # set this to 0 when we can't find anything in the current item:
        look_in_current_item = 1
        current_tree_iter = self.get_first_selected_iter()

        while self.hit_start == -1:
            if look_in_current_item:
                if self.settings.get_boolean("find-backwards"):
                    start_iter = self.textBuffer.get_start_iter()
                    end_mark = self.textBuffer.get_insert()
                    end_iter = self.textBuffer.get_iter_at_mark(end_mark)
                    self.start_offset = 0
                else:
                    start_mark = self.textBuffer.get_insert()
                    start_iter = self.textBuffer.get_iter_at_mark(start_mark)
                    end_iter = self.textBuffer.get_end_iter()
                    self.start_offset = start_iter.get_offset()
                zone = self.textBuffer.get_text(start_iter, end_iter, False)
            else:
                if not self.settings.get_boolean("find-global"):
                    return 0
                # we need the next tree item:
                if self.settings.get_boolean("find-backwards"):
                    current_tree_iter = self.get_linear_prev(current_tree_iter)
                else:
                    current_tree_iter = self.get_linear_next(current_tree_iter)
                if not current_tree_iter:
                    return 0
                zone = self.get_node_value(current_tree_iter)
                self.start_offset = 0

            search_regex = self.gui_get_widget("menubar_find_entry").get_text()
            if self.debug:
                print("Searching for: ", search_regex)

            self.add_string_to_combobox(search_regex, prepend = True)
            self.update_settings_from_combobox()

            # py2: search_regex = search_regex.decode("utf-8")
            # py2: zone = zone.decode("utf-8")

            if not self.settings.get_boolean("find-regex"):
                search_regex = re.escape(search_regex)

            if not self.settings.get_boolean("find-match-case"):
                options = re.IGNORECASE

            try:
                self.pattern = re.compile(search_regex, options)
            except:
                self.err_msg(_("Bad regular expression"))
                return

            self.match = None
            if self.settings.get_boolean("find-backwards"):
                # accept the last match:
                for self.match in self.pattern.finditer(zone):
                    pass
            else:
                self.match = self.pattern.search(zone)
            if self.match:
                self.hit_start = self.match.start()
                self.hit_end = self.match.end()
            else:
                look_in_current_item = 0
                continue

            # OK - we got one, now return:
            if not look_in_current_item:
                current_tree_path = self.treestore.get_path(current_tree_iter)
                self.treeView.expand_to_path(current_tree_path)
                self.treeView.get_selection().unselect_all()
                self.treeView.get_selection().select_iter(current_tree_iter)
                self.treeView.scroll_to_cell(current_tree_path, None, 1,
                                             0.5, 0.5)
            hit_start_iter = self.textBuffer.get_iter_at_offset(
                self.start_offset + self.hit_start)
            hit_end_iter = self.textBuffer.get_iter_at_offset(
                self.start_offset + self.hit_end)
            #self.textBuffer.move_mark_by_name("selection_bound", hit_start_iter)
            self.textBuffer.apply_tag(self.found_tag, hit_start_iter,
                hit_end_iter)
            if self.settings.get_boolean("find-backwards"):
                self.textBuffer.place_cursor(hit_start_iter)
            else:
                self.textBuffer.place_cursor(hit_end_iter)
            start_mark = self.textBuffer.get_insert()
            self.textView.scroll_to_mark(start_mark, 0.0 , 1, 1.0, 0.5)
            return 1

    def replace_next(self):
        """

        Returns 1 if something found; else 0

        """
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.sync_text_buffer()
        if self.hit_start == -1:
            return self.find_next()

        hit_start_iter = self.textBuffer.get_iter_at_offset(
            self.start_offset + self.hit_start)
        hit_end_iter = self.textBuffer.get_iter_at_offset(
            self.start_offset + self.hit_end)
        if self.settings.get_boolean("find-regex"):
            new_text = self.pattern.sub(
                self.settings.get_string("replace-text"),
                self.textBuffer.get_text(hit_start_iter, hit_end_iter, False))
        else:
            new_text = self.settings.get_string("replace-text")

        self.textBuffer.place_cursor(hit_end_iter)
        self.textBuffer.delete(hit_start_iter, hit_end_iter)
        self.textBuffer.insert_at_cursor(new_text)
        # "insert" mark is now at the _end_ of the replaced text.
        # Now place the "selection" mark at the start of the replaced text:
        start_mark = self.textBuffer.get_insert()
        start_iter = self.textBuffer.get_iter_at_mark(start_mark)
        self.start_offset = start_iter.get_offset()
        new_selection_bound_iter = self.textBuffer.get_iter_at_offset(
            self.start_offset - len(new_text))
        self.textBuffer.move_mark_by_name("selection_bound",
                                          new_selection_bound_iter)

        # now find the next one:
        return self.find_next()


    def _wrangle_geometry(self):
        if self.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        if not self.has_set_size:
            self.has_set_size = 1
            width = height = 0
            if self.geometry and len(self.geometry) > 0:
                m = re.match(r"(\d+)x(\d+)", self.geometry)
                if m and m.group:
                    width = int(m.group(1))
                    height = int(m.group(2))
                else:
                    sys.stderr.write(_("%s: bad geometry specification: %s\n") % (self.progName, self.geometry))
                    sys.exit(1)
                self.geometry = ""
            if height == 0 and width == 0 and self.settings:
                width = self.settings.get_int("width")
                height = self.settings.get_int("height")
            if height > 0 and width > 0:
                # print "setting size to", width, height
                self.gjots.resize(width, height)
        else:
            width, height = self.gjots.get_size()
            self.settings.set_int("width", width)
            self.settings.set_int("height", height)
        return

    def _init_icons(self):
        """
        Registers all of the required images as stock items for easy use
        within the gjots2 ui file.
        """
        for stock_name, file in self.icons.items():
            factory = Gtk.IconFactory()
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(file)
            iconset = Gtk.IconSet.new_from_pixbuf(pixbuf)
            factory.add(stock_name, iconset)
            factory.add_default()

    def init_gui(self, prefix, progName, geometry):
        """
        In this init we are going to display the main
        gjots window
        """

        # create widget tree ...
        self.has_set_size = 0
        self.progName = progName
        self.geometry = geometry

        # Try ./ first (if one local development file exists, then assume
        # all others exists) - developer's version, else goto site-packages.

        self.sharedir = "./"
        self.password = ""

        self.prefix = prefix

        # Format is 'stock-name':'file-name'
        self.icons = { 'gjots2-new-page' : 'gjots2-new-page.png',
                       'gjots2-new-child' : 'gjots2-new-child.png',
                       'gjots2-merge-items' : 'gjots2-merge-items.png',
                       'gjots2-split-item' : 'gjots2-split-item.png',
                       'gjots2-hide-all' : 'gjots2-hide-all.png',
                       'gjots2-show-all' : 'gjots2-show-all.png',
                       'gjots2-clock' : 'gjots2-clock.png'}

        # Perform more developer checks. If running from CVS or local
        # tarball, then register local icons, otherwise look in the system
        # data directory (e.g. /usr/share/gjots2).
        gui_file = "ui/gjots.ui"
        self.gui_filename = self.sharedir + gui_file
        if not os.access(self.gui_filename, os.F_OK):
            self.sharedir = prefix + "/share/gjots2/"
            self.gui_filename = self.sharedir + gui_file

        for name, file in self.icons.items():
            self.icons[name] = self.sharedir + "pixmaps/" + self.icons[name]

        self._init_icons()
        from gi.repository import Gtk, Gio
        Gtk.Window.set_default_icon_name("gjots")

        self.builder = Gtk.Builder()
        self.builder.set_translation_domain('gjots2')
        self.builder.add_from_file(self.gui_filename)
        self.builder.add_from_file(self.sharedir + "ui/treeContextMenu.ui")
        self.gui_get_widget = self.builder.get_object
        self.treeContextMenu_get_widget = self.builder.get_object

        self.treestore = None
        self.gjots = self.gui_get_widget("gjots")

        # Connect the window manager close window event to our callback
        self.gjots.connect("delete_event", self.delete_event)

        self.textView = self.gui_get_widget("textView")
        self.treeView = self.gui_get_widget("treeView")
        self.appbar = self.gui_get_widget("appbar")
        self.last_message = ""
        #self.appbar.set_default(self.last_message)
        self.dirtyflag = ""
        self._create_empty_tree()
        self.temp_text = _("New...>>>") # must be odd enough to never be in the user's text - problem when documenting gjots itself??
        self.tree_cutbuffer = None
        self.current_item = None
        self.combobox_max_lines_to_save = 10

        # this flag is used to reduce overhead on every keystroke - it
        # is set when the textBuffer is out of sync with the current
        # treestore item. It needs to be checked and sync'd
        # (sync_text_buffer()) before the current item is used eg in
        # any save, cut, copy, export and before exit. It is auto
        # sync'd on change of selection. There must be a nicer way to
        # do this with signals ...
        self.current_dirty = 0

        self.has_gtksourceview = 1
        self.sourceview_err_msg = ""
        self.sourceview_msg = " using gtksourceview"

        try:
            from gi.repository import GtkSource
            self.textBuffer = GtkSource.Buffer()
            self.textBuffer.set_text = lambda *args: not not (
                self.textBuffer.begin_not_undoable_action(),
                GtkSource.Buffer.set_text(*[self.textBuffer] + list(args)),
                self.textBuffer.end_not_undoable_action(),
                )
            self.sourceview_msg += GtkSource._version
        except:
            try:
                import gtksourceview
                self.textBuffer = gtksourceview.SourceBuffer()
                self.textBuffer.set_text = lambda *args: not not (
                    self.textBuffer.begin_not_undoable_action(),
                    gtksourceview.Buffer.set_text(*[self.textBuffer] + list(args)),
                    self.textBuffer.end_not_undoable_action(),
                    )
            except:
                self.sourceview_err_msg = _("Install gtksourceview to enable undo/redo")
                self.textBuffer = Gtk.TextBuffer()
                self.has_gtksourceview = 0
                self.sourceview_msg = " no gtksourceview!!"

        self.textView.set_buffer(self.textBuffer)
        self.textBuffer.set_text("", 0)
        self.hit_start = self.hit_end = -1
        self.found_tag = self.textBuffer.create_tag(None,
                                                    background="lightblue")

        # add a model to make the combobox == combobox_with_text (can't do it in glade2 or 3)
        self.on_combobox_handler = None
        self.combobox = self.gui_get_widget("menubar_find_combobox");
        if self.combobox:
            liststore = Gtk.ListStore(GObject.TYPE_STRING)
            self.combobox.set_model(liststore)
            cell = Gtk.CellRendererText()
            self.combobox.pack_start(cell, True)

        self._initialise_settings()
        self._wrangle_geometry()
        self.cut_text = None
        self.browser = None
        self.find_dialog = None

        self.file_filter = Gtk.FileFilter()
        self.file_filter_pattern = [ "*.gjots*", "*.org" ]
        for p in self.file_filter_pattern:
            self.file_filter.add_pattern(p)
        self.file_filter.set_name("All gjots files *.gjots* *.org")

        # Init the clipboard to use the system default "CLIPBOARD"
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        if not self.clipboard:
            print("No clipboard")
            sys.exit(3)
        self.primary = Gtk.Clipboard.get(Gdk.SELECTION_PRIMARY)
        if not self.primary:
            print("No primary clipboard")
            sys.exit(3)

        self._disable_tree_paste()

        callbacks = {
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
            "on_findAgainBackwards_trigger": self.on_findAgainBackwards_trigger,

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
            "on_textView_move_cursor":      self.on_textView_move_cursor,

            # tree callbacks
            "on_tree_selection_changed":    self.on_tree_selection_changed,
            "on_tree_drag_drop":            self.on_tree_drag_drop,
            "on_tree_key_press_event":      self.on_tree_key_press_event,
            "on_tree_button_press_event":   self.on_tree_button_press_event,

            # menutoolbar callbacks
            "on_menubar_find_entry_icon_press": self.on_menubar_find_entry_icon_press,
            "on_menubar_find_entry_activate": self.on_menubar_find_entry_activate,
            "on_menubar_find_entry_changed": self.on_menubar_find_entry_changed,
            "on_gjots_focus_out_event":     self.on_gjots_focus_out_event,
        }
        self.builder.connect_signals(callbacks)

        self.textBuffer_changed_handler = self.textBuffer.connect("changed", self.on_textBuffer_changed)
        self.on_tree_selection_changed_handler = self.treeView.get_selection().connect("changed", self.on_tree_selection_changed)
        self.on_combobox_handler = self.gui_get_widget("menubar_find_combobox").connect("changed", self.on_combobox_changed)
        self.on_readOnly_handler = self.gui_get_widget("readOnlyMenuItem").connect("activate", self.on_readOnly_trigger)

        # self.on_settings_handler = self.settings.connect("changed::find-text", self.on_settings_find_text_changed, self.gjots)
        self.settings.connect("changed::text-font", self.on_settings_text_font_changed, self.gjots)
        self.settings.connect("changed::top-toolbar", self.on_settings_top_toolbar_changed, self.gjots)
        self.settings.connect("changed::side-toolbar", self.on_settings_side_toolbar_changed, self.gjots)
        self.settings.connect("changed::show-icon-text", self.on_settings_show_icon_text_changed, self.gjots)
        self.settings.connect("changed::status-bar", self.on_settings_status_bar_changed, self.gjots)
        self.settings.connect("changed::pane-position", self.on_settings_pane_position_changed, self.gjots)
        return

    def __init__(self, prefix, progName, geometry, filename, readonly, debug, purge_password):

        if debug:
            print(inspect.getframeinfo(inspect.currentframe())[2], vars())
            self.debug = 1
            #sys.settrace(self.debugfunc)
        else:
            self.debug = 0

        self.purge_password = purge_password

        self.init_gui(prefix, progName, geometry)

        if not self.gjotsfile.read_file("", filename, readonly, import_after=None):
            sys.exit(1)
        root_path = self.treestore.get_path(self.get_root())
        self.treeView.expand_row(root_path, 0)
        self._warp(self.get_root())
        #self.treeView.get_selection().select_path(root_path)

        self.msg(progName + _(": version ") + gjots_version + self.sourceview_msg + " + glade3 (libglade)")

        self.treeView.grab_focus()
        self.gjots.show()

        if self.sourceview_err_msg != "":
            self.err_msg(self.sourceview_err_msg)

        self.autosave_timeout_tag = False

        self.set_readonly(readonly, quietly=1)
        self._do_goto_root()
        return

# Local variables:
# eval:(setq compile-command "cd ..; ./gjots2 test.gjots")
# eval:(setq indent-tabs-mode nil)
# eval:(setq tab-width 4)
# eval:(setq python-indent 4)
# End:
