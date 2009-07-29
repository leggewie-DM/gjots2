import gtk.keysyms
import gtk.glade
import re
import inspect

class find_dialog:
	def remove_tag(self):
		if self.hit_end != -1 and self.hit_start != -1:
			hit_start_iter = self.gui.textBuffer.get_iter_at_offset(self.start_offset + self.hit_start)
			hit_end_iter = self.gui.textBuffer.get_iter_at_offset(self.start_offset + self.hit_end)
			self.gui.textBuffer.remove_tag(self.found_tag, hit_start_iter, hit_end_iter)
		
	def destroy(self):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.xml.get_widget(self.name).destroy()
		self.remove_tag()
		
	def saveSettings(self):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		w = self.xml.get_widget("caseCheckbutton")
		if w:
			self.gui.client.set_bool(self.gui.find_match_case_path, w.get_active())

		w = self.xml.get_widget("globalCheckbutton")
		if w:
			self.gui.client.set_bool(self.gui.find_global_path, w.get_active())

		w = self.xml.get_widget("regexCheckbutton")
		if w:
			self.gui.client.set_bool(self.gui.find_regex_path, w.get_active())

		w = self.xml.get_widget("backwardsCheckbutton")
		if w:
			self.gui.client.set_bool(self.gui.find_backwards_path, w.get_active())

		w = self.xml.get_widget("findEntry")
		if w:
			self.gui.client.set_string(self.gui.find_text_path, w.get_text())

		w = self.xml.get_widget("replaceEntry")
		if w:
			self.gui.client.set_string(self.gui.replace_text_path, w.get_text())
		
		return
	
	def on_findDialog_destroy(self, widget):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		return
	
	def on_findEntry_key_press_event(self, widget, key_event):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()

		# to get all keysyms: print gtk.keysyms.__dict__
		if key_event.keyval == gtk.keysyms.Return or key_event.keyval == gtk.keysyms.KP_Enter:
			self.on_findStartButton_clicked(widget)
		if key_event.keyval == gtk.keysyms.Escape:
			self.on_findCancelButton_clicked(widget)
		return
	
	def on_replaceEntry_key_press_event(self, widget, key_event):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()
		if key_event.keyval == gtk.keysyms.Return or key_event.keyval == gtk.keysyms.KP_Enter:
			self.on_replaceStartButton_clicked(widget)
		if key_event.keyval == gtk.keysyms.Escape:
			self.on_findCancelButton_clicked(widget)
		return

	def _get_settings(self):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		match_case_bool = global_bool = regex_bool = backwards_bool = 0
		find_text = replace_text = ""
		w = self.xml.get_widget("caseCheckbutton")
		if w:
			match_case_bool = w.get_active()

		w = self.xml.get_widget("globalCheckbutton")
		if w:
			global_bool = w.get_active()

		w = self.xml.get_widget("regexCheckbutton")
		if w:
			regex_bool = w.get_active()

		w = self.xml.get_widget("backwardsCheckbutton")
		if w:
			backwards_bool = w.get_active()

		w = self.xml.get_widget("findEntry")
		if w:
			find_text = w.get_text()

		
		w = self.xml.get_widget("replaceEntry")
		if w:
			replace_text = w.get_text()

		return match_case_bool, global_bool, regex_bool, backwards_bool, find_text, replace_text
		
	def feedback(self, msg):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()
		w = self.xml.get_widget("findFeedback")
		if w:
			w.set_text(msg)
		return

	def _find_next(self):
		"""

		Returns textBuffer iters for the start and end the next match
		within the text from the "insert" mark and the end (or
		beginning ) of the element (or -1 if none).

		For regex matches, sets self.match

		May move to the next item in the tree if "global_bool" is set.

		Returns 1 if something found; else 0.

		"""
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]

		self.remove_tag()
		match_case_bool, global_bool, regex_bool, backwards_bool, find_text, replace_text = self._get_settings()
		self.hit_start = self.hit_end = -1
		use_textBuffer = 1
		current_tree_iter = self.gui.get_first_selected_iter()
		
		while self.hit_start == -1:
			if not use_textBuffer:
				if not global_bool:
					return 0
				# we need the next tree item
				current_tree_iter = self.gui.get_linear_next(current_tree_iter)
				if not current_tree_iter:
					return 0
				zone = self.gui.get_node_value(current_tree_iter)
				self.start_offset = 0
			else:
				start_mark = self.gui.textBuffer.get_insert()
				start_iter = self.gui.textBuffer.get_iter_at_mark(start_mark)
				end_iter = self.gui.textBuffer.get_end_iter()
				self.start_offset = start_iter.get_offset()
				zone = self.gui.textBuffer.get_text(start_iter, end_iter)
			
			if regex_bool:
				options = re.M | re.L
				if not match_case_bool:
					options = options | re.I
				try:
					self.prog = re.compile(find_text, options)
				except:
					self.gui.err_msg(_("Bad regular expression"))
					use_textBuffer = 0
					continue
				
				self.match = self.prog.search(zone)
				if self.match:
					self.hit_start = self.match.start()
					self.hit_end = self.match.end()
				else:
					use_textBuffer = 0
					continue
			else:
				if not match_case_bool:
					zone = zone.lower()
					find_text = find_text.lower()
				self.hit_start = zone.find(find_text)
				if self.hit_start < 0:
					use_textBuffer = 0
					continue
				self.hit_end = self.hit_start + len(find_text)

			# OK - we got one, now return:
			if not use_textBuffer:
				current_tree_path = self.gui.treestore.get_path(current_tree_iter)
				self.gui.treeView.expand_to_path(current_tree_path)
				self.gui.treeView.get_selection().unselect_all()
				self.gui.treeView.get_selection().select_iter(current_tree_iter)
				self.gui.treeView.scroll_to_cell(current_tree_path, None, 0, 0.5, 0.5)
			hit_start_iter = self.gui.textBuffer.get_iter_at_offset(self.start_offset + self.hit_start)
			hit_end_iter = self.gui.textBuffer.get_iter_at_offset(self.start_offset + self.hit_end)
			#self.gui.textBuffer.move_mark_by_name("selection_bound", hit_start_iter)
			self.gui.textBuffer.apply_tag(self.found_tag, hit_start_iter,
                hit_end_iter)	  
			self.gui.textBuffer.place_cursor(hit_end_iter)
			start_mark = self.gui.textBuffer.get_insert()
			self.gui.textView.scroll_to_mark(start_mark, 0.0 , 1, 1.0, 0.5)
			return 1
		
	def on_findStartButton_clicked(self, widget):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.gui.sync_text_buffer()
		self.saveSettings()
		self.feedback("")

		if not self._find_next():
			self.feedback(_("Not found"))
		else:
			self.feedback(_("Found"))

		w = self.xml.get_widget("findEntry")
		if w:
			w.grab_focus()

	def on_findCloseButton_clicked(self, widget):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.saveSettings()
		self.destroy()
		return
	
	def _replace_next(self):
		"""

		Returns 1 if something found; else 0

		"""
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.gui.sync_text_buffer()
		if self.hit_start == -1:
			return self._find_next()

		match_case_bool, global_bool, regex_bool, backwards_bool, find_text, replace_text = self._get_settings()
		
		hit_start_iter = self.gui.textBuffer.get_iter_at_offset(self.start_offset + self.hit_start)
		hit_end_iter = self.gui.textBuffer.get_iter_at_offset(self.start_offset + self.hit_end)
		if regex_bool:
			new_text = self.prog.sub(replace_text, self.gui.textBuffer.get_text(hit_start_iter, hit_end_iter))
		else:
			new_text = replace_text
		
		self.gui.textBuffer.place_cursor(hit_end_iter)
		self.gui.textBuffer.delete(hit_start_iter, hit_end_iter)
		self.gui.textBuffer.insert_at_cursor(new_text, len(new_text))
		# "insert" mark is now at the _end_ of the replaced text.
		# Now place the "selection" mark at the start of the replaced text:
		start_mark = self.gui.textBuffer.get_insert()
		start_iter = self.gui.textBuffer.get_iter_at_mark(start_mark)
		self.start_offset = start_iter.get_offset()
		new_selection_bound_iter = self.gui.textBuffer.get_iter_at_offset(self.start_offset - len(new_text))
		self.gui.textBuffer.move_mark_by_name("selection_bound", new_selection_bound_iter)
		#self.gui.dirty = 1 ... handled in on_textBuffer_changed()
		
		# now find the next one:
		return self._find_next()
	
	def on_replaceStartButton_clicked(self, widget):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.gui.sync_text_buffer()
		self.saveSettings()
		self.feedback("")

		if not self._replace_next():
			self.feedback(_("Not found"))
			return

		self.feedback(_("Replace?"))

		w = self.xml.get_widget("findEntry")
		if w:
			w.grab_focus()
		return
		
	def on_replaceAllButton_clicked(self, widget):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.gui.sync_text_buffer()
		self.saveSettings()
		total = 0
		i = 1
		while i:
			i = self._replace_next()
			total = total + i
		self.feedback(_("%d substitutions") % total)

		w = self.xml.get_widget("findEntry")
		if w:
			w.grab_focus()
		return
	
	def on_findCancelButton_clicked(self, widget):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.destroy()
		return
	
	def on_findClearButton_clicked(self, widget):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		w = self.xml.get_widget("findEntry")
		if w:
			w.set_text("")
			w.grab_focus()

		w = self.xml.get_widget("replaceEntry")
		if w:
			w.set_text("")
		return

	def _set_readonly(self, mode):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		if mode:
			w = self.xml.get_widget("replaceStartButton")
			w.hide()
			w = self.xml.get_widget("replaceEntry")
			w.hide()
			w = self.xml.get_widget("replaceLabel")
			w.hide()
			w = self.xml.get_widget("replaceAllButton")
			w.hide()
		else:
			w = self.xml.get_widget("replaceStartButton")
			w.show()
			w = self.xml.get_widget("replaceEntry")
			w.show()
			w = self.xml.get_widget("replaceLabel")
			w.show()
			w = self.xml.get_widget("replaceAllButton")
			w.show()
	
	def __init__(self, gui):
		"""
		Find dialog
		"""

		self.gui = gui
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]

		callbacks = {
			"on_findDialog_destroy":					self.on_findDialog_destroy,
			"on_findEntry_key_press_event":				self.on_findEntry_key_press_event,
			"on_replaceEntry_key_press_event":			self.on_replaceEntry_key_press_event,
			"on_findStartButton_clicked":				self.on_findStartButton_clicked,
			"on_findCloseButton_clicked":				self.on_findCloseButton_clicked,
			"on_replaceStartButton_clicked":			self.on_replaceStartButton_clicked,
			"on_replaceAllButton_clicked":				self.on_replaceAllButton_clicked,
			"on_findCancelButton_clicked":				self.on_findCancelButton_clicked,
			"on_findClearButton_clicked":				self.on_findClearButton_clicked 
		}
		self.name = "findDialog"
		self.xml = gtk.glade.XML(self.gui.gui_filename, self.name, domain="gjots2")
		self.xml.signal_autoconnect(callbacks)

		w = self.xml.get_widget("caseCheckbutton")
		if w:
			w.set_active(self.gui.client.get_bool(self.gui.find_match_case_path))

		w = self.xml.get_widget("globalCheckbutton")
		if w:
			w.set_active(self.gui.client.get_bool(self.gui.find_global_path))

		w = self.xml.get_widget("regexCheckbutton")
		if w:
			w.set_active(self.gui.client.get_bool(self.gui.find_regex_path))

		w = self.xml.get_widget("backwardsCheckbutton")
		if w:
			w.set_active(self.gui.client.get_bool(self.gui.find_backwards_path))

		w = self.xml.get_widget("findEntry")
		if w:
			w.set_text(self.gui.client.get_string(self.gui.find_text_path))
			w.select_region(0, -1)

		w = self.xml.get_widget("replaceEntry")
		if w:
			w.set_text(self.gui.client.get_string(self.gui.replace_text_path))
			
		self.feedback("")
		self._set_readonly(self.gui.readonly)
		self.hit_start = self.hit_end = -1
		self.found_tag = self.gui.textBuffer.create_tag(None,
														background="lightblue")
		
# find_dialog

# Local variables:
# eval:(setq compile-command "cd ..; ./gjots2 j")
# End:
