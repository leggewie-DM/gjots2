from gi.repository import Gtk
from gi.repository import GConf
import inspect

from common import *

"""

OK, yeah, I know - strictly speaking we should have a nofifier in here
in case something else (eg gconf-editor) changes a setting while we
are in here, but quite honestly - really!

"""

class font_dialog:
    def destroy(self):
        if self.gui.debug:
            print inspect.getframeinfo(inspect.currentframe())[2]
        self.fonts_get_widget(self.name).destroy()

    def on_fontCancel_clicked(self, widget):
        if self.gui.debug:
            print inspect.getframeinfo(inspect.currentframe())[2]
        self.value = CANCEL

    def on_fontApply_clicked(self, widget):
        if self.gui.debug:
            print inspect.getframeinfo(inspect.currentframe())[2]
        self.value = OK

    def on_fontOK_clicked(self, widget):
        if self.gui.debug:
            print inspect.getframeinfo(inspect.currentframe())[2]
        self.value = OK

    def __init__(self, gui):
        """
        Font dialog
        """

        self.gui = gui
        if self.gui.debug:
            print inspect.getframeinfo(inspect.currentframe())[2]

        callbacks = {
            "on_fontCancel_clicked":                    self.on_fontCancel_clicked,
            "on_fontApply_clicked":                     self.on_fontApply_clicked,
            "on_fontOK_clicked":                        self.on_fontOK_clicked,
        }
        self.name = "fontselectiondialog"
        self.gui.builder.add_from_file(self.gui.sharedir + "ui/fontDialog.ui")
        self.gui.builder.connect_signals(callbacks)
        self.fonts_get_widget = self.gui.gui_get_widget

        self.fontselectiondialog = self.fonts_get_widget("fontselectiondialog")
        self.fontselectiondialog.set_font_name(self.gui.settings.get_string("text-font"))
        self.value = WAITING
        while self.value == WAITING:
            Gtk.main_iteration()

class prefs_dialog:
    def destroy(self):
        if self.gui.debug:
            print inspect.getframeinfo(inspect.currentframe())[2]
        self.prefs_get_widget(self.name).destroy()

    def on_fontButton_clicked(self, widget):
        if self.gui.debug:
            print inspect.getframeinfo(inspect.currentframe())[2]
        f = font_dialog(self.gui)
        if f.value == OK:
            self.fontName_entry.set_text(f.fontselectiondialog.get_font_name())
        f.destroy()
        
    def on_prefsOK_clicked(self, widget):
        if self.gui.debug:
            print inspect.getframeinfo(inspect.currentframe())[2]
        
        self.gui.settings.set_int("line-length",            self.lineLength_spinbutton.get_value_as_int())
        self.gui.settings.set_string("text-formatter",  self.textFormatter_entry.get_text())
        self.gui.settings.set_string("external-editor",     self.externalEditor_entry.get_text())
        self.gui.settings.set_string("date-format",         self.dateFormat_entry.get_text())
        self.gui.settings.set_string("text-font",       self.fontName_entry.get_text())
        self.gui.settings.set_int("auto-save-interval",   self.autoSaveInterval_spinbutton.get_value_as_int())
        self.gui.set_autosave_timeout()
        self.destroy()

    def on_prefsCancel_clicked(self, widget):
        if self.gui.debug:
            print inspect.getframeinfo(inspect.currentframe())[2]
        self.destroy()
    
    def on_textFormatter_key_press_event(self, widget, key_event):
        if self.gui.debug:
            print inspect.getframeinfo(inspect.currentframe())[2], vars()
        if key_event.keyval == Gdk.KEY_Return or key_event.keyval == Gdk.KEY_KP_Enter:
            self.on_prefsOK_clicked(widget)
        if key_event.keyval == Gdk.KEY_Escape:
            self.on_prefsCancel_clicked(widget)
        return
    
    def on_lineLength_key_press_event(self, widget, key_event):
        if self.gui.debug:
            print inspect.getframeinfo(inspect.currentframe())[2], vars()
        if key_event.keyval == Gdk.KEY_Return or key_event.keyval == Gdk.KEY_KP_Enter:
            self.on_prefsOK_clicked(widget)
        if key_event.keyval == Gdk.KEY_Escape:
            self.on_prefsCancel_clicked(widget)
        return
    
    def on_externalEditor_key_press_event(self, widget, key_event):
        if self.gui.debug:
            print inspect.getframeinfo(inspect.currentframe())[2], vars()
        if key_event.keyval == Gdk.KEY_Return or key_event.keyval == Gdk.KEY_KP_Enter:
            self.on_prefsOK_clicked(widget)
        if key_event.keyval == Gdk.KEY_Escape:
            self.on_prefsCancel_clicked(widget)
        return
    
    def on_dateFormat_key_press_event(self, widget, key_event):
        if self.gui.debug:
            print inspect.getframeinfo(inspect.currentframe())[2], vars()
        if key_event.keyval == Gdk.KEY_Return or key_event.keyval == Gdk.KEY_KP_Enter:
            self.on_prefsOK_clicked(widget)
        if key_event.keyval == Gdk.KEY_Escape:
            self.on_prefsCancel_clicked(widget)
        return
    
    def on_fontName_key_press_event(self, widget, key_event):
        if self.gui.debug:
            print inspect.getframeinfo(inspect.currentframe())[2], vars()
        if key_event.keyval == Gdk.KEY_Return or key_event.keyval == Gdk.KEY_KP_Enter:
            self.on_prefsOK_clicked(widget)
        if key_event.keyval == Gdk.KEY_Escape:
            self.on_prefsCancel_clicked(widget)
        return

    def __init__(self, gui):
        """
        Prefs dialog
        """

        self.gui = gui
        if self.gui.debug:
            print inspect.getframeinfo(inspect.currentframe())[2]

        callbacks = {
            "on_fontButton_clicked":                    self.on_fontButton_clicked,
            "on_prefsOK_clicked":                       self.on_prefsOK_clicked,
            "on_prefsCancel_clicked":                   self.on_prefsCancel_clicked,
            "on_textFormatter_key_press_event":         self.on_textFormatter_key_press_event,
            "on_lineLength_key_press_event":            self.on_lineLength_key_press_event,
            "on_externalEditor_key_press_event":        self.on_externalEditor_key_press_event,
            "on_dateFormat_key_press_event":            self.on_dateFormat_key_press_event,
            "on_fontName_key_press_event":              self.on_fontName_key_press_event,
        }
        self.name = "prefsDialog"
        self.gui.builder.add_from_file(self.gui.sharedir + "ui/prefsDialog.ui")
        self.gui.builder.connect_signals(callbacks)
        self.prefs_get_widget = self.gui.gui_get_widget

        self.lineLength_spinbutton = self.prefs_get_widget("lineLength")
        self.autoSaveInterval_spinbutton = self.prefs_get_widget("autoSaveInterval")
        self.autoSaveInterval_spinbutton.set_range(0, 3600)
        self.textFormatter_entry = self.prefs_get_widget("textFormatter")
        self.externalEditor_entry = self.prefs_get_widget("externalEditor")
        self.dateFormat_entry = self.prefs_get_widget("dateFormat")
        self.fontName_entry = self.prefs_get_widget("fontName")
        
        self.lineLength_spinbutton.set_value(self.gui.settings.get_int   ("line-length"))
        self.textFormatter_entry.set_text   (self.gui.settings.get_string("text-formatter"))
        self.externalEditor_entry.set_text  (self.gui.settings.get_string("external-editor"))
        self.dateFormat_entry.set_text      (self.gui.settings.get_string("date-format"))
        self.fontName_entry.set_text        (self.gui.settings.get_string("text-font"))
        self.autoSaveInterval_spinbutton.set_value(self.gui.settings.get_int("auto-save-interval"))

# Local variables:
# eval:(setq compile-command "cd ..; ./gjots2 test.gjots")
# eval:(setq indent-tabs-mode 1)
# eval:(setq tab-width 4)
# eval:(setq python-indent 4)
# End:
