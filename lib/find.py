import gtk.keysyms
import gtk.glade
import re
import inspect

class find_dialog:
		
	def destroy(self):
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.find_get_widget(self.name).destroy()
		self.gui.remove_tag()
		
	def saveSettings(self):
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2]
		w = self.find_get_widget("caseCheckbutton")
		if w:
			self.gui.client.set_bool(self.gui.find_match_case_path, w.get_active())

		w = self.find_get_widget("globalCheckbutton")
		if w:
			self.gui.client.set_bool(self.gui.find_global_path, w.get_active())

		w = self.find_get_widget("regexCheckbutton")
		if w:
			self.gui.client.set_bool(self.gui.find_regex_path, w.get_active())

		w = self.find_get_widget("backwardsCheckbutton")
		if w:
			self.gui.client.set_bool(self.gui.find_backwards_path, w.get_active())

		w = self.find_get_widget("findEntry")
		if w:
			self.gui.client.set_string(self.gui.find_text_path, w.get_text())
			m = self.find_get_widget("menubar_find_entry")
			if not m:
				# glade2
				m = self.gui.gui_get_widget("menubar_find_combobox").child
				
			if m:
				m.set_text(w.get_text())

		w = self.find_get_widget("replaceEntry")
		if w:
			self.gui.client.set_string(self.gui.replace_text_path, w.get_text())
		
		return
	
	def on_findDialog_destroy(self, widget):
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.gui.find_dialog = None
		return
	
	def on_replaceEntry_key_press_event(self, widget, key_event):
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()
		if key_event.keyval == gtk.keysyms.Return or key_event.keyval == gtk.keysyms.KP_Enter:
			self.on_replaceStartButton_clicked(widget)
		if key_event.keyval == gtk.keysyms.Escape:
			self.on_findCancelButton_clicked(widget)
		return

	def feedback(self, msg):
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()
		w = self.find_get_widget("findFeedback")
		if w:
			w.set_text(msg)
		return
		
	def on_findStartButton_clicked(self, widget):
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2]
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
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.saveSettings()
		self.destroy()
		return

	def on_replaceStartButton_clicked(self, widget):
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2]
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
			print inspect.getframeinfo(inspect.currentframe())[2]
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
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.destroy()
		return
	
	def on_findClearButton_clicked(self, widget):
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2]
		w = self.find_get_widget("findEntry")
		if w:
			w.set_text("")
			w.grab_focus()

		w = self.find_get_widget("replaceEntry")
		if w:
			w.set_text("")
		return
	
	def update_find_entry(self):
		# Potential for wonderful infinite loops here?
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2]
		m = self.find_get_widget("findEntry")
		if m:
			m.set_text(self.gui.client.get_string(self.gui.find_text_path))

	def _set_readonly(self, mode):
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2]
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
			print inspect.getframeinfo(inspect.currentframe())[2]

		callbacks = {
			"on_findDialog_destroy":					self.on_findDialog_destroy,
			"on_replaceEntry_key_press_event":			self.on_replaceEntry_key_press_event,
			"on_findStartButton_clicked":				self.on_findStartButton_clicked,
			"on_findCloseButton_clicked":				self.on_findCloseButton_clicked,
			"on_replaceStartButton_clicked":			self.on_replaceStartButton_clicked,
			"on_replaceAllButton_clicked":				self.on_replaceAllButton_clicked,
			"on_findCancelButton_clicked":				self.on_findCancelButton_clicked,
			"on_findClearButton_clicked":				self.on_findClearButton_clicked 
		}
		self.name = "findDialog"
		if self.gui.builder:
			self.gui.builder.add_from_file(self.gui.sharedir + "ui/findDialog.ui")
			self.gui.builder.connect_signals(callbacks)
			self.find_get_widget = self.gui.gui_get_widget
		else:
			self.xml = gtk.glade.XML(self.gui.gui_filename, self.name, domain="gjots2")
			self.xml.signal_autoconnect(callbacks)
			self.find_get_widget = self.xml.get_widget

		w = self.find_get_widget("caseCheckbutton")
		if w:
			w.set_active(self.gui.client.get_bool(self.gui.find_match_case_path))

		w = self.find_get_widget("globalCheckbutton")
		if w:
			w.set_active(self.gui.client.get_bool(self.gui.find_global_path))

		w = self.find_get_widget("regexCheckbutton")
		if w:
			w.set_active(self.gui.client.get_bool(self.gui.find_regex_path))

		w = self.find_get_widget("backwardsCheckbutton")
		if w:
			w.set_active(self.gui.client.get_bool(self.gui.find_backwards_path))

		w = self.find_get_widget("findEntry")
		if w:
			w.set_text(self.gui.client.get_string(self.gui.find_text_path))
			w.select_region(0, -1)

		w = self.find_get_widget("replaceEntry")
		if w:
			w.set_text(self.gui.client.get_string(self.gui.replace_text_path))
			
		self.feedback("")
		self._set_readonly(self.gui.readonly)
		
# find_dialog

# Local variables:
# eval:(setq compile-command "cd ..; ./gjots2 test.gjots")
# eval:(setq-default indent-tabs-mode 1)
# eval:(setq tab-width 4)
# eval:(setq python-indent 4)
# End:
