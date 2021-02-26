import re
import inspect
import tempfile
import pipes
import string
from gi.repository import GObject, Gtk

"""

We'll actually sort a list of list, each element of which is [ row,
title, value ] "value" is only used for numeric sorts and is extracted
by the _safe_float routine.

"""

# from: https://docs.python.org/3/howto/sorting.html
def cmp_to_key(mycmp):
    'Convert a cmp= function into a key= function'
    class K:
        def __init__(self, obj, *args):
            self.obj = obj
        def __lt__(self, other):
            return mycmp(self.obj, other.obj) < 0
        def __gt__(self, other):
            return mycmp(self.obj, other.obj) > 0
        def __eq__(self, other):
            return mycmp(self.obj, other.obj) == 0
        def __le__(self, other):
            return mycmp(self.obj, other.obj) <= 0
        def __ge__(self, other):
            return mycmp(self.obj, other.obj) >= 0
        def __ne__(self, other):
            return mycmp(self.obj, other.obj) != 0
    return K

def cmp(a, b):
    return (a > b) - (a < b)

def _sort_function_alpha_asc(x, y):
    return cmp(x[1].lower(), y[1].lower())

def _sort_function_alpha_des(x, y):
    return -cmp(x[1].lower(), y[1].lower())

def _safe_float(xin):
    """
    Hopefully, this will barf on nothing, unlike a bare "float" - always returns a number or None if "not a number"
    """
    x = xin
    if not x or x == "":
        return None
    m = re.search('[-+]?(\d+(\.\d*)?|\d*\.\d+)([eE][-+]?\d+)?', x)
    if m:
        return(float(x[m.start():m.end()]))
    else:
        return None

def _num_cmp(xin, yin):
    x = _safe_float(xin)
    y = _safe_float(yin)
    if x == y: # could both be "None"
        return 0
    if x == None:
        return -1;
    if y == None:
        return 1;
    if x < y:
        return -1
    return 1
     
def _sort_function_num_asc(x, y):
    return _num_cmp(x[1], y[1])

def _sort_function_num_des(x, y):
    return -_num_cmp(x[1], y[1])

class sort_dialog:
    def destroy(self):
        if self.gui.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.sort_get_widget(self.name).destroy()

    def saveSettings(self):
        if self.gui.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        w = self.sort_get_widget("sortAscendingRadioButton")
        if w:
            self.gui.settings.set_boolean("sort-ascending", w.get_active())
        else:
            print("Cant find sortAscendingRadioButton")
        w = self.sort_get_widget("sortAlphabeticRadioButton")
        if w:
            self.gui.settings.set_boolean("sort-alpha", w.get_active())

        w = self.sort_get_widget("sortSublevelsSpinButton")
        if w:
            self.gui.settings.set_int("sort-sublevels", w.get_value_as_int())
        
        return
    
    def on_sortDialog_destroy(self, widget):
        if self.gui.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        return
    
    def on_sortCommandEntry_key_press_event(self, widget, key_event):
        if self.gui.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2], vars())

        # to get all keysyms see gdk/gdkkeysyms.h
        if key_event.keyval == gi.repository.Gdk.KEY_Return or key_event.keyval == gi.repository.Gdk.KEY_KP_Enter:
            self.on_sortOKButton_clicked(widget)
        if key_event.keyval == gi.repository.Gdk.KEY_Escape:
            self.on_sortCancelButton_clicked(widget)
        return

    def _get_settings(self):
        if self.gui.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        sort_ascending = sort_alpha = sort_items = sort_sublevels = 0
        w = self.sort_get_widget("sortAscendingRadioButton")
        if w:
            sort_ascending = w.get_active()
        else:
            print(_("_get_settings: Cant find sortAscendingRadioButton"))
        w = self.sort_get_widget("sortAlphabeticRadioButton")
        if w:
            sort_alpha = w.get_active()

        w = self.sort_get_widget("sortSublevelsSpinButton")
        if w:
            sort_sublevels = w.get_value_as_int()

        if self.type == "tree":
            sort_items = True

        return sort_ascending, sort_alpha, sort_items, sort_sublevels
            
    def _sort_item(self, item, start_iter, end_iter, sort_ascending, sort_alpha, sort_sublevels, level):
        """
        Sort the children of the current item, starting at start_iter,
        ending at end_iter (0,0 mean first & last).

        Always sort one level. If sublevels, then sort children recursively up to sort_sublevels deep (<0 for all).

        Sorting only takes place on the title, not on the body.
        """
        if self.gui.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2], vars())
            print("Item = ", self.gui.treestore.get_value(item, 0))

        item_path = self.gui.treestore.get_path(item)
        item_was_expanded = self.gui.treeView.row_expanded(item_path)
        
        child = self.gui.treestore.iter_children(item)
        if not child:
            return

        if start_iter == 0:
            start_iter = child
        else:
            while not self.gui.same_iter(child, start_iter):
                child = self.gui.treestore.iter_next(child)
                if not child:
                    self.gui.msg(_("Internal error"))
                    return

        if end_iter == 0:
            next = end_iter = start_iter
            while next:
                end_iter = next
                next = self.gui.treestore.iter_next(end_iter)

        # contruct the sort list
        sort_list = [ ]
        child = self.gui.treestore.iter_children(item)
        selection_start = -1
        selection_end = -1
        count = 0
        while child:
            if selection_start == -1 and self.gui.same_iter(child, start_iter):
                selection_start = count
            if selection_start != -1 and selection_end == -1:
                sort_list.append([count, self.gui.get_node_title(child)])
            if sort_sublevels < 0 or level < sort_sublevels:
                if selection_start != -1 and count >= selection_start and ( selection_end == -1 or count <= selection_end ):
                    if self.gui.treestore.iter_children(child):
                        self._sort_item(child, 0, 0, sort_ascending, sort_alpha, sort_sublevels, level + 1)
            if selection_end == -1 and self.gui.same_iter(child, end_iter):
                selection_end = count
            child = self.gui.treestore.iter_next(child)
            count = count + 1

        #print "sort_list before sort = ", sort_list
        # Do the sort
        if sort_alpha:
            if sort_ascending:
                sort_list.sort(key=cmp_to_key(_sort_function_alpha_asc))
            else:
                sort_list.sort(key=cmp_to_key(_sort_function_alpha_des))
        else:
            if sort_ascending:
                sort_list.sort(key=cmp_to_key(_sort_function_num_asc))
            else:
                sort_list.sort(key=cmp_to_key(_sort_function_num_des))
        #print "sort_list after sort = ", sort_list

        # Extract a reorder list from the sorted list
        child = self.gui.treestore.iter_children(item)
        count = 0
        reorder_list = [ ]
        while count < selection_start:
            reorder_list.append(count)
            child = self.gui.treestore.iter_next(child)
            count = count + 1
        sorted_count = 0
        while child and count <= selection_end:
            reorder_list.append(sort_list[sorted_count].pop(0))
            child = self.gui.treestore.iter_next(child)
            count = count + 1
            sorted_count = sorted_count + 1
        while child:
            reorder_list.append(count)
            child = self.gui.treestore.iter_next(child)
            count = count + 1
        #print "reorder_list = ", reorder_list
        try:
            self.gui.treestore.reorder(item, reorder_list)
        except:
            # gtk+-3.16 does not export reorder to python
            # https://bugzilla.gnome.org/show_bug.cgi?id=757796

            # a homebrew reorder
            
            # create a temporary treestore:
            temp_treestore = Gtk.TreeStore(
                GObject.TYPE_STRING, # title == first line of body except for root, which is filename
                GObject.TYPE_STRING, # body
                GObject.TYPE_INT)    # body_temp_flag - used after creating new items

            temp_treestore_root = temp_treestore.insert(None, 0)
            
            first_unselected = self.gui.treestore.iter_next(end_iter) # maybe None

            #print "start_iter = ", self.gui.treestore.get_value(start_iter, 0)
            #print "end_iter = ", self.gui.treestore.get_value(end_iter, 0)
            #print "first_unselected = ", self.gui.treestore.get_value(first_unselected, 0) if first_unselected else "None"
            
            # make a copy of the selected items and remove them from the treestore:
            this = start_iter
            while this:
                #print "copying ", self.gui.treestore.get_value(this, 0)
                next = self.gui.treestore.iter_next(this)
                if self.gui.same_iter(this, end_iter):
                    next = None
                self.gui._copy_subtree(
                    self.gui.treestore, this, 
                    temp_treestore, temp_treestore_root, 
                    -1)
                if not self.gui.treestore.remove(this): # returns false if no more items
                    next = None
                this = next

            # now copy them back in the right order:
            this = first_unselected if first_unselected else -1
            after = False
            # print "reorder_list = ", reorder_list
            count = 0
            for iter in reorder_list:
                if iter >= selection_start and iter <= selection_end:
                    # print "iter = ", iter
                
                    this = self.gui._copy_subtree(
                        temp_treestore, temp_treestore.iter_nth_child(temp_treestore_root, iter - selection_start),
                        self.gui.treestore, item, 
                        this, after)
                    count = count + 1
                    after = True

            # expand item:
            if item_was_expanded: self.gui.treeView.expand_row(item_path, 0)
            
            return
    
    def on_sortOKButton_clicked(self, widget):
        """
        """
        
        if self.gui.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.gui.sync_text_buffer()
        self.saveSettings()
        sort_ascending, sort_alpha, sort_items, sort_sublevels = self._get_settings()

        if not sort_items:
            # then sort lines
            body, start_text, end_text = self.gui.get_selected_text()
            if not body:
                start_text = self.gui.textBuffer.get_start_iter()
                end_text = self.gui.textBuffer.get_end_iter()
                body = self.gui.textBuffer.get_text(start_text, end_text, False)
                if not body:
                    self.gui.msg(_("Nothing to sort!"))
                    return
            text_list = body.split('\n')
            if sort_alpha:
                if sort_ascending:
                    text_list.sort(key=str.lower)
                else:
                    text_list.sort(key=str.lower, reverse=True)
            else:
                if sort_ascending:
                    text_list.sort()
                else:
                    text_list.sort(reverse=True)
                
            body = "\n".join(text_list)
            self.gui.textBuffer.delete(start_text, end_text)
            self.gui.textBuffer.insert(start_text, body, len(body))
            self.gui._set_dirtyflag()
            return

        """
        Sorting items - if only one item selected then sort its children.
        Otherwise sort the selected items
        """
        first_selected = self.gui.get_first_selected_iter()
        if not first_selected:
            self.gui.msg(_("Nothing selected"))
            return

        last_selected = self.gui.get_last_selected_iter()
        if not last_selected:
            self.gui.msg(_("Nothing selected"))
            return

        if self.gui.same_iter(first_selected, last_selected):
            # Only one item selected
            self._sort_item(first_selected, 0, 0, sort_ascending, sort_alpha, sort_sublevels, 0)
            self.gui._set_dirtyflag()
            return

        parent = self.gui.treestore.iter_parent(first_selected)
        if not parent:
            self.gui.msg(_("No parent!"))
            return

        self._sort_item(parent, first_selected, last_selected, sort_ascending, sort_alpha, sort_sublevels, 0)
        self.gui._set_dirtyflag()
        return
        
    def on_sortCancelButton_clicked(self, widget):
        if self.gui.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.destroy()
        return

    def __init__(self, gui, type):
        """
        Print dialog
        """

        # if type == "tree":
        #   gui.err_msg("tree sort is unavailable until GtkTreeStore.reorder() in gtk+ is fixed")
        #   return

        self.gui = gui
        if self.gui.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])

        callbacks = {
            "on_sortDialog_destroy":                    self.on_sortDialog_destroy,
            "on_sortCommandEntry_key_press_event":      self.on_sortCommandEntry_key_press_event,
            "on_sortOKButton_clicked":                  self.on_sortOKButton_clicked,
            "on_sortCancelButton_clicked":              self.on_sortCancelButton_clicked,
        }
        self.name = "sortDialog"
        self.gui.builder.add_from_file(self.gui.sharedir + "ui/sortDialog.ui")
        self.gui.builder.connect_signals(callbacks)
        self.sort_get_widget = self.gui.gui_get_widget

        # Initialize the GUI state of the radio buttons and spin button
        # based on the type of sort ('tree', 'text', or 'both')

        # TODO: Shouldn't we be setting each radio button???
        w = self.sort_get_widget("sortAscendingRadioButton")
        w.set_active(self.gui.settings.get_boolean("sort-ascending"))
        w = self.sort_get_widget("sortAlphabeticRadioButton")
        w.set_active(self.gui.settings.get_boolean("sort-alpha"))

        if type == "tree":
            self.type = "tree"
            self.sort_get_widget("sortSublevelsSpinButton").set_sensitive(True)
            self.sort_get_widget("sortDialog").set_title(_("Sort Tree"))
        elif type == "text":
            self.type = "text"
            self.sort_get_widget("sortRangeFrame").hide()
            self.sort_get_widget("sortDialog").set_title(_("Sort Text"))

        return
        
# sort_dialog

# Local variables:
# eval:(setq compile-command "cd ..; ./gjots2 test.gjots")
# eval:(setq indent-tabs-mode nil)
# eval:(setq tab-width 4)
# eval:(setq python-indent 4)
# End:
