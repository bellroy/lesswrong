if (typeof Protoplasm == 'undefined')
	throw('protoplasm.js not loaded, could not intitialize rte');
if (typeof Control == 'undefined') Control = {};

Protoplasm.use('colorpicker');
Protoplasm.use('filechooser');
Protoplasm.loadStylesheet('rte.css', 'rte');

/**
 * class Control.RTE
 *
 * An in-browser WYSIWYG rich text editor for IE 6+, Firefox 1.0+.
 * Designed for AJAX applications based on the Prototype library.
 *
 * Features:
 *  - Lightweight & easy to use - doesn't try to be a Word replacement
 *  - Can be created/destroyed on the fly, to function in an constantly 
 *    changing page environment (TinyMCE et. al. fail miserably here)
 *  - Use external hooks for showing directory lists for
 *    inserting images
 *
 * Example: <a href="http://jongsma.org/software/protoplasm/control/rte">Rich
 * Text Editor demo</a>
**/
Control.RTE = Class.create();

Object.extend(Control.RTE, {

	activeEditor: null,
	useEffects: false,
	dialogElement: null,
	includePath: null,
	initialized: false,
	editors: {},

	// Load things that are only needed on the page if at least one
	// editor is created
	init: function() {
		if (!Control.RTE.initialized) {
			Control.RTE.Dialog.cache = {
				ColorPalette: new Control.RTE.Dialog.ColorPalette(),
				InsertLink: new Control.RTE.Dialog.InsertLink(),
				ImageBrowser: new Control.RTE.Dialog.ImageBrowser(),
				InsertTable: new Control.RTE.Dialog.InsertTable()
			}
		}
	},

	// Shortcut to create an element with all attributes, classes and styles
	createElement: function(type, attributes, className, styles) {
		var elt = null;
		try {
			elt = document.createElement(type);
			if (attributes)
				for (att in attributes)
					elt.setAttribute(att, attributes[att]);
			if (className)
				elt.className = className;
			if (styles)
				Element.setStyle(elt, styles);
		} catch(e) {
			alert('Could not create element.');
		}
		return elt;
	}
});

Control.RTE.prototype = {

	initialize: function(textarea, options) {
		if (!Control.RTE.initialized) Control.RTE.init();

		this.textarea = $(textarea);

		if (ta = this.textarea.retrieve('editor'))
			ta.destroy();

		this.options = options || {};

		// Set global include path
		if (this.options.includePath) {
			if (!/\/$/.test(this.options.includePath))
				this.options.includePath += '/';
			Control.RTE.includePath = this.options.includePath || '';
		} else {
			Control.RTE.includePath = Protoplasm.base('rte')+'images/';
		}

		this.toolbarStyle = this.options.toolbarStyle;
		this.useXHTML = this.options.useXHTML;
		this.fileLister = this.options.fileLister;
		this.editorCss = this.options.editorCss;
		this.disableSourceView = this.options.disableSourceView;

		this.editorDiv = null;
		this.toolbar = null;
		this.iframe = null;
		this.iframeDiv = null;

		this.isEnabled = false;
		this.sourceCheckbox = null;
		this.inSourceView = false;
		this.activeDialog = null;
		this.selectedRange = null;

		// Event listeners
		this.keyPressListener = this.keyPressHandler.bindAsEventListener(this);
		this.cancelKeyPressListener = this.cancelKeyPressHandler.bindAsEventListener(this);
		this.keyUpListener = this.keyUpHandler.bindAsEventListener(this);
		this.clickListener = this.updateToolbarState.bindAsEventListener(this);
		this.closeDialogListener = this.closeDialog.bindAsEventListener(this);
		this.escKeyListener = this.escKeyPressed.bindAsEventListener(this);
		this.iframeTabListener = this.tabKeyPressed.bindAsEventListener(this);
		this.focusListener = this.focus.bindAsEventListener(this);
		this.changeListener = this.syncToEditor.bindAsEventListener(this);
		this.submitListener = function(e) {
				this.syncToTextarea();
				return true;
			}.bindAsEventListener(this);

		// Browser check
		var ua = navigator.userAgent.toLowerCase();
		this.isIE = ((ua.indexOf("msie") != -1) && (ua.indexOf("opera") == -1) && (ua.indexOf("webtv") == -1)); 
		this.isGecko = (ua.indexOf("gecko") != -1);
		//this.isSafari = (ua.indexOf("safari") != -1);
		//this.isKonqueror = (ua.indexOf("konqueror") != -1);

		// Check for design-mode capable browsers and create editor
		//if (document.getElementById && document.designMode && !this.isSafari && !this.isKonqueror)
		this.createEditor();
		this.destructor = Event.on(window, 'unload', this.destroy.bind(this));
		
	},

	createEditor: function() {
		var container = this.textarea.parentNode;
		var width = this.textarea.offsetWidth
			? this.textarea.offsetWidth + 'px'
			: this.textarea.style.width;
		var height = this.textarea.offsetHeight
			? this.textarea.offsetHeight + 'px'
			: this.textarea.style.height;

		var editor = document.createElement('div');
		if (width)
			editor.style.width = width;

		// Create it here
		this.toolbar = new Control.RTE.Toolbar(this, this.toolbarStyle);
		if (this.options.variables) {
			this.toolbar.add(new Control.RTE.ToolbarLineBreak());
			this.toolbar.add(new Control.RTE.ToolbarVariableList('varlist',
					this.options.variables,
					'Insert Field',
					this.options.variableClass));
		}

		var frameDiv = document.createElement('div');
		frameDiv.className = 'rteEditor';
		this.iframeDiv = frameDiv;

		var footer = document.createElement('div');
		// FIXME: use stylesheet?
		footer.style.borderTop = '1px solid #999999';

		if (!this.disableSourceView) {
			footer.className = 'rteFooter';
			var checkbox = document.createElement('input');
			checkbox.type = 'checkbox';
			checkbox.id = this.textarea.name + '_viewsource';
			checkbox.onclick = this.toggleSourceView.bindAsEventListener(this);
			this.sourceCheckbox = checkbox;
			footer.appendChild(checkbox);
			var label = document.createElement('label');
			label.htmlFor = checkbox.id;
			label.innerHTML = 'View HTML Source - ';
			footer.appendChild(label);
			clearFormatting = document.createElement('span');
			clearFormatting.onclick = function(e) {
					if (confirm('Are you sure you want to clear all text formatting?'))
						this.clearFormatting();
					return false;
				}.bindAsEventListener(this);
			clearFormatting.innerHTML = 'Clear All Formatting';
			clearFormatting.style.textDecoration = 'underline';
			clearFormatting.style.color = 'blue';
			clearFormatting.style.cursor = 'pointer';
			footer.appendChild(clearFormatting);
		}

		// Create editor window
		editor.appendChild(this.toolbar.element);
		editor.appendChild(frameDiv);
		editor.appendChild(footer);
		this.editorDiv = editor;

		Element.hide(this.textarea);
		container.insertBefore(editor, this.textarea);
	
		// Create IFRAME
		var frame = document.createElement('iframe');
		frame.width = '100%';
		if (height) {
			if (editor.offsetHeight > 0)
				frame.height = parseInt(height) - editor.offsetHeight;
			else
				frame.height = parseInt(height) - 83;
		}
		frame.style.border = 0;
		frame.style.margin = 0;

		this.iframe = frame;
		frameDiv.appendChild(frame);

		this.createEditDoc();

		// Close dialogs when close are encountered outside of the toolbar
		Event.observe(this.getIframeWindow().document, 'click', this.closeDialogListener);
		Event.observe(document, 'keypress', this.escKeyListener);
		Control.RTE.activeEditor = this;

		// Set tab indexes
		if (document.all) {
			// IE respects iframe tabindexes
			this.iframe.tabIndex = this.textarea.tabIndex;
		} else {
			// Firefox needs some help with tabs
			var i;
			var elements = this.textarea.form.elements;
			for (i = 0; i < elements.length; ++i) {
				if (elements[i] == this.textarea) break;
				if (!elements[i].hidden) this.prevElement = elements[i];
			}
			if (elements.length > i + 1) this.nextElement = elements[i + 1];

			if (this.prevElement)
				Event.observe(this.prevElement, 'keypress', function(e) {
						if (e.keyCode == Event.KEY_TAB && !e.shiftKey) {
							this.focus();
							return false;
						}
					}.bindAsEventListener(this));
			if (this.nextElement)
				Event.observe(this.nextElement, 'keypress', function(e) {
						if (e.keyCode == Event.KEY_TAB && e.shiftKey) {
							this.focus();
							return false;
						}
					}.bindAsEventListener(this));

			Event.observe(this.getIframeWindow().document, 'keypress', this.iframeTabListener, true);
		}
		Event.observe(this.textarea, 'change', this.changeListener);
		Event.observe(this.textarea, 'focus', this.focusListener);
		Event.observe(this.textarea.form, 'submit', this.submitListener);
		this.textarea.store('editor', this);
		return true;
	},

	tabKeyPressed: function(e) {
		if (e.keyCode == Event.KEY_TAB) {
			this.moveFocus(e.shiftKey ? this.prevElement : this.nextElement);
			Event.stop(e);
		}
	},

	focus: function(e) {
		// WHY WON'T THIS FUCKING WORK
		this.textarea.blur();
		this.getIframeWindow().focus();
	},

	moveFocus: function(element) {
		if (element) {
			if (element.editor) element.editor.focus.bind(element.editor)();
			else element.focus();
		}
	},

	destroy: function() {
		// Remove event listeners to prevent memory leaks
		Event.stopObserving(document, 'keypress', this.escKeyListener);
		Event.stopObserving(this.textarea.form, 'submit', this.submitListener);
		Event.stopObserving(this.textarea, 'change', this.changeListener);
		Event.stopObserving(this.textarea, 'focus', this.focusListener);
		var doc = this.getIframeWindow().document;
		Event.stopObserving(doc, 'keypress', this.iframeTabListener, true);
		Event.stopObserving(doc, 'click', this.closeDialogListener);
		Event.stopObserving(doc, 'keypress', this.keyPressListener, true);
		Event.stopObserving(doc, 'keyup', this.keyUpListener, true);
		Event.stopObserving(doc, 'click', this.clickListener, true);

		// Clean up HTML elements
		Element.remove(this.editorDiv);
		this.editorDiv = null;
		this.iframe = null;
		this.sourceCheckbox = null;

		this.destructor.stop();

		// Restore textarea
		this.textarea.store('editor', null);
		Element.show(this.textarea);
	},

	enable: function() {
		if (!this.isEnabled) {
			try {
				var doc = this.iframe.contentWindow.document;
				doc.designMode = 'On';
				this.toolbar.enable();
				this.updateToolbarState();
				// Add event handlers
				Event.stopObserving(doc, 'keypress', this.cancelKeyPressListener, true);
				Event.observe(doc, 'keypress', this.keyPressListener, true);
				Event.observe(doc, 'keyup', this.keyUpListener, true);
				Event.observe(doc, 'click', this.clickListener, true);
				if (this.sourceCheckbox)
					this.sourceCheckbox.disabled = false;
				this.isEnabled = true;
			} catch (e) {
				// If element is not visible or is still rendering, Gecko won't
				// enable design mode, so keep trying
				if (this.isGecko) setTimeout(this.enable.bind(this), 10);
				return false;
			}
		}
	},

	disable: function() {
		if (this.isEnabled) {
			var doc = this.iframe.contentWindow.document;
			doc.designMode = 'Off';
			this.toolbar.disable();
			// Remove event handlers
			Event.stopObserving(doc, 'keypress', this.keyPressListener, true);
			Event.stopObserving(doc, 'keyup', this.keyUpListener, true);
			Event.stopObserving(doc, 'click', this.clickListener, true);
			Event.observe(doc, 'keypress', this.cancelKeyPressListener, true);
			if (this.sourceCheckbox)
				this.sourceCheckbox.disabled = true;
			this.isEnabled = false;
		}
	},
	
	createEditDoc: function() {
		var doc = this.iframe.contentWindow.document;
		doc.open();
		doc.write(this.getEditorDoc(this.markupVariables(this.textarea.value), this.editorCss));
		doc.close();
		this.enable();
	},

	updateToolbarState: function() {
		this.toolbar.refresh();
	},

	clearSelection: function() {
		var win = this.getIframeWindow();
		if (document.all) {
			var selection = win.document.selection; 
			selection.empty();
		} else {
			var selection = win.getSelection();
			selection.removeAllRanges();
		}
		this.selectedRange = null;
	},

	getSelectedText: function() {
		if (this.selectedRange) {
			if (this.isIE)
				return new String(this.selectedRange.htmlText).stripTags();
			else {
				return this.selectedRange.toString().stripTags();
			}
		}
		return '';
	},
	
	closeDialog: function(e) {
		Control.RTE.Dialog.destroyActive();
	},

	showDialog: function(type, e) {
		if (this.activeDialog == type) {
			Control.RTE.Dialog.closeActive();
			return;
		}

		// Save selected range before leaving to prevent losing selection
		var win = this.getIframeWindow();
		if (document.all) {
			var selection = win.document.selection; 
			if (selection)
				this.selectedRange = selection.createRange();
		} else {
			var selection = win.getSelection();
			if (selection && selection.rangeCount > 0)
				this.selectedRange = selection.getRangeAt(selection.rangeCount - 1).cloneRange();
		}

		switch(type) {
			case 'textcolor':
			case 'bgcolor':
				Control.RTE.Dialog.activate('ColorPalette', this, Event.element(e));
				break;
			case 'link':
				Control.RTE.Dialog.activate('InsertLink', this, Event.element(e));
				break;
			case 'image':
				Control.RTE.Dialog.activate('ImageBrowser', this, null, { fileLister: this.fileLister });
				break;
			case 'table':
				Control.RTE.Dialog.activate('InsertTable', this, Event.element(e));
				break;
			default:
				new Control.RTE.Dialog(this, Event.element(e));
		}

		Control.RTE.activeEditor = this;
		this.activeDialog = type;
	},

	setDialogColor: function(color) {
		if (document.all && this.selectedRange)
			this.selectedRange.select();

		if (this.activeDialog == 'textcolor')
			this.doCommand('forecolor', color);
		else {
			if (document.all)
				this.doCommand('backcolor', color);
			else
				this.doCommand('hilitecolor', color);
		}
		//this.clearSelection();
		setTimeout(Control.RTE.Dialog.closeActive);
	},

	insertHtml: function(html) {
		var win = this.getIframeWindow();
		win.focus();
		if (document.all) {
			if (this.selectedRange) {
				this.selectedRange.pasteHTML(html);
				this.selectedRange.collapse(false);
				this.selectedRange.select();
			} else {
			}
		} else {
			win.document.execCommand('insertHTML', false, html);
		}
		setTimeout(Control.RTE.Dialog.closeActive);
	},

	getIframeWindow: function() {
		//if (document.all) return this.iframe;
		//else return this.iframe.contentWindow;
		return this.iframe.contentWindow;
	},

	doCommand: function(command, option) {
		clearTimeout(this.syncTimeout);
		var cw = this.getIframeWindow();
		try {
			cw.focus();
			cw.document.execCommand(command, false, option);
			cw.focus();
		} catch (e) {
			return false;
		}
		this.updateToolbarState();
		this.syncTimeout = setTimeout(this.syncToTextarea.bind(this), 1000);
		return true;
	},

	debug: function(message) {
		if (!this.debugElement) {
			var dl = document.createElement('div');
			dl.style.position = 'absolute';
			dl.style.top = 0;
			dl.style.width = '100%';
			dl.style.backgroundColor = '#FFFFCC';
			dl.style.MozOpacity = '.8';
			dl.style.height = '125px';
			dl.style.overflow = 'auto';
			dl.style.fontFamily = 'monospace';
			dl.style.borderBottom = '1px solid black';
			this.debugElement = dl;
			document.body.appendChild(this.debugElement);
			window.onscroll = function() { dl.style.top = window.pageYOffset + 'px'; };
		}
		this.debugElement.appendChild(document.createTextNode(message));
		this.debugElement.appendChild(document.createElement('br'));
		if (this.debugElement.scrollHeight > 125)
			this.debugElement.scrollTop = this.debugElement.scrollHeight - 125;
	},

	checkCommand: function(command) {
		var cw = this.getIframeWindow();
		try {
			return cw.document.queryCommandState(command);
		} catch (e) {
			return false;
		}
	},

	checkCommandValue: function(command) {
		var cw = this.getIframeWindow();
		try {
			return cw.document.queryCommandValue(command);
		} catch (e) {
			return false;
		}
	},

	commandEnabled: function(command) {
		var cw = this.getIframeWindow();
		try {
			return cw.document.queryCommandEnabled(command);
		} catch (e) {
			return false;
		}
	},

	getEditorDoc: function(html, cssUrl) {
		var frameHtml = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n';
		frameHtml += '<html>\n'
		frameHtml += '<head>\n';
		if (cssUrl) {
			frameHtml += '<link media="all" type="text/css" href="' + cssUrl + '" rel="stylesheet">\n';
		} else {
			frameHtml += '<style type="text/css">\n';
			frameHtml += 'body {\n';
			frameHtml += '	background: #FFFFFF;\n';
			frameHtml += '	margin: 2px;\n';
			frameHtml += '	padding: 2px;\n';
			frameHtml += '	font-family: sans-serif;\n';
			frameHtml += '	font-size: 10pt;\n';
			frameHtml += '}\n';
			frameHtml += '</style>\n';
		}
		frameHtml += '<style type="text/css">\n';
		frameHtml += 'body.source {\n';
		frameHtml += '  white-space: pre;\n';
		frameHtml += '  font-family: monospace;\n';
		frameHtml += '  background-color: #FFFFDD;\n';
		frameHtml += '}\n';
		frameHtml += '</style>\n';
		frameHtml += '</head>\n';
		frameHtml += '<body>\n';
		frameHtml += html + '\n';
		frameHtml += '</body>\n';
		frameHtml += '</html>';
		return frameHtml;
	},

	toggleSourceView: function(e) {
		var showSource = this.sourceCheckbox.checked;
		var win = this.getIframeWindow();
		var doc = win.document;
		this.syncToTextarea();
		if (showSource && !this.inSourceView) {
			this.inSourceView = true;
			this.toolbar.disable();
			if (this.isGecko)
				doc.body.className = 'source';
			this.syncToEditor();
		} else if (!showSource && this.inSourceView) {
			this.inSourceView = false;
			// This line causes IE to lock up HARD, so we just won't change styles
			if (this.isGecko)
				doc.body.className = '';
			if (this.isEnabled)
				this.toolbar.enable();
			this.syncToEditor();
		}
		win.focus();
	},

	escKeyPressed: function(e) {
		if (e.keyCode == Event.KEY_ESC)
			Control.RTE.Dialog.destroyActive();
	},

	keyPressHandler: function(e) {
		if (this.isGecko && e.ctrlKey) {
			var key = String.fromCharCode(e.charCode).toLowerCase();
			var command = null;
			switch (key) {
				case 'b': command = "bold"; break;
				case 'i': command = "italic"; break;
				case 'u': command = "underline"; break;
			};

			if (command) {
				this.doCommand(command, false, null);
				this.updateToolbarState();
				Event.stop(e);
			}
		}
	},

	cancelKeyPressHandler: function(e) {
		Event.stop(e);
	},

	keyUpHandler: function(e) {
		// Refresh toolbar if user moved to a different text block
		clearTimeout(this.syncTimeout);
		if (e.keyCode == Event.KEY_DOWN
				|| e.keyCode == Event.KEY_UP
				|| e.keyCode == Event.KEY_LEFT
				|| e.keyCode == Event.KEY_RIGHT
				|| e.keyCode == Event.KEY_RETURN
				|| e.keyCode == 33 // PgUp
				|| e.keyCode == 34 // PgDn
				|| e.keyCode == 35 // End
				|| e.keyCode == 36 // Home
				) {
			this.updateToolbarState();
		}
		this.syncTimeout = setTimeout(this.syncToTextarea.bind(this), 1000);
	},

	markupVariables: function(text) {
		if (this.options.variableClass && this.options.variableExpression) {
			var re = new RegExp('(' + this.options.variableExpression + ')', 'gm');
			text = text.replace(re, '<span class="' + this.options.variableClass + '">$1</span>');
		}
		return text;
	},

	unmarkupVariables: function(text) {
		if (this.options.variableClass) {
			var re = new RegExp('<span class="' + this.options.variableClass + '">([^<]*)</span>', 'gm');
			text = text.replace(re, '$1');
		}
		return text;
	},

	setText: function(text) {
		this.textarea.value = text;
		this.syncToEditor();
	},

	getText: function() {	
		if (this.isEnabled)
			this.syncToTextarea();
		return this.textarea.value;
	},

	syncToTextarea: function() {
		clearTimeout(this.syncTimeout);
		var text = this.getNodeText(this.getIframeWindow().document.body, !this.inSourceView);
		text = this.unmarkupVariables(text);
		this.textarea.value = this.trimWhitespace(this.escapeText(text));
	},

	getNodeText: function(node, source) {
		var text;
		if (!source) {
			if (document.all) {
				//fix for IE
				text = escape(node.innerText);
				text = text.replace("%3CP%3E%0D%0A%3CHR%3E", "%3CHR%3E");
				text = unescape(text.replace("%3CHR%3E%0D%0A%3C/P%3E", "%3CHR%3E"));
			} else {
				var htmlSrc = node.ownerDocument.createRange();
				htmlSrc.selectNodeContents(node);
				text = htmlSrc.toString();
			}
			if (this.useXHTML) {
				var anonDiv = document.createElement('div');
				anonDiv.innerHTML = text;
				text = get_xhtml(anonDiv);
			}
		} else {
			if (this.useXHTML)
				text = get_xhtml(node);
			else
				text = node.innerHTML;
		}
		return text;
	},

	// Fix quotes, special characters and newlines
	escapeText: function(text) {
		for (var i = 0; i < text.length; ++i) {
			var cc = text.charCodeAt(i);
			// Remove CRLF
			if (cc == 13)
				text = text.substring(0, i).concat(text.substring(i + 1, text.length));
			else if (cc > 128) {
				if (cc == 39 || cc == 145 || cc == 146 || cc == 8217 || cc == 8216)
					text = text.substring(0, i).concat('&apos;', text.substring(i + 1, text.length));
				else if (cc == 34 || cc == 147 || cc == 148 || cc == 8220 || cc == 8221)
					text = text.substring(0, i).concat('&quot;', text.substring(i + 1, text.length));
				else if (cc == 150 || cc == 8211)
					text = text.substring(0, i).concat('-', text.substring(i + 1, text.length));
				else if (cc == 153 || cc == 8482)
					text = text.substring(0, i).concat('&trade;', text.substring(i + 1, text.length));
				else
					text = text.substring(0, i).concat('&#', String(cc), ';', text.substring(i + 1, text.length));
			}
		}
		return text;
	},

	trimWhitespace: function(text) {
		var start = 0;
		var end = -1;
		for (var i = 0; i < text.length; ++i) {
			var c = text.charCodeAt(i);
			switch(text.charCodeAt(i)) {
				case 32:
				case 8:
				case 10:
				case 13:
					if (end == -1) start = i + 1;
					break;
				default:
					end = i;
			}
		}
		if (end == -1) return '';
		return text.substr(start, (end + 1) - start);
	},

	clearFormatting: function() {
		var cont = document.createElement('div');
		cont.innerHTML = this.getText();
		// Recurse through nodes and remove all tags but <img> and <br>
		this.removeNodeFormatting(cont);
		this.textarea.value = this.getNodeText(cont, !this.inSourceView);
		this.syncToEditor();
	},

	removeNodeFormatting: function(node) {
		if (node.childNodes.length > 0) {
			for (var i = 0; i < node.childNodes.length; ++i) {
				var cn = node.childNodes[i];
				if (cn.nodeType == 1) {
					this.removeNodeFormatting(cn);
					switch (cn.nodeName.toLowerCase()) {
						case 'p':
						case 'br':
						case 'img':
						case 'a':
							break; // Keep these
						default:
							i += cn.childNodes.length - 1;
							while(cn.firstChild)
								node.insertBefore(cn.firstChild, cn);
							node.removeChild(cn);
					}
				}
			}
		}
	},

	syncToEditor: function() {
		var doc = this.getIframeWindow().document;
		if (this.inSourceView) {
			if (document.all) {
				doc.body.innerText = this.textarea.value;
			} else {
				var htmlSrc = doc.createTextNode(this.textarea.value);
				doc.body.innerHTML = "";
				doc.body.appendChild(htmlSrc);
			}
		} else {
			// If sync occurs before iframe has initialized, we'll get an error
			doc.body.innerHTML = this.markupVariables(this.textarea.value);
		}
	}

};

/*
 * TOOLBARS
 */

Control.RTE.Toolbar = Class.create();
Object.extend(Control.RTE.Toolbar.prototype, {
	initialize: function(editor, layout) {
		this.editor = editor;
		this.items = [];

		this.element = document.createElement('div');
		this.element.className = 'rteToolbar';

		this.addLayout(layout);
	},
	add: function(item) {
		item.toolbar = this;
		this.items.push(item);
		this.element.appendChild(item.element);
	},
	addSeparator: function() {
		this.add(new Control.RTE.ToolbarSeparator());
	},
	addLineBreak: function() {
		this.add(new Control.RTE.ToolbarLineBreak());
	},
	disable: function() {
		this.disabled = true;
		Element.addClassName(this.element, 'rteToolbarDisabled');
		this.items.each(function(item) { item.disable(); });
	},
	enable: function() {
		this.disabled = false;
		Element.removeClassName(this.element, 'rteToolbarDisabled');
		this.items.each(function(item) { item.enable(); });
	},
	refresh: function() {
		if (!this.toolbarRefreshing) {
			this.toolbarRefreshing = true;
			this.items.each(function(item) { item.refresh(); });
			if (this.toolbarNeedsRefresh)
				this.refresh();
			this.toolbarRefreshing = false;
			this.toolbarNeedsRefresh = false;
		} else {
			this.toolbarNeedsRefresh = true;
		}
	},
	addLayout: function(layout) {
		if (layout == 'simple') {
			this.add(Control.RTE.ToolbarButton.BOLD());
			this.add(Control.RTE.ToolbarButton.ITALIC());
			this.add(Control.RTE.ToolbarButton.UNDERLINE());
			this.add(new Control.RTE.ToolbarSeparator());
			this.add(Control.RTE.ToolbarButton.UNDO());
			this.add(Control.RTE.ToolbarButton.REDO());
		} else if (layout == 'html') {
			this.add(Control.RTE.ToolbarButton.BOLD());
			this.add(Control.RTE.ToolbarButton.ITALIC());
			this.add(Control.RTE.ToolbarButton.UNDERLINE());
			this.add(new Control.RTE.ToolbarSeparator());
			this.add(Control.RTE.ToolbarButton.UNDO());
			this.add(Control.RTE.ToolbarButton.REDO());
			this.add(new Control.RTE.ToolbarSeparator());
			this.add(Control.RTE.ToolbarButton.TEXT_COLOR());
			this.add(Control.RTE.ToolbarButton.BACKGROUND_COLOR());
			this.add(new Control.RTE.ToolbarSeparator());
			this.add(Control.RTE.ToolbarButton.INSERT_LINK());
			this.add(Control.RTE.ToolbarButton.INSERT_IMAGE());
		} else if (layout == 'advanced') {
			this.add(Control.RTE.ToolbarButton.BOLD());
			this.add(Control.RTE.ToolbarButton.ITALIC());
			this.add(Control.RTE.ToolbarButton.UNDERLINE());
			this.add(new Control.RTE.ToolbarSeparator());
			this.add(Control.RTE.ToolbarButton.LEFT_JUSTIFY());
			this.add(Control.RTE.ToolbarButton.CENTER_JUSTIFY());
			this.add(Control.RTE.ToolbarButton.RIGHT_JUSTIFY());
			this.add(Control.RTE.ToolbarButton.FULL_JUSTIFY());
			this.add(new Control.RTE.ToolbarSeparator());
			this.add(Control.RTE.ToolbarButton.UNDO());
			this.add(Control.RTE.ToolbarButton.REDO());
			this.add(new Control.RTE.ToolbarSeparator());
			this.add(Control.RTE.ToolbarButton.HORIZONTAL_RULE());
			this.add(new Control.RTE.ToolbarSeparator());
			this.add(Control.RTE.ToolbarButton.ORDERED_LIST());
			this.add(Control.RTE.ToolbarButton.UNORDERED_LIST());
			this.add(Control.RTE.ToolbarButton.OUTDENT());
			this.add(Control.RTE.ToolbarButton.INDENT());
			this.add(new Control.RTE.ToolbarSeparator());
			this.add(Control.RTE.ToolbarButton.TEXT_COLOR());
			this.add(Control.RTE.ToolbarButton.BACKGROUND_COLOR());
			this.add(new Control.RTE.ToolbarSeparator());
			this.add(Control.RTE.ToolbarButton.INSERT_LINK());
			this.add(Control.RTE.ToolbarButton.INSERT_IMAGE());
			this.add(Control.RTE.ToolbarButton.INSERT_TABLE());
		} else {
			this.add(Control.RTE.ToolbarButton.FONT_FACE());
			this.add(Control.RTE.ToolbarButton.FONT_SIZE());
			this.add(Control.RTE.ToolbarButton.BLOCK_STYLE());
			this.add(new Control.RTE.ToolbarLineBreak());
			this.add(Control.RTE.ToolbarButton.BOLD());
			this.add(Control.RTE.ToolbarButton.ITALIC());
			this.add(Control.RTE.ToolbarButton.UNDERLINE());
			this.add(new Control.RTE.ToolbarSeparator());
			this.add(Control.RTE.ToolbarButton.LEFT_JUSTIFY());
			this.add(Control.RTE.ToolbarButton.CENTER_JUSTIFY());
			this.add(Control.RTE.ToolbarButton.RIGHT_JUSTIFY());
			this.add(Control.RTE.ToolbarButton.FULL_JUSTIFY());
			this.add(new Control.RTE.ToolbarSeparator());
			this.add(Control.RTE.ToolbarButton.UNDO());
			this.add(Control.RTE.ToolbarButton.REDO());
			this.add(new Control.RTE.ToolbarSeparator());
			this.add(Control.RTE.ToolbarButton.HORIZONTAL_RULE());
			this.add(new Control.RTE.ToolbarSeparator());
			this.add(Control.RTE.ToolbarButton.ORDERED_LIST());
			this.add(Control.RTE.ToolbarButton.UNORDERED_LIST());
			this.add(Control.RTE.ToolbarButton.OUTDENT());
			this.add(Control.RTE.ToolbarButton.INDENT());
			this.add(new Control.RTE.ToolbarSeparator());
			this.add(Control.RTE.ToolbarButton.TEXT_COLOR());
			this.add(Control.RTE.ToolbarButton.BACKGROUND_COLOR());
			this.add(new Control.RTE.ToolbarSeparator());
			this.add(Control.RTE.ToolbarButton.INSERT_LINK());
			this.add(Control.RTE.ToolbarButton.INSERT_IMAGE());
			this.add(Control.RTE.ToolbarButton.INSERT_TABLE());
		}
	}
});

Control.RTE.ToolbarItem = new Object();
Object.extend(Control.RTE.ToolbarItem, {
	element: null,
	toolbar: null,
	refresh: Prototype.emptyFunction,
	enable: Prototype.emptyFunction,
	disable: Prototype.emptyFunction
});

Control.RTE.ToolbarSeparator = Class.create();
Object.extend(Control.RTE.ToolbarSeparator.prototype, Control.RTE.ToolbarItem);
Object.extend(Control.RTE.ToolbarSeparator.prototype, {
	initialize: function() {	
		var img = document.createElement('img');
		img.className = 'rteVertSep';
		img.src = Control.RTE.includePath + 'separator.gif';
		img.width = 1;
		img.height = 20;

		this.element = img;
	}
});

Control.RTE.ToolbarLineBreak = Class.create();
Object.extend(Control.RTE.ToolbarLineBreak.prototype, Control.RTE.ToolbarItem);
Object.extend(Control.RTE.ToolbarLineBreak.prototype, {
	initialize: function() {	
		this.element = document.createElement('hr');
		this.element.className = 'rteHorizSep';
	}
});

Control.RTE.ToolbarButton = Class.create();
Object.extend(Control.RTE.ToolbarButton.prototype, Control.RTE.ToolbarItem);
Object.extend(Control.RTE.ToolbarButton.prototype, {

	initialize: function(id, image, title) {
		this.element = this.createButton(id, image, title);
	},

	createButton: function(id, image, title) {
		var img = document.createElement('img');
		img.id = id;
		img.className = 'rteButton';
		img.src = Control.RTE.includePath + image;
		img.width = 25;
		img.height = 24;
		img.alt = title;
		img.title = title;

		this.addCommonBehavior(img);
		this.addButtonBehavior(img);

		return img;
	},

	addButtonBehavior: function(button) {
		this.addButtonActionBehavior(button);
	},

	addButtonActionBehavior: function(button, action) {
		button.onclick = function(e) {
				if (!this.toolbar.disabled) (action || Prototype.emptyFunction).bind(this)(e);
			}.bindAsEventListener(this);
			
		button.onmousedown = function(e) {
				if (!this.toolbar.disabled) {
					Element.addClassName(Event.element(e), 'rteButtonActive');
					Element.removeClassName(Event.element(e), 'rteButtonHover');
				}
				return false;
			}.bindAsEventListener(this);

		button.onmouseup = function(e) {
				if (!this.toolbar.disabled) {
					Element.removeClassName(Event.element(e), 'rteButtonActive');
					Element.addClassName(Event.element(e), 'rteButtonHover');
				}
			}.bindAsEventListener(this);

		button.onmouseover = function(e) {
				if (!this.toolbar.disabled && !Element.hasClassName(Event.element(e), 'rteButtonActive'))
					Element.addClassName(Event.element(e), 'rteButtonHover');
			}.bindAsEventListener(this);

		button.onmouseout = function(e) {
				if (!this.toolbar.disabled)
					Element.removeClassName(Event.element(e), 'rteButtonHover');
					Element.removeClassName(Event.element(e), 'rteButtonActive');
			}.bindAsEventListener(this);
	},

	addCommonBehavior: function(button) {
		// Prevent dragging/highlighting an image
		button.onmousedown = function() { return false; };
		button.onselectstart = function() { return false; };
	},

	disable: function() {
		Element.setOpacity(this.element, 0.3);
	},

	enable: function() {
		Element.setOpacity(this.element, 1.0);
	}

});

Control.RTE.ToolbarCommandButton = Class.create();
Object.extend(Control.RTE.ToolbarCommandButton.prototype, Control.RTE.ToolbarButton.prototype);
Object.extend(Control.RTE.ToolbarCommandButton.prototype, {

	initialize: function(id, image, title, command, noSync) {
		this.command = command;
		this.noSync = noSync;
		this.element = this.createButton(id, image, title);
	},

	addButtonBehavior: function(button) {
		if (this.noSync)
			this.addButtonActionBehavior(button, function(e) { return this.toolbar.editor.doCommand(this.command); }.bindAsEventListener(this));
		else
			this.addButtonStateBehavior(button, function(e) { return this.toolbar.editor.doCommand(this.command); }.bindAsEventListener(this));
	},

	addButtonStateBehavior: function(button, action) {
		button.onmousedown = function(e) {
				if (!this.toolbar.disabled && action(e)) {
					if(this.toolbar.editor.checkCommand(this.command)) {
						Element.addClassName(Event.element(e), 'rteButtonActive');
						Element.removeClassName(Event.element(e), 'rteButtonHover');
					} else {
						Element.removeClassName(Event.element(e), 'rteButtonActive');
						Element.addClassName(Event.element(e), 'rteButtonHover');
					}
				}
				return false;
			}.bindAsEventListener(this);

		button.onmouseover = function(e) {
				if (!this.toolbar.disabled && !Element.hasClassName(Event.element(e), 'rteButtonActive'))
					Element.addClassName(Event.element(e), 'rteButtonHover');
			}.bindAsEventListener(this);

		button.onmouseout = function(e) {
				if (!this.toolbar.disabled)
					Element.removeClassName(Event.element(e), 'rteButtonHover');
			}.bindAsEventListener(this);
	},

	refresh: function() {
		if (this.toolbar.editor.checkCommand(this.command))
			Element.addClassName(this.element, 'rteButtonActive');
		else
			Element.removeClassName(this.element, 'rteButtonActive');
	}

});

Control.RTE.ToolbarDialogButton = Class.create();
Object.extend(Control.RTE.ToolbarDialogButton.prototype, Control.RTE.ToolbarButton.prototype);
Object.extend(Control.RTE.ToolbarDialogButton.prototype, {

	initialize: function(id, image, title, dialogType) {
		this.dialogType = dialogType;
		this.element = this.createButton(id, image, title);
	},

	addButtonBehavior: function(button) {
		this.addButtonActionBehavior(button, function(e) { return this.toolbar.editor.showDialog(this.dialogType, e); }.bindAsEventListener(this));
	}

});

Control.RTE.ToolbarCommandList = Class.create();
Object.extend(Control.RTE.ToolbarCommandList.prototype, Control.RTE.ToolbarItem);
Object.extend(Control.RTE.ToolbarCommandList.prototype, {

	initialize: function(id, list, title, command) {
		this.command = command;
		this.element = this.createList(id, list, title);
	},

	createList: function(id, list, title) {
        var select = new Element('select', {'id':id});
        select.appendChild(new Element('option', {value: ''}).insert({top:title}));
        if (list.constructor == Array) {
            list.each(function(item) {
                select.appendChild(new Element('option', {value: item}).insert({top:item}));
            });
        } else {
            $H(list).each(function(item) {
                select.appendChild(new Element('option', {value: item[0]}).insert({top:item[1]}));
            });
        }
        this.applyBehavior(select);
        return select;
	},

	applyBehavior: function(elt) {
		elt.onchange = this.valueChanged.bindAsEventListener(this);
	},

	valueChanged: function(e) {
		if (!this.toolbar.disabled) {
			var select = Event.element(e);
			var value = select.options[select.selectedIndex].value;
			this.toolbar.editor.doCommand(this.command, value);
		}
	},

	refresh: function() {
		// Check status here
		// This doesn't work right for FontName in Mozilla (haven't checked IE)
		var value = this.toolbar.editor.checkCommandValue(this.command);
		for (var i = 0; i < this.element.options.length; ++i) {
			if (this.element.options[i].value == value) this.element.selectedIndex = i;
			break;
		}
	},

	disable: function() {
		this.element.disabled = true;
	},

	enable: function() {
		this.element.disabled = false;
	}

});

Control.RTE.ToolbarVariableList = Class.create();
Object.extend(Control.RTE.ToolbarVariableList.prototype, Control.RTE.ToolbarItem);
Object.extend(Control.RTE.ToolbarVariableList.prototype, {

	initialize: function(id, list, title, spanClass) {
		this.spanClass = spanClass;
		this.element = this.createList(id, list, title);
	},

	createList: function(id, list, title) {
        var select = new Element('select', {'id':id});
        select.appendChild(new Element('option', {value: ''}).insert({top:title}));
		list.each(function(item) {
			select.appendChild(new Element('option', {value: item}).insert({top:item}));
		});
        this.applyBehavior(select);
        return select;
	},

	applyBehavior: function(elt) {
		elt.onchange = this.valueChanged.bindAsEventListener(this);
	},

	valueChanged: function(e) {
		if (!this.toolbar.disabled) {
			var select = Event.element(e);
			var value = select.options[select.selectedIndex].value;
			if (value) {
				if (this.spanClass)
					value = '<span class="' + this.spanClass + '">' + value + '</span>&nbsp;';
				this.toolbar.editor.insertHtml(value);
			}
			select.selectedIndex = 0;
		}
	},

	disable: function() {
		this.element.disabled = true;
	},

	enable: function() {
		this.element.disabled = false;
	}

});

// Preset buttons
Control.RTE.ToolbarButton.FONT_FACE = function() { return new Control.RTE.ToolbarCommandList('rteFontFace', {'serif': 'Serif', 'sans-serif': 'Sans Serif', 'monospace': 'Monospace'}, 'Font', 'fontname'); };
Control.RTE.ToolbarButton.FONT_SIZE = function() { return new Control.RTE.ToolbarCommandList('rteFontSize', {'1': '-1', '2': 'Normal', '3': '+1', '4': '+2', '5': '+3', '6': '+4', '7': '+5'}, 'Font Size', 'fontsize'); };
Control.RTE.ToolbarButton.BLOCK_STYLE = function() { return new Control.RTE.ToolbarCommandList('rteBlockStyle', {'span': 'No Style', 'p': 'Paragraph', 'pre': 'Preformatted', 'h1': 'Heading 1', 'h2': 'Heading 2', 'h3': 'Heading 3', 'h4': 'Heading 4', 'h5': 'Heading 5', 'h6': 'Heading 6', 'address': 'Address'}, 'Style', 'formatblock'); };
Control.RTE.ToolbarButton.BOLD = function() { return new Control.RTE.ToolbarCommandButton('rteBold', 'bold.gif', 'Bold', 'bold'); };
Control.RTE.ToolbarButton.ITALIC = function() { return new Control.RTE.ToolbarCommandButton('rteItalic', 'italic.gif', 'Italic', 'italic'); };
Control.RTE.ToolbarButton.UNDERLINE = function() { return new Control.RTE.ToolbarCommandButton('rteUnderline', 'underline.gif', 'Underline', 'underline'); };
Control.RTE.ToolbarButton.LEFT_JUSTIFY = function() { return new Control.RTE.ToolbarCommandButton('rteLeftJustify', 'left_just.gif', 'Align Left', 'justifyleft'); };
Control.RTE.ToolbarButton.CENTER_JUSTIFY = function() { return new Control.RTE.ToolbarCommandButton('rteCenterJustify', 'centre.gif', 'Align Center', 'justifycenter'); };
Control.RTE.ToolbarButton.RIGHT_JUSTIFY = function() { return new Control.RTE.ToolbarCommandButton('rteRightJustify', 'right_just.gif', 'Align Right', 'justifyright'); };
Control.RTE.ToolbarButton.FULL_JUSTIFY = function() { return new Control.RTE.ToolbarCommandButton('rteFullJustify', 'justifyfull.gif', 'Full Justified', 'justifyfull'); };
Control.RTE.ToolbarButton.UNDO = function() { return new Control.RTE.ToolbarCommandButton('rteUndo', 'undo.gif', 'Undo', 'undo', true); };
Control.RTE.ToolbarButton.REDO = function() { return new Control.RTE.ToolbarCommandButton('rteRedo', 'redo.gif', 'Redo', 'redo', true); };
Control.RTE.ToolbarButton.HORIZONTAL_RULE = function() { return new Control.RTE.ToolbarCommandButton('rteHorizontalRule', 'hr.gif', 'Horizontal Rule', 'inserthorizontalrule', true); };
Control.RTE.ToolbarButton.ORDERED_LIST = function() { return new Control.RTE.ToolbarCommandButton('rteOrderedList', 'numbered_list.gif', 'Ordered List', 'insertorderedlist'); };
Control.RTE.ToolbarButton.UNORDERED_LIST = function() { return new Control.RTE.ToolbarCommandButton('rteUnorderedList', 'list.gif', 'Unordered List', 'insertunorderedlist'); };
Control.RTE.ToolbarButton.OUTDENT = function() { return new Control.RTE.ToolbarCommandButton('rteOutdent', 'outdent.gif', 'Outdent', 'outdent', true); };
Control.RTE.ToolbarButton.INDENT = function() { return new Control.RTE.ToolbarCommandButton('rteIndent', 'indent.gif', 'Indent', 'indent', true); };
Control.RTE.ToolbarButton.TEXT_COLOR = function() { return new Control.RTE.ToolbarDialogButton('rteTextColor', 'textcolor.gif', 'Text Color', 'textcolor'); };
Control.RTE.ToolbarButton.BACKGROUND_COLOR = function() { return new Control.RTE.ToolbarDialogButton('rteBackgroundColor', 'bgcolor.gif', 'Background Color', 'bgcolor'); };
Control.RTE.ToolbarButton.INSERT_LINK = function() { return new Control.RTE.ToolbarDialogButton('rteLink', 'hyperlink.gif', 'Insert Link', 'link'); };
Control.RTE.ToolbarButton.INSERT_IMAGE = function() { return new Control.RTE.ToolbarDialogButton('rteImage', 'image.gif', 'Insert Image', 'image'); };
Control.RTE.ToolbarButton.INSERT_TABLE = function() { return new Control.RTE.ToolbarDialogButton('rteTable', 'insert_table.gif', 'Insert Table', 'table'); };

/*
 * DIALOG BOXES
 */

Control.RTE.Dialog = Class.create();
Object.extend(Control.RTE.Dialog, {
	activeEffect: null,
	activeDialog: null,

	// Close dialog with animation
	closeActive: function() {
		if (Control.RTE.Dialog.activeDialog) {
			if (Control.RTE.useEffects) {
				// Stop effects before removing element
				if (Control.RTE.Dialog.activeEffect)
					Control.RTE.Dialog.activeEffect.cancel();
				Control.RTE.Dialog.activeEffect = new Effect.SlideUp(Control.RTE.Dialog.activeDialog.dialogContainer, { afterFinish: Control.RTE.Dialog.destroyActive, duration: 0.2 });
			} else {
				Control.RTE.Dialog.destroyActive();
			}
		}
	},

	// Close dialog immediately
	destroyActive: function() {
		if (Control.RTE.Dialog.activeDialog) {
			// Stop effects before removing element
			if (Control.RTE.Dialog.activeEffect) {
				Control.RTE.Dialog.activeEffect.cancel();
				Control.RTE.Dialog.activeEffect = null;
			}
			Control.RTE.Dialog.activeDialog.destroy();
			Control.RTE.Dialog.activeDialog = null;
		}
	},

	activate: function(dialog, editor, anchor, options, callback) {
		// Clean up active dialogs
		Control.RTE.Dialog.destroyActive();
		Control.RTE.Dialog.activeDialog = Control.RTE.Dialog.cache[dialog];
		Control.RTE.Dialog.cache[dialog].activate(editor, anchor, options, callback);
	}

});

Object.extend(Control.RTE.Dialog.prototype, {
	initialize: function() {

		// Outer container with no styling for accurate height/width computations
		var cont = Control.RTE.createElement('div', null, null, { 'position': 'absolute' });
		// Inner container with customizable dialog class
		var dlg = Control.RTE.createElement('div', null, 'rteDialog');
		dlg.appendChild(this.create());
		cont.appendChild(dlg);
		// Hide dialog initially
		Element.hide(cont);

		this.element = cont;

	},

	activate: function(editor, anchor, options, callback) {
		this.editor = editor;
		this.callback = callback;

		this.editor.editorDiv.appendChild(this.element);

		if (anchor) {
			// Attach to a parent element
			var anchorPos = Position.cumulativeOffset(anchor);
			this.element.style.top = (anchorPos[1] + anchor.offsetHeight) + 'px';
			var maxright = Position.cumulativeOffset(editor.editorDiv)[0] + editor.editorDiv.offsetWidth;
			var left = anchorPos[0];
			var width = Element.getDimensions(this.element).width;
			if (left + width > maxright) left = maxright - width;
			this.element.style.left = left + 'px';
		} else {
			// Center below the toolbar and roll down
			this.element.style.top = Position.cumulativeOffset(editor.iframeDiv)[1] + 'px';
			var width = Element.getDimensions(this.element).width;
			var editorWidth = editor.editorDiv.offsetWidth;
			var left = ((editorWidth - width) / 2) + Position.cumulativeOffset(editor.editorDiv)[0];
			this.element.style.left = left + 'px';
		}

		// Refresh data
		this.refresh(options);

		// Slide animation
		if (Control.RTE.useEffects)
			Control.RTE.Dialog.activeEffect = new Effect.SlideDown(this.element, { afterFinish: this.dialogReady.bind(this), duration: 0.2 });
		else {
			Element.show(this.element);
			this.dialogReady();
		}
	},

	refresh: function(options) {
	},

	destroy: function() {
		Element.remove(this.element);
		if (this.editor) this.editor.activeDialog = null;
		this.editor = null;
		this.callback = null;
	},

	dialogReady: function(ef) {
		if (Control.RTE.Dialog.activeEffect == ef)
			Control.RTE.Dialog.activeEffect = null;
		// Only call if it hasn't been closed already
		if (Control.RTE.Dialog.activeDialog == this) {
			(this.focus || Prototype.emptyFunction).bind(this)();
			(this.callback || Prototype.emptyFunction)();
			this.editor.getIframeWindow().blur();
			window.focus();
		}
	},

	create: function() {
		// Override in child
		return document.createElement('div');
	}
});

Control.RTE.Dialog.ColorPalette = Class.create();
Object.extend(Control.RTE.Dialog.ColorPalette.prototype, Control.RTE.Dialog.prototype);
Object.extend(Control.RTE.Dialog.ColorPalette.prototype, {

	create: function() {
		this.colorpicker = new Control.ColorPicker.Panel({
				className: 'rteColorPicker',
				onSelect: function(color) {
						this.editor.setDialogColor(color);
					}.bind(this)
			});
		return this.colorpicker.element;
	},

	focus: function() {
		// Set field focus
		Field.activate(this.colorpicker.customInput);
	}

});

Control.RTE.Dialog.InsertLink = Class.create();
Object.extend(Control.RTE.Dialog.InsertLink.prototype, Control.RTE.Dialog.prototype);
Object.extend(Control.RTE.Dialog.InsertLink.prototype, {

	create: function() {
		var cont = document.createElement('div');

		var linkTable = Control.RTE.createElement('table', { cellpadding: 2, cellspacing: 0, border: 0 });

		var row = linkTable.insertRow(0);
		var cell = row.insertCell(0);
		cell.innerHTML = 'Title';
		cell = row.insertCell(1);
		var linkTitle = Control.RTE.createElement('input', { 'id': 'link_title', 'type': 'text' }, null, { 'width': '120px', 'border': '1px solid gray' });
		cell.appendChild(linkTitle);

		var row = linkTable.insertRow(1);
		var cell = row.insertCell(0);
		cell.innerHTML = 'URL';
		cell = row.insertCell(1);
		var linkUrl = Control.RTE.createElement('input', { 'id': 'link_url', 'type': 'text' }, null, { 'width': '120px', 'border': '1px solid gray' });
		cell.appendChild(linkUrl);

		var row = linkTable.insertRow(2);
		var cell = row.insertCell(0);
		cell.innerHTML = 'Tooltip';
		cell = row.insertCell(1);
		cell.appendChild(Control.RTE.createElement('input', { 'id': 'link_tooltip', 'type': 'text' }, null, { 'width': '120px', 'border': '1px solid gray' }));

		var row = linkTable.insertRow(3);
		var cell = row.insertCell(0);
		cell.innerHTML = '&nbsp;';
		cell = row.insertCell(1);
		cell.appendChild(Control.RTE.createElement('input', { 'id': 'link_newwindow', 'type': 'checkbox' }));
		var label = Control.RTE.createElement('label', { 'for': 'link_newwindow' });
		label.innerHTML = 'New window';
		cell.appendChild(label);

		var row = linkTable.insertRow(4);
		var cell = row.insertCell(0);
		cell.colSpan = 2;
		cell.align = 'center';
		cell.appendChild(Control.RTE.createElement('hr', null, 'rteHorizSep'));
		var submit = Control.RTE.createElement('input', { 'id': 'link_insert', 'type': 'submit', 'value': 'Insert Link' }, null, { 'border': '1px solid gray' });
		cell.appendChild(submit);

		var linkForm = Control.RTE.createElement('form', { 'id': 'link_form' }, null, { 'margin': '0', 'padding': '0' });
		linkForm.onsubmit = this.submitLinkListener();
		linkForm.appendChild(linkTable);

		cont.appendChild(linkForm);

		return cont;
	},

	focus: function() {
		// Set field focus
		var linkText = this.editor.getSelectedText();
		if (linkText && linkText != '') {
			$('link_title').value = linkText;
			Field.activate('link_url');
		} else {
			Field.activate('link_title');
		}
	},

	submitLinkListener: function() {
		return function(e) {
				var linkHtml = '<a href="' + $('link_url').value + '"';
				if ($('link_newwindow').checked) linkHtml += ' target="_new"';
				if ($('link_tooltip').value != '') linkHtml += ' title="' + $('link_tooltip').value + '"';
				linkHtml += '>' + $('link_title').value + '</a>';
				this.editor.insertHtml(linkHtml);
				return false;
			}.bindAsEventListener(this);
	}

});

Control.RTE.Dialog.InsertTable = Class.create();
Object.extend(Control.RTE.Dialog.InsertTable.prototype, Control.RTE.Dialog.prototype);
Object.extend(Control.RTE.Dialog.InsertTable.prototype, {

	create: function() {
		var cont = document.createElement('div');

		var tableTable = Control.RTE.createElement('table', { cellpadding: 2, cellspacing: 0, border: 0 });

		var row = tableTable.insertRow(0);
		var cell = row.insertCell(0);
		cell.innerHTML = 'Rows';
		cell = row.insertCell(1);
		cell.appendChild(Control.RTE.createElement('input', { 'id': 'table_rows', 'type': 'text', 'value': '2', 'align': 'right' }, null, { 'width': '30px', 'border': '1px solid gray', 'paddingRight': '3px' }));
		var cell = row.insertCell(2);
		cell.width = 5;
		cell.innerHTML = '&nbsp;';
		var cell = row.insertCell(3);
		cell.innerHTML = 'Columns';
		cell = row.insertCell(4);
		cell.appendChild(Control.RTE.createElement('input', { 'id': 'table_cols', 'type': 'text', 'value': '2', 'align': 'right' }, null, { 'width': '30px', 'border': '1px solid gray', 'paddingRight': '3px' }));

		row = tableTable.insertRow(1);
		cell = row.insertCell(0);
		cell.innerHTML = 'Width';
		cell = row.insertCell(1);
		cell.colSpan = 4;
		cell.appendChild(Control.RTE.createElement('input', { 'id': 'table_width', 'type': 'text', 'value': '100', 'align': 'right' }, null, { 'width': '30px', 'border': '1px solid gray', 'paddingRight': '3px' }));
		var select = Control.RTE.createElement('select', { 'id': 'table_width_type' }, null, { 'border': '1px solid gray', 'marginLeft': '3px' });
		var option = Control.RTE.createElement('option', { 'value': 'px' });
		option.innerHTML = 'pixels';
		select.appendChild(option);
		option = Control.RTE.createElement('option', { 'value': '%' });
		option.innerHTML = 'percent';
		option.selected = true;
		select.appendChild(option);
		cell.appendChild(select);

		row = tableTable.insertRow(2);
		cell = row.insertCell(0);
		cell.colSpan = 5;
		cell.appendChild(Control.RTE.createElement('hr', null, 'rteHorizSep'));

		row = tableTable.insertRow(3);
		cell = row.insertCell(0);
		cell.colSpan = 3;
		cell.innerHTML = 'Border width';
		cell = row.insertCell(1);
		cell.colSpan = 2;
		cell.appendChild(Control.RTE.createElement('input', { 'id': 'table_border', 'type': 'text', 'value': '1', 'align': 'right' }, null, { 'width': '30px', 'border': '1px solid gray', 'paddingRight': '3px' }));

		row = tableTable.insertRow(4);
		cell = row.insertCell(0);
		cell.colSpan = 3;
		cell.innerHTML = 'Cell spacing';
		cell = row.insertCell(1);
		cell.colSpan = 2;
		cell.appendChild(Control.RTE.createElement('input', { 'id': 'table_cellspacing', 'type': 'text', 'value': '1', 'align': 'right' }, null, { 'width': '30px', 'border': '1px solid gray', 'paddingRight': '3px' }));

		row = tableTable.insertRow(5);
		cell = row.insertCell(0);
		cell.colSpan = 3;
		cell.innerHTML = 'Cell padding';
		cell = row.insertCell(1);
		cell.colSpan = 2;
		cell.appendChild(Control.RTE.createElement('input', { 'id': 'table_cellpadding', 'type': 'text', 'value': '1', 'align': 'right' }, null, { 'width': '30px', 'border': '1px solid gray', 'paddingRight': '3px' }));

		row = tableTable.insertRow(6);
		cell = row.insertCell(0);
		cell.colSpan = 5;
		cell.align = 'center';
		cell.appendChild(Control.RTE.createElement('hr', null, 'rteHorizSep'));
		var submit = Control.RTE.createElement('input', { 'id': 'table_insert', 'type': 'submit', 'value': 'Insert Table' }, null, { 'border': '1px solid gray' });
		cell.appendChild(submit);

		var tableForm = Control.RTE.createElement('form', { 'id': 'table_form' }, null, { 'margin': '0', 'padding': '0' });
		tableForm.onsubmit = this.submitTableListener();
		tableForm.appendChild(tableTable);

		cont.appendChild(tableForm);

		return cont;
	},

	submitTableListener: function() {
		return function(e) {
				var tableHtml = '<table border="' + $('table_border').value + '"';
				tableHtml += ' cellspacing="' + $('table_cellspacing').value + '"';
				tableHtml += ' cellpadding="' + $('table_cellpadding').value + '"';

				var width = $('table_width').value + $('table_width_type').options[$('table_width_type').selectedIndex].value;
				tableHtml += ' width="' + width + '">';

				var rows = parseInt($('table_rows').value);
				var cols = parseInt($('table_cols').value);
				for (var i = 0; i < rows; ++i) {
					tableHtml += '<tr>';
					for (var j = 0; j < rows; ++j)
						tableHtml += '<td>&nbsp;</td>';
					tableHtml += '</tr>';
				}

				tableHtml += '</table>';

				this.editor.insertHtml(tableHtml);
				return false;
			}.bindAsEventListener(this);
	},

	focus: function() {
		$('table_rows').focus();
		$('table_rows').select();
	}

});

Control.RTE.Dialog.ImageBrowser = Class.create();
Object.extend(Control.RTE.Dialog.ImageBrowser.prototype, Control.RTE.Dialog.prototype);
Object.extend(Control.RTE.Dialog.ImageBrowser.prototype, {

	create: function() {
		var cont = document.createElement('div');
		this.imageForm = this.createAttributeForm();
		cont.appendChild(this.imageForm);
		return cont;
	},

	refresh: function(options) {
		this.imageForm.reset();
		if (options && options.fileLister && typeof Control.FileChooser != 'undefined') {
			if (!this.browser) {
				this.browser = new Control.FileChooser.Panel(null, {
							className: 'rteFileChooser',
							fileImage: Control.RTE.includePath + '/file.gif',
							directoryImage: Control.RTE.includePath + '/directory.gif',
							parentImage: Control.RTE.includePath + '/parent.gif',
							selectListener: function(url) {
								$('image_url').value = url;
							},
							previewListener: function(width, height) {
								$('image_width').value = width;
								$('image_height').value = height;
							},
							openListener: this.submitImageListener()
						}
					);
				this.imageForm.parentNode.insertBefore(this.browser.getElement(), this.imageForm);
			}
			this.browser.fileLister = options.fileLister;
			this.browser.refresh(null);
		}
	},

	createAttributeForm: function() {
		var imageForm = Control.RTE.createElement('form', { 'id': 'image_form' }, null, { 'margin': '0', 'padding': '0' });
		imageForm.onsubmit = this.submitImageListener();

		var imageTable = Control.RTE.createElement('table', { cellpadding: 2, cellspacing: 0, border: 0 });

		var row = imageTable.insertRow(0);
		var cell = row.insertCell(0);
		cell.innerHTML = '<nobr>Image URL</nobr>';
		cell = row.insertCell(1);
		cell.colSpan = 7;
		cell.appendChild(Control.RTE.createElement('input', { 'id': 'image_url', 'type': 'text' }, null, { 'width': '295px', 'border': '1px solid gray' }));

		row = imageTable.insertRow(1);
		cell = row.insertCell(0);
		cell.innerHTML = 'Width';
		cell = row.insertCell(1);
		cell.appendChild(Control.RTE.createElement('input', { 'id': 'image_width', 'type': 'text', 'align': 'right' }, null, { 'width': '30px', 'border': '1px solid gray', 'paddingRight': '3px' }));

		cell = row.insertCell(2);
		cell.width = 5;
		cell.innerHTML = '&nbsp;';

		cell = row.insertCell(3);
		cell.innerHTML = 'Height';

		cell = row.insertCell(4);
		cell.align = 'right';
		cell.appendChild(Control.RTE.createElement('input', { 'id': 'image_height', 'type': 'text', 'align': 'right' }, null, { 'width': '30px', 'border': '1px solid gray', 'paddingRight': '3px' }));

		cell = row.insertCell(5);
		cell.width = 5;
		cell.innerHTML = '&nbsp;';

		cell = row.insertCell(6);
		cell.innerHTML = 'Alignment';

		cell = row.insertCell(7);
		var select = Control.RTE.createElement('select', { 'id': 'image_align' }, null, { 'border': '1px solid gray' });
		var option = Control.RTE.createElement('option', { 'value': '' });
		option.innerHTML = 'Default';
		option.selected = true;
		select.appendChild(option);
		option = Control.RTE.createElement('option', { 'value': 'left' });
		option.innerHTML = 'Left';
		select.appendChild(option);
		option = Control.RTE.createElement('option', { 'value': 'center' });
		option.innerHTML = 'Center';
		select.appendChild(option);
		option = Control.RTE.createElement('option', { 'value': 'right' });
		option.innerHTML = 'Right';
		select.appendChild(option);
		cell.appendChild(select);

		imageForm.appendChild(imageTable);

		imageTable = Control.RTE.createElement('table', { cellpadding: 2, cellspacing: 0, border: 0 });

		row = imageTable.insertRow(0);
		cell = row.insertCell(0);
		cell.innerHTML = 'Description';
		cell = row.insertCell(1);
		cell.appendChild(Control.RTE.createElement('input', { 'id': 'image_title', 'type': 'text' }, null, { 'width': '295px', 'border': '1px solid gray' }));

		row = imageTable.insertRow(1);
		cell = row.insertCell(0);
		cell.innerHTML = 'Alt text';
		cell = row.insertCell(1);
		cell.appendChild(Control.RTE.createElement('input', { 'id': 'image_alt', 'type': 'text' }, null, { 'width': '295px', 'border': '1px solid gray' }));

		row = imageTable.insertRow(2);
		cell = row.insertCell(0);
		cell.colSpan = 2;
		cell.appendChild(Control.RTE.createElement('hr', null, 'rteHorizSep'));

		imageForm.appendChild(imageTable);

		var submitDiv = Control.RTE.createElement('div', null, null, { 'textAlign': 'center' });
		submitDiv.appendChild(Control.RTE.createElement('input', { 'id': 'image_insert', 'type': 'submit', 'value': 'Insert Image' }, null, { 'border': '1px solid gray' }));
		imageForm.appendChild(submitDiv);

		return imageForm;
	},

	createImageHtml: function(url, width, height, align, title, alt) {
		var imageHtml = '<img src="' + url + '"';
		if (width && width != '') imageHtml += ' width="' + width + '"';
		if (height && height != '') imageHtml += ' height="' + height + '"';
		if (align && align != '') imageHtml += ' align="' + align + '"';
		if (title && title != '') imageHtml += ' title="' + title + '"';
		if (alt && alt != '') imageHtml += ' alt="' + alt + '"';
		imageHtml += ' border="0"/>';
		return imageHtml;
	},

	submitImageListener: function() {
		return function(e) {
				var url = $('image_url').value;
				var width = $('image_width').value;
				var height = $('image_height').value;
				var align = $('image_align').options[$('image_align').selectedIndex].value;
				var title = $('image_title').value;
				var alt = $('image_alt').value;

				this.editor.insertHtml(this.createImageHtml(url, width, height, align, title, alt));
				return false;
			}.bindAsEventListener(this);
	}

});

Protoplasm.register('rte', Control.RTE);
