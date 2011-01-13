import gtk
import inspect

from common import *

class general_dialog:
	def destroy(self):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.xml.get_widget(self.name).destroy()

	def on_generalField1_key_press_event(self, widget, event):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		if event.keyval == 65307: # Escape
			self.generalValue = CANCEL;
			return 1

		if event.keyval == 65289: # tab
			if self.generalNumFields > 1:
				self.xml.get_widget("generalField2").grab_focus()
				return 1
			
		if event.keyval == 65421 or event.keyval == 65293: # KP_Enter / Return
			if self.generalNumFields > 1:
				#generalDialog = gtk_widget_get_toplevel(widget);
				self.xml.get_widget("generalField2").grab_focus()
			else:
				self.generalValue = OK;
			return 1
		return 0

	def on_generalField2_key_press_event(self, widget, event):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		if event.keyval == 65307: # Escape
			self.generalValue = CANCEL;
			return 1

		if event.keyval == 65289: # tab
			self.xml.get_widget("generalField1").grab_focus()
			return 1
			
		if event.keyval == 65421 or event.keyval == 65293: # KP_Enter / Return
			self.generalValue = OK;
			return 1
		return 0

	def on_generalOK_clicked(self, widget):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.generalValue = OK

	def on_generalNo_clicked(self, widget):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.generalValue = NO

	def on_generalCancel_clicked(self, widget):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.generalValue = CANCEL

	def on_generalTryagain_clicked(self, widget):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.generalValue = TRYAGAIN

	def on_generalReadonly_clicked(self, widget):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		self.generalValue = READONLY

	def get_field1(self):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		return self.field1

	def get_field2(self):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		return self.field2

	def get_value(self):
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2]
		return self.generalValue
	
	def __init__(self, gui, title, prompt, buttons, num_fields = 0, secretp = 0, feedback = "",
				 field1_label = "", field1_default = "",
				 field2_label = "", field2_default = ""):
		self.gui = gui
		if self.gui.trace:
			print inspect.getframeinfo(inspect.currentframe())[2], vars()

		callbacks = {

			# General popup:
			"on_generalField1_key_press_event":			self.on_generalField1_key_press_event,
			"on_generalField2_key_press_event":			self.on_generalField2_key_press_event,
			"on_generalOK_clicked":						self.on_generalOK_clicked,
			"on_generalNo_clicked":						self.on_generalNo_clicked,
			"on_generalCancel_clicked":					self.on_generalCancel_clicked,
			"on_generalTryagain_clicked":				self.on_generalTryagain_clicked,
			"on_generalReadonly_clicked":				self.on_generalReadonly_clicked,
		}
		self.field1 = field1_default
		self.field2 = field2_default
		self.generalNumFields = num_fields
		self.name = "generalDialog"

		self.gui_filename = gui.gui_filename
		self.xml = gtk.glade.XML(self.gui_filename, self.name, domain="gjots2")
		self.xml.signal_autoconnect(callbacks)

		#gtk.Widget.show(self)
		self.xml.get_widget(self.name).set_transient_for(self.gui.gjots)
		self.xml.get_widget(self.name).set_title(title)
		self.xml.get_widget("generalPromptLabel").set_label(prompt)
		if num_fields < 1:
			self.xml.get_widget("generalLabel1").hide()
			self.xml.get_widget("generalField1").hide()
		else:
			self.xml.get_widget("generalLabel1").set_label(field1_label)
			self.xml.get_widget("generalLabel1").show()
			self.xml.get_widget("generalField1").set_text(field1_default)
			self.xml.get_widget("generalField1").set_visibility(not secretp)
			self.xml.get_widget("generalField1").show()
			
		if num_fields < 2:
			self.xml.get_widget("generalLabel2").hide()
			self.xml.get_widget("generalField2").hide()
		else:
			self.xml.get_widget("generalLabel2").set_label(field2_label)
			self.xml.get_widget("generalLabel2").show()
			self.xml.get_widget("generalField2").set_text(field2_default)
			self.xml.get_widget("generalField2").set_visibility(not secretp)
			self.xml.get_widget("generalField2").show()

		if feedback:
			self.xml.get_widget("generalFeedback").set_label(feedback)
			self.xml.get_widget("generalFeedback").show()
		else:
			self.xml.get_widget("generalFeedback").hide()

		if (buttons & YES or buttons & OK):
			self.xml.get_widget("generalOK").show()
			if (buttons & YES):
				self.xml.get_widget("generalOK").set_label(_("Yes"))
		else:
			self.xml.get_widget("generalOK").hide()
			
		if (buttons & NO):
			self.xml.get_widget("generalNo").show()
		else:
			self.xml.get_widget("generalNo").hide()

		if (buttons & CANCEL):
			self.xml.get_widget("generalCancel").show()
		else:
			self.xml.get_widget("generalCancel").hide()
			
		if (buttons & READONLY):
			self.xml.get_widget("generalReadonly").show()
		else:
			self.xml.get_widget("generalReadonly").hide()
			
		if (buttons & TRYAGAIN):
			self.xml.get_widget("generalTryagain").show()
		else:
			self.xml.get_widget("generalTryagain").hide()
			
		self.generalValue = WAITING

		while self.generalValue == WAITING:
			gtk.main_iteration()

		if self.generalValue == OK:
			if num_fields > 1:
				self.field2 = self.xml.get_widget("generalField2").get_text()
			if num_fields > 0:
				self.field1 = self.xml.get_widget("generalField1").get_text()

		self.xml.get_widget(self.name).destroy()

# Local variables:
# eval:(setq compile-command "cd ..; ./gjots2 test.gjots")
# eval:(setq-default indent-tabs-mode 1)
# eval:(setq tab-width 4)
# eval:(setq python-indent 4)
# End:
