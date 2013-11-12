import gtk.keysyms
import gtk.glade
import re
import inspect
import tempfile
import pipes

class print_dialog:
	def destroy(self):
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.print_get_widget(self.name).destroy()

	def saveSettings(self):
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2]
		w = self.print_get_widget("printPageRadioButton")
		if w:
			self.gui.client.set_bool(self.gui.print_page_path, w.get_active())
		w = self.print_get_widget("printSelectionRadioButton")
		if w:
			self.gui.client.set_bool(self.gui.print_selection_path, w.get_active())
		w = self.print_get_widget("printAllRadioButton")
		if w:
			self.gui.client.set_bool(self.gui.print_all_path, w.get_active())

		w = self.print_get_widget("printPageFeedButton")
		if w:
			self.gui.client.set_bool(self.gui.print_page_feed_path, w.get_active())
		w = self.print_get_widget("printBoldTitlesButton")
		if w:
			self.gui.client.set_bool(self.gui.print_bold_title_path, w.get_active())

		w = self.print_get_widget("printCommandEntry")
		if w:
			self.gui.client.set_string(self.gui.print_command_path, w.get_text())
		
		return
	
	def on_printDialog_destroy(self, widget):
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2]
		return
	
	def on_printCommandEntry_key_press_event(self, widget, key_event):
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()

		# to get all keysyms: print gtk.keysyms.__dict__
		if key_event.keyval == gtk.keysyms.Return or key_event.keyval == gtk.keysyms.KP_Enter:
			self.on_printOKButton_clicked(widget)
		if key_event.keyval == gtk.keysyms.Escape:
			self.on_printCancelButton_clicked(widget)
		return

	def _get_settings(self):
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2]
		print_page = print_selection = print_all = page_feed = bold_titles = 0
		print_command = ""
		w = self.print_get_widget("printPageRadioButton")
		if w:
			print_page = w.get_active()
		if not print_page:
			w = self.print_get_widget("printSelectionRadioButton")
			if w:
				print_selection = w.get_active()
			if not print_selection:
				print_all = 1

		w = self.print_get_widget("printPageFeedButton")
		if w:
			page_feed = w.get_active()
		w = self.print_get_widget("printBoldTitlesButton")
		if w:
			bold_titles = w.get_active()

		w = self.print_get_widget("printCommandEntry")
		if w:
			print_command = w.get_text()
		
		return print_page, print_selection, print_all, page_feed, bold_titles, print_command
		
	def on_printOKButton_clicked(self, widget):
		"""
		if print_all is set then
			print all the pages
		else
			If print_page is set then
				print the page
			else
				if 1 tree item is selected then
					print the selected text
				else
					print all the selected pages.
		"""
		
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.gui.sync_text_buffer()
		self.saveSettings()
		print_page, print_selection, print_all, page_feed, bold_titles, print_command = self._get_settings()

		if print_all:
			this_iter = self.gui.get_root()
		else:
			this_iter = self.gui.get_first_selected_iter()
			
		if not this_iter:
			self.gui.msg(_("Nothing selected"))
			return
		
		last_selected = self.gui.get_last_selected_iter()
		if not last_selected:
			self.gui.msg(_("Nothing selected"))
			return

		t = pipes.Template()
		t.append(print_command, "-.")
		scratch = tempfile.mktemp()
		f = t.open(scratch, "w")

		single_page = 0
		if print_page or ( print_selection and self.gui.same_iter(this_iter, last_selected) ):
			single_page = 1
		while (1):
			if print_selection and single_page: 
				body, insertion_point, selection_bound = self.gui.get_selected_text()
			else:
				body = self.gui.get_node_value(this_iter)
			if body:
				f.write(body)
			if single_page:
				break
			if print_selection:
				if self.gui.same_iter(this_iter, last_selected):
					break
			this_iter = self.gui.get_linear_next(this_iter)
			if not this_iter:
				break
			if page_feed:
				f.write('')
		f.close()
		os.unlink(scratch)
		self.destroy()
		return
		
	def on_printCancelButton_clicked(self, widget):
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.destroy()
		return
	
	def __init__(self, gui):
		"""
		Print dialog
		"""

		self.gui = gui
		if self.gui.debug:
			print inspect.getframeinfo(inspect.currentframe())[2]

		callbacks = {
			"on_printDialog_destroy":					self.on_printDialog_destroy,
			"on_printCommandEntry_key_press_event":		self.on_printCommandEntry_key_press_event,
			"on_printOKButton_clicked":					self.on_printOKButton_clicked,
			"on_printCancelButton_clicked":				self.on_printCancelButton_clicked,
		}
		self.name = "printDialog"
		if self.gui.builder:
			self.gui.builder.add_from_file(self.gui.sharedir + "ui/printDialog.ui")
			self.gui.builder.connect_signals(callbacks)
			self.print_get_widget = self.gui.gui_get_widget
		else:
			self.xml = gtk.glade.XML(self.gui.gui_filename, self.name, domain="gjots2")
			self.xml.signal_autoconnect(callbacks)
			self.print_get_widget = self.xml.get_widget

		w = self.print_get_widget("printPageRadioButton")
		if w:
			w.set_active(self.gui.client.get_bool(self.gui.print_page_path))
		w = self.print_get_widget("printSelectionRadioButton")
		if w:
			w.set_active(self.gui.client.get_bool(self.gui.print_selection_path))
		w = self.print_get_widget("printAllRadioButton")
		if w:
			w.set_active(self.gui.client.get_bool(self.gui.print_all_path))

		w = self.print_get_widget("printPageFeedButton")
		if w:
			w.set_active(self.gui.client.get_bool(self.gui.print_page_feed_path))
		w = self.print_get_widget("printBoldTitlesButton")
		if w:
			w.set_active(self.gui.client.get_bool(self.gui.print_bold_title_path))

		w = self.print_get_widget("printCommandEntry")
		if w:
			w.set_text(self.gui.client.get_string(self.gui.print_command_path))
		return
		
# print_dialog

# Local variables:
# eval:(setq compile-command "cd ..; ./gjots2 test.gjots")
# eval:(setq-default indent-tabs-mode 1)
# eval:(setq tab-width 4)
# eval:(setq python-indent 4)
# End:
