import gtk
import gnome
import gconf
import inspect

from common import *

"""

OK, yeah, I know - strictly speaking we should have a nofifier in here
in case something else (eg gconf-editor) changes a setting while we
are in here, but quite honestly - really!

"""

class font_dialog:
	def destroy(self):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.xml.get_widget(self.name).destroy()

	def on_fontCancel_clicked(self, widget):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.value = CANCEL

	def on_fontApply_clicked(self, widget):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.value = OK

	def on_fontOK_clicked(self, widget):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.value = OK

	def __init__(self, gui):
		"""
		Font dialog
		"""

		self.gui = gui
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]

		callbacks = {
			"on_fontCancel_clicked":					self.on_fontCancel_clicked,
			"on_fontApply_clicked":						self.on_fontApply_clicked,
			"on_fontOK_clicked":						self.on_fontOK_clicked,
		}
		self.name = "fontselectiondialog"
		self.xml = gtk.glade.XML(self.gui.gui_filename, self.name, domain="gjots2")
		self.xml.signal_autoconnect(callbacks)
		self.fontselectiondialog = self.xml.get_widget("fontselectiondialog")
		self.fontselectiondialog.set_font_name(self.gui.client.get_string(self.gui.text_font_path))
		self.value = WAITING
		while self.value == WAITING:
			gtk.main_iteration()
		self.destroy()

class prefs_dialog:
	def destroy(self):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.xml.get_widget(self.name).destroy()

	def on_fontButton_clicked(self, widget):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		f = font_dialog(self.gui)
		if f.value == OK:
			self.gui.client.set_string(self.gui.text_font_path, f.fontselectiondialog.get_font_name())
			self.fontName_entry.set_text(self.gui.client.get_string(self.gui.text_font_path))
		
	def on_prefsOK_clicked(self, widget):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		
		self.gui.client.set_int(self.gui.line_length_path, 			self.lineLength_spinbutton.get_value_as_int())
		self.gui.client.set_string(self.gui.text_formatter_path, 	self.textFormatter_entry.get_text())
		self.gui.client.set_string(self.gui.external_editor_path, 	self.externalEditor_entry.get_text())
		self.gui.client.set_string(self.gui.date_format_path, 		self.dateFormat_entry.get_text())
		self.gui.client.set_string(self.gui.text_font_path, 		self.fontName_entry.get_text())
		self.destroy()

	def on_prefsCancel_clicked(self, widget):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.destroy()
	
	def on_textFormatter_key_press_event(self, widget, key_event):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()
		if key_event.keyval == gtk.keysyms.Return or key_event.keyval == gtk.keysyms.KP_Enter:
			self.on_prefsOK_clicked(widget)
		if key_event.keyval == gtk.keysyms.Escape:
			self.on_prefsCancel_clicked(widget)
		return
	
	def on_lineLength_key_press_event(self, widget, key_event):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()
		if key_event.keyval == gtk.keysyms.Return or key_event.keyval == gtk.keysyms.KP_Enter:
			self.on_prefsOK_clicked(widget)
		if key_event.keyval == gtk.keysyms.Escape:
			self.on_prefsCancel_clicked(widget)
		return
	
	def on_externalEditor_key_press_event(self, widget, key_event):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()
		if key_event.keyval == gtk.keysyms.Return or key_event.keyval == gtk.keysyms.KP_Enter:
			self.on_prefsOK_clicked(widget)
		if key_event.keyval == gtk.keysyms.Escape:
			self.on_prefsCancel_clicked(widget)
		return
	
	def on_dateFormat_key_press_event(self, widget, key_event):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()
		if key_event.keyval == gtk.keysyms.Return or key_event.keyval == gtk.keysyms.KP_Enter:
			self.on_prefsOK_clicked(widget)
		if key_event.keyval == gtk.keysyms.Escape:
			self.on_prefsCancel_clicked(widget)
		return
	
	def on_fontName_key_press_event(self, widget, key_event):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()
		if key_event.keyval == gtk.keysyms.Return or key_event.keyval == gtk.keysyms.KP_Enter:
			self.on_prefsOK_clicked(widget)
		if key_event.keyval == gtk.keysyms.Escape:
			self.on_prefsCancel_clicked(widget)
		return

	def __init__(self, gui):
		"""
		Prefs dialog
		"""

		self.gui = gui
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]

		callbacks = {
			"on_fontButton_clicked":					self.on_fontButton_clicked,
			"on_prefsOK_clicked":						self.on_prefsOK_clicked,
			"on_prefsCancel_clicked":					self.on_prefsCancel_clicked,
			"on_textFormatter_key_press_event":			self.on_textFormatter_key_press_event,
			"on_lineLength_key_press_event":			self.on_lineLength_key_press_event,
			"on_externalEditor_key_press_event":		self.on_externalEditor_key_press_event,
			"on_dateFormat_key_press_event":			self.on_dateFormat_key_press_event,
			"on_fontName_key_press_event":				self.on_fontName_key_press_event,
		}
		self.name = "prefs"
		self.xml = gtk.glade.XML(self.gui.gui_filename, self.name, domain="gjots2")
		self.xml.signal_autoconnect(callbacks)

		self.lineLength_spinbutton = self.xml.get_widget("lineLength")
		self.textFormatter_entry = self.xml.get_widget("textFormatter")
		self.externalEditor_entry = self.xml.get_widget("externalEditor")
		self.dateFormat_entry = self.xml.get_widget("dateFormat")
		self.fontName_entry = self.xml.get_widget("fontName")
		
		self.lineLength_spinbutton.set_value(self.gui.client.get_int   (self.gui.line_length_path))
		self.textFormatter_entry.set_text   (self.gui.client.get_string(self.gui.text_formatter_path))
		self.externalEditor_entry.set_text  (self.gui.client.get_string(self.gui.external_editor_path))
		self.dateFormat_entry.set_text      (self.gui.client.get_string(self.gui.date_format_path))
		self.fontName_entry.set_text        (self.gui.client.get_string(self.gui.text_font_path))

# Local variables:
# eval:(setq compile-command "cd ..; ./gjots2 j")
# End:
