import inspect

class find_dialog:

    def destroy(self):
        if self.gui.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.find_get_widget(self.name).destroy()
        self.gui.remove_tag()

    def saveSettings(self):
        if self.gui.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        w = self.find_get_widget("caseCheckbutton")
        if w:
            self.gui.settings.set_boolean("find-match-case", w.get_active())

        w = self.find_get_widget("globalCheckbutton")
        if w:
            self.gui.settings.set_boolean("find-global", w.get_active())

        w = self.find_get_widget("regexCheckbutton")
        if w:
            self.gui.settings.set_boolean("find-regex", w.get_active())

        w = self.find_get_widget("backwardsCheckbutton")
        if w:
            self.gui.settings.set_boolean("find-backwards", w.get_active())

        self.gui.add_string_to_combobox(self.find_get_widget("findEntry").get_text(), True)
        self.gui.update_settings_from_combobox()

        w = self.find_get_widget("replaceEntry")
        if w:
            self.gui.settings.set_string("replace-text", w.get_text())

        return

    def on_findDialog_destroy(self, widget):
        if self.gui.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.gui.find_dialog = None
        return

    def on_replaceEntry_key_press_event(self, widget, key_event):
        if self.gui.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2], vars())
        if key_event.keyval == gi.repository.Gdk.KEY_Return or key_event.keyval == gi.repository.Gdk.KEY_KP_Enter:
            self.on_replaceStartButton_clicked(widget)
        if key_event.keyval == gi.repository.Gdk.KEY_Escape:
            self.on_findCancelButton_clicked(widget)
        return

    def feedback(self, msg):
        if self.gui.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2], vars())
        w = self.find_get_widget("findFeedback")
        if w:
            w.set_text(msg)
        return

    def on_findStartButton_clicked(self, widget):
        if self.gui.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.gui.sync_text_buffer()
        self.saveSettings()
        self.feedback("")

        if not self.gui.find_next():
            self.feedback(_("Not found"))
        else:
            self.feedback(_("Found"))

        w = self.find_get_widget("findEntry")
        if w:
            w.grab_focus()

    def on_findCloseButton_clicked(self, widget):
        if self.gui.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.saveSettings()
        self.destroy()
        return

    def on_replaceStartButton_clicked(self, widget):
        if self.gui.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.gui.sync_text_buffer()
        self.saveSettings()
        self.feedback("")

        if not self.gui.replace_next():
            self.feedback(_("Not found"))
            return

        self.feedback(_("Replace?"))

        w = self.find_get_widget("findEntry")
        if w:
            w.grab_focus()
        return

    def on_replaceAllButton_clicked(self, widget):
        if self.gui.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.gui.sync_text_buffer()
        self.saveSettings()
        total = 0
        i = 1
        while i:
            i = self.gui.replace_next()
            total = total + i
        self.feedback(_("%d substitutions") % total)

        w = self.find_get_widget("findEntry")
        if w:
            w.grab_focus()
        return

    def on_findCancelButton_clicked(self, widget):
        if self.gui.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        self.destroy()
        return

    def on_findClearButton_clicked(self, widget):
        if self.gui.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        w = self.find_get_widget("findEntry")
        if w:
            w.set_text("")
            w.grab_focus()

        w = self.find_get_widget("replaceEntry")
        if w:
            w.set_text("")
        return

    def _set_readonly(self, mode):
        if self.gui.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])
        if mode:
            w = self.find_get_widget("replaceStartButton")
            w.hide()
            w = self.find_get_widget("replaceEntry")
            w.hide()
            w = self.find_get_widget("replaceLabel")
            w.hide()
            w = self.find_get_widget("replaceAllButton")
            w.hide()
        else:
            w = self.find_get_widget("replaceStartButton")
            w.show()
            w = self.find_get_widget("replaceEntry")
            w.show()
            w = self.find_get_widget("replaceLabel")
            w.show()
            w = self.find_get_widget("replaceAllButton")
            w.show()

    def __init__(self, gui):
        """
        Find dialog
        """

        self.gui = gui
        if self.gui.debug:
            print(inspect.getframeinfo(inspect.currentframe())[2])

        callbacks = {
            "on_findDialog_destroy":                    self.on_findDialog_destroy,
            "on_replaceEntry_key_press_event":          self.on_replaceEntry_key_press_event,
            "on_findStartButton_clicked":               self.on_findStartButton_clicked,
            "on_findCloseButton_clicked":               self.on_findCloseButton_clicked,
            "on_replaceStartButton_clicked":            self.on_replaceStartButton_clicked,
            "on_replaceAllButton_clicked":              self.on_replaceAllButton_clicked,
            "on_findCancelButton_clicked":              self.on_findCancelButton_clicked,
            "on_findClearButton_clicked":               self.on_findClearButton_clicked
        }
        self.name = "findDialog"
        self.gui.builder.add_from_file(self.gui.sharedir + "ui/findDialog.ui")
        self.gui.builder.connect_signals(callbacks)
        self.find_get_widget = self.gui.gui_get_widget

        w = self.find_get_widget("caseCheckbutton")
        if w:
            w.set_active(self.gui.settings.get_boolean("find-match-case"))

        w = self.find_get_widget("globalCheckbutton")
        if w:
            w.set_active(self.gui.settings.get_boolean("find-global"))

        w = self.find_get_widget("regexCheckbutton")
        if w:
            w.set_active(self.gui.settings.get_boolean("find-regex"))

        w = self.find_get_widget("backwardsCheckbutton")
        if w:
            w.set_active(self.gui.settings.get_boolean("find-backwards"))

        w = self.find_get_widget("findEntry")
        if w:
            current_search_text = self.gui.get_active_item_from_combobox()
            if current_search_text:
                w.set_text(current_search_text)
            else:
                w.set_text("")

        w = self.find_get_widget("replaceEntry")
        if w:
            w.set_text(self.gui.settings.get_string("replace-text"))

        self.feedback("")
        self._set_readonly(self.gui.readonly)

# find_dialog

# Local variables:
# eval:(setq compile-command "cd ..; ./gjots2 test.gjots")
# eval:(setq indent-tabs-mode nil)
# eval:(setq tab-width 4)
# eval:(setq python-indent 4)
# End:
