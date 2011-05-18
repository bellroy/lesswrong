if (typeof Protoplasm == 'undefined')
	throw('protoplasm.js not loaded, could not intitialize filechooser');
if (typeof Control == 'undefined') Control = {};

Protoplasm.use('dialog');
Protoplasm.use('upload');
Protoplasm.loadStylesheet('filechooser.css', 'filechooser');

/**
 * class Control.FileChooser
 * 
 * Displays a file chooser when a user clicks on the file select icon in
 * the input control.  Requires a user-provided function to provide directory
 * queries (static or via AJAX).
 *
 * Control ID: `filechooser`
 *
 * Features:
 *  - Image preview
 *  - Integrated file upload
 *  - Create and delete directories and files
 *  - Customizable by CSS
 *
 * Example: <a href="http://jongsma.org/software/protoplasm/control/filechooser">File
 * Chooser demo</a>
**/
Control.FileChooser = Class.create({

/**
 * new Control.FileChooser(element, fileHandler[, options])
 * - element (String | Element): A `<input type="text">` element (or DOM ID).
 * - fileHandler (Function): The file lister callback.
 * - options (Hash): Additional options for the control.
 *
 * Create a new file chooser from the given `<input type="text">`
 * element.
 *
 * For details on the fileHandler specifications, see
 * the <a href="http://jongsma.org/software/protoplasm/control/filechooser#filehandler">online
 * documentation</a>.
 *
 * Additional options:
 *
 * * icon: The icon to display in the input box
 * * fileImage: The file icon to use in the chooser
 * * directoryImage: The directory icon to use in the chooser
 * * parentImage: The parent directory icon to use in the chooser
**/
	initialize: function(element, fileManager, options) {

/**
 * Control.FileChooser#element -> Element
 *
 * The underlying `<input>` element passed to the constructor.
**/
		this.element = $(element);

		if (fc = this.element.retrieve('filechooser'))
			fc.destroy();

		this.options = options || {};
		
		// Load resources from script directory
		var base = Protoplasm.base('filechooser');
		if (!this.options.icon) this.options.icon = base + 'filechooser.png';
		if (!this.options.fileImage) this.options.fileImage = base + 'file.gif';
		if (!this.options.directoryImage) this.options.directoryImage = base + 'directory.gif';
		if (!this.options.parentImage) this.options.parentImage = base + 'parent.gif';

		if (this.options.icon) {
			this.element.style.background = 'url('+this.options.icon+') right center no-repeat #FFF';
			// Prevent text writing over icon
			this.oldPadding = this.element.style.paddingRight;
			this.element.style.paddingRight = '20px';
		}

/**
 * Control.FileChooser#panel -> Control.FileChooser.Panel
 *
 * The panel dialog box linked to this control.  This may be
 * null if the control is not open.
**/
		this.panel = new Control.FileChooser.Panel(fileManager, Object.extend({
				openListener: this.fileSelected.bind(this),
				standalone: true,
				selectFile: this.element.value
			}, this.options || {}));

		this.dialogOpen = false;

		this.dialog = this.panel.getElement();

		this.listeners = [
			this.element.on('click', this.toggle.bindAsEventListener(this)),
			this.element.on('blur', this.delayedHide.bindAsEventListener(this)),
			this.dialog.on('click', this.cancelHide.bindAsEventListener(this)),
			this.element.on('keydown', this.keyHandler.bindAsEventListener(this))
		];

		this.clickListener = null;
		this.keyListener = null;

		this.element.store('filechooser', this);
		this.destructor = Event.on(window, 'unload', this.destroy.bind(this));
	},

/**
 * Control.FileChooser#destroy() -> null
 *
 * Destroy this control and return the underlying element to
 * its original behavior.
**/
	destroy: function() {
		this.hide();
		for (var i = 0; i < this.listeners.length; i++)
			this.listeners[i].stop();
		if (this.clickListener)
			this.clickListener.stop();
		if (this.keyListener)
			this.keyListener.stop();
		//this.wrapper.parentNode.replaceChild(this.element, this.wrapper);
		this.element.style.paddingRight = this.oldPadding;
		this.element.store('filechooser', null);
		this.destructor.stop();
	},

	fileSelected: function(file) {
		if (file)
			this.element.value = file.url;
		this.hide();
	},

/**
 * Control.FileChooser#toggle() -> null
 *
 * Toggle the visibility of the file chooser panel for this control.
**/
	toggle: function() {
		if (this.dialogOpen) this.hide();
		else this.show();
	},

/**
 * Control.FileChooser#show() -> null
 *
 * Show the file chooser panel for this control.
**/
	show: function() {
		if (!this.dialogOpen) {
			var dim = Element.getDimensions(this.element);
			var position = Position.cumulativeOffset(this.element);
			var pickerTop = /MSIE/.test(navigator.userAgent) ? (position[1] + dim.height) + 'px' : (position[1] + dim.height - 1) + 'px';
			this.dialog.style.top = pickerTop;
			this.dialog.style.left = position[0] + 'px';
			if (this.element.value)
				this.panel.select(this.element.value);
			else
				this.panel.refresh();
			document.body.appendChild(this.dialog);
			this.clickListener = document.on('click', this.documentClickHandler.bindAsEventListener(this));
			this.keyListener = document.on('keydown', this.escHandler.bindAsEventListener(this));
			this.dialogOpen = true;
		}
	},
	delayedHide: function(e) {
		this.hideTimeout = setTimeout(this.hide, 100);
	},
	cancelHide: function(e) {
		if (this.hideTimeout) {
			clearTimeout(this.hideTimeout);
			this.hideTimeout = null;
		}
	},
/**
 * Control.FileChooser#hide() -> null
 *
 * Hide the file chooser panel for this control.
**/
	hide: function() {
		if (this.dialogOpen) {
			if (this.clickListener) {
				this.clickListener.stop();
				this.clickListener = null;
			}
			if (this.keyListener) {
				this.keyListener.stop();
				this.keyListener = null;
			}
			if (this.dialog.parentNode)
				Element.remove(this.dialog);
			this.dialogOpen = false;
		}
	},
	keyHandler: function(e) {
		switch(e.keyCode) {
			case Event.KEY_DOWN:
				this.show();
				break;
		}
	},
	escHandler: function(e) {
		switch(e.keyCode) {
			case Event.KEY_ESC:
				this.hide();
				break;
		}
	},
	documentClickHandler: function(e) {
		var element = Event.element(e);
		var abort = false;
		do {
			if (element == this.dialog || element == this.element
					|| (Dialog.active && (element == Dialog.active.contents
						|| element == Dialog.active.overlay)))
				abort = true;
		} while (element = element.parentNode);
		if (!abort)
			this.hide();
	}
});

/**
 * class Control.FileChooser.Panel
 *
 * The dialog panel that is displayed when the file chooser is opened.
**/
Control.FileChooser.Panel = Class.create({

/**
 * new Control.FileChooser.Panel([options])
 * - fileHandler (Function): The file lister callback.
 * - options (Hash): Additional options for the control.
 *
 * Create a new file chooser panel.
 *
 * For details on the fileHandler specifications, see
 * the <a href="http://jongsma.org/software/protoplasm/control/filechooser#filehandler">online
 * documentation</a>.
 *
 * Additional options:
 *
 * * icon: The icon to display in the input box
 * * className: The class name for the main panel container
 * * width: The panel width
 * * width: The panel height
 * * fileImage: The file icon to use in the chooser
 * * directoryImage: The directory icon to use in the chooser
 * * parentImage: The parent directory icon to use in the chooser
 * * uploadHandler: The upload handler function, called when "Upload"
 *   is clicked
**/
	initialize: function(fileLister, options) {
		this.fileLister = fileLister || Prototype.emptyFunction;
		this.options = Object.extend({
				width: 360,
				height: 220,
				className: '',
				fileImage: '/images/icons/file.gif',
				directoryImage: '/images/icons/directory.gif',
				parentImage: '/images/icons/parent.gif',
				uploadProgress: false
			}, options || {});

		this.uploadHandler = this.options.uploadProgress
			?  this.showAdvancedUploadDialog.bind(this)
			: this.showUploadDialog.bind(this);
/**
 * Control.FileChooser.Panel#element -> Element
 *
 * The root Element of this dialog panel.
**/
		this.element = this.createFileChooser();
		if (this.options.selectFile)
			this.select(this.options.selectFile);
	},

	getElement: function() {
		return this.element;
	},

	createFileChooser: function() {
		var browser = new Element('div');

		this.directoryHeader = new Element('div', { 'class': '_pp_filechooser_directoryheader',
			'style': 'margin-bottom:5px;'}).update('&nbsp;');
		browser.appendChild(this.directoryHeader);

		var table = new Element('table');
		table.cellSpacing = 0;
		table.cellPadding = 0;
		table.style.border = 0;

		var row = table.insertRow(0);

		var previewHeight = this.options.height - 40;
		var previewWidth = Math.round((this.options.width - 6) * 0.3);
		var listHeight = this.options.height - 61;
		var listWidth = this.options.width - previewWidth - 10;

		var cell = row.insertCell(0);
		cell.vAlign = 'top';
		this.fileList = new Element('div', { 'class': '_pp_panel _pp_inset',
			'style': 'height:'+listHeight+'px;width'+listWidth+'px;overflow:auto;margin-right:3px;margin-bottom:5px;'});
		this.fileList.on('mousedown', function() { return false; });
		this.fileList.on('selectstart', function() { return false; });
		cell.appendChild(this.fileList);

		this.createButton = new Element('input', { 'type': 'button', 'value': 'New Folder', 'class': '_pp_button',
			'style': 'margin-right:5px;width:'+Math.round((listWidth - 10) / 3)+'px'});
		this.createButton.on('click', this.showDirectoryCreateDialog.bindAsEventListener(this));

		this.uploadButton = new Element('input', { 'type': 'button', 'value': 'New File', 'class': '_pp_button',
			'style': 'margin-right:5px;width:'+Math.round((listWidth - 10) / 3)+'px'});
		this.uploadButton.on('click', function(e) { this.uploadHandler(this); }.bindAsEventListener(this));

		this.deleteButton = new Element('input', { 'type': 'button', 'value': 'Delete', 'class': '_pp_button',
			'style': 'width:'+Math.round((listWidth - 10) / 3)+'px'});
		this.deleteButton.on('click', this.showDeleteDialog.bindAsEventListener(this));

		var buttons = new Element('div');
		buttons.appendChild(this.createButton);
		buttons.appendChild(this.uploadButton);
		buttons.appendChild(this.deleteButton);
		cell.appendChild(buttons);

		cell = row.insertCell(1);
		cell.vAlign = 'top';
		this.filePreview = new Element('div', { 'class': '_pp_filechooser_preview _pp_inset',
			'style': 'height:'+previewHeight+'px;width:'+previewWidth
				+'px;margin-left:3px;margin-bottom:5px;overflow:hidden;position:relative'});
		cell.appendChild(this.filePreview);

		browser.appendChild(table);

		document.on('keydown', this.keyPressListener());

		if (this.options.standalone) {
			var form = new Element('form');
			form.style.margin = 0;

			var table = new Element('table');
			table.cellSpacing = 0;
			table.cellPadding = 0;
			table.border = 0;

			var row = table.insertRow(0);

			var cell = row.insertCell(0);
			this.fileLocation = new Element('input', {'type': 'text', 'readOnly': true,
				'style': 'width:245px;margin-right:5px'});
			cell.appendChild(this.fileLocation);

			cell = row.insertCell(1);
			cell.style.textAlign = 'right';
			var input = new Element('input', { 'type': 'button', 'value': 'Cancel', 'class': '_pp_button',
				'style': 'width:50px;margin-right:5px;'});
			input.on('click', function(e) { Element.remove(this.getElement()); }.bindAsEventListener(this));
			cell.appendChild(input);

			cell = row.insertCell(2);
			cell.style.textAlign = 'right';
			var input = new Element('input', { 'type': 'button', 'value': 'Select', 'class': '_pp_button',
				'style': 'width:50px;' });
			input.on('click', function(e) {
					(this.options.openListener || Prototype.emptyFunction)(this.selectedFile);
				}.bindAsEventListener(this));
			cell.appendChild(input);

			form.appendChild(table);

			browser.appendChild(form);

			var wrapper = new Element('div');
			wrapper.style.position = 'absolute';
			wrapper.appendChild(browser);

			wrapper.className = '_pp_frame _pp_filechooser '+this.options.className;
			return wrapper;
		} else {
			browser.className = '_pp_frame _pp_filechooser '+this.options.className;
			return browser;
		}
	},

/**
 * Control.FileChooser.Panel#select(file) -> null
 * - file (String): The file path to select (relative to your file manager root)
 *
 * Navigate to the directory containing the given file and select
 * it.
**/
	select: function(path) {
		this.filePreview.innerHTML = '';
		this.fileList.innerHTML = '<div style="padding:3px">Loading file list...</div>';
		this.selectedFile = null;
		var response = this.fileLister(null, this.selectByURL(path).bind(this));
		if (response)
			this.selectByURL(path)(response);
	},

/**
 * Control.FileChooser.Panel#selectByUrl(url) -> null
 * - file (String): The file URL to select
 *
 * Navigate to the directory containing the file represented by the 
 * given url and select it.
**/
	selectByURL: function(path) {
		return function(directory) {
			console.log(directory);
			if (directory.status != 'error' && path && path.indexOf(directory.url) == 0) {
				var relpath = path.substr(directory.url.length);
				var reldir = relpath.substr(0, relpath.lastIndexOf('/'));
				this.pendingSelect = path;
				if (reldir != directory.path) {
					this.refresh(reldir);
					return;
				}
			}
			this.populateFileList(directory);
		}.bind(this);
	},

/**
 * Control.FileChooser.Panel#refresh() -> null
 *
 * Refresh the current directory.
**/
	refresh: function(directory) {
		if (!directory && this.currentDirectory) directory = this.currentDirectory.path;
		Dialog.close();
		this.filePreview.update();
		this.fileList.update('<div style="padding:3px">Loading file list...</div>');
		this.selectedFile = null;

		var response = this.fileLister(directory, this.populateFileList.bind(this));
		// If it returned no result, it's asynchronous
		if (response)
			this.populateFileList(response);
	},

	populateFileList: function(directory) {
		if (directory.status == 'error') {
			this.fileList.update('<div style="padding:3px">Could not get directory contents.</div>');
			return;
		}

		this.currentDirectory = directory;
		this.entries = [];
	
		this.directoryHeader.update('<b>Folder:</b> ' + (directory.path || '/'));
		this.fileList.update();
		if (directory.parent)
			this.entries[this.entries.length] = {
				image: 'parent',
				type: 'directory',
				name: 'Parent folder',
				path: directory.parent 
				};
		if(directory.files) {
			if (directory.files.constructor == Array)
				directory.files.each(function(row) {
						this.entries.push(row);
					}.bind(this));
			else
				this.entries.push(directory.files);
		}

		if (this.entries.length) {
			var table = new Element('table');
			var sRow = null;
			table.cellSpacing = 0;
			table.cellPadding = 0;
			table.width = '100%';
			table.style.border = 3;
			this.entries.each(function(row) {
					var cRow = this.createFileRow(row, table);
					if (this.pendingSelect && this.pendingSelect == row.url) {
						this.selectRow(row);
						sRow = cRow;
						this.pendingSelect = null;
					}
				}.bind(this));
			this.fileList.appendChild(table);
			if (sRow) {
				var tHeight = table.offsetHeight;
				var cHeight = this.fileList.offsetHeight;
				var rTop = sRow.offsetTop;
				var rBottom = rTop + sRow.offsetHeight;
				if (rBottom > cHeight) {
					var idealTop = Math.round(rTop - (cHeight / 2));
					if (idealTop + cHeight > tHeight)
						this.fileList.scrollTop = tHeight - cHeight;
					else
						this.fileList.scrollTop = idealTop;
				}
			}
		} else {
			this.fileList.update('<div style="padding:3px">To add items to your folder, please click <b>New Folder</b> or <b>New File</b> below.</div>');
		}

		if (directory.fileManager) {
			this.createButton.disabled = false;
			this.uploadButton.disabled = false;
		} else {
			this.createButton.disabled = true;
			this.uploadButton.disabled = true;
		}
	},

	showAdvancedUploadDialog: function(chooser) {
		this.showUploadDialog(chooser, true);
	},

	showUploadDialog: function(chooser, progress) {

		var form = new Element('form', { 'method': 'post',
			'action': this.currentDirectory.fileManager,
			'style': 'padding: 12px;width:300px;' });

		var path = this.currentDirectory.path || '';
		form.appendChild(new Element('input', { 'type': 'hidden', 'name': 'a',
			'value': 'upload' }));
		form.appendChild(new Element('input', { 'type': 'hidden', 'name': 'p',
			'value': (this.currentDirectory.path || '') }));

		var label = new Element('div', { 'style': 'float:left;width:60px;padding-top:3px;' }).update('Files:');
		form.appendChild(label);
		var file = new Element('input', { 'type': 'file', 'name': 'i', 'multiple': 'multiple' });
		form.appendChild(file);
		form.appendChild(new Element('br'));
		var buttons = new Element('div', { 'style': 'float:right;' });
		var cancel = new Element('input', { 'type': 'button', 'value': 'Close', 'class': '_pp_button' });
		cancel.on('click', function(e) { Dialog.close(); Event.stop(e); }.bindAsEventListener(this));
		buttons.appendChild(cancel);
		buttons.appendChild(new Element('input', { 'type': 'submit', 'value': 'Upload Files', 'class': '_pp_button' }));
		form.appendChild(buttons);
		form.appendChild(new Element('div', {'style': 'clear:both;' }));

		var failed = false;
		var uploader = new Control.FileUpload(file, {
				multiple: true,
				inline: true,
				batch: true,
				progress: progress,
				includeFields: ['a', 'p'],
				prependPath: path,
				onFailure: function() {
					failed = true;
				},
				onComplete: function() {
					if (!failed)
						Dialog.close();
				}.bind(this)
			});

		var frame = new Element('div', { 'class': '_pp_dialog _pp_panel' });
		frame.appendChild(new Element('div', { 'class': '_pp_title' }).update('Upload Files'));
		frame.appendChild(form);

		var dialog = new Dialog.HTML(frame, {
				onClose: function() {
					this.refresh();
				}.bind(this)
			});
		dialog.show();

	},

	showDeleteDialog: function() {
		var message = this.selectedFile.type == 'directory'
			? 'Are you sure you want to PERMANENTLY delete this folder\nand all files and folders in it?'
			: 'Are you sure you want to PERMANENTLY delete this file?';
		if (this.selectedFile && confirm(message)) {
			var url = this.currentDirectory.fileManager;
			var options = {
					parameters: 'a=delete&p=' + (this.currentDirectory.path || '') + '&f=' + this.selectedFile.name,
					onSuccess: function(transport) {
							this.refresh(this.currentDirectory.path);
						}.bindAsEventListener(this),
					onFailure: function(transport) {
							this.refresh(this.currentDirectory.path);
							alert(transport.responseText);
						}.bindAsEventListener(this)
				};

			this.filePreview.innerHTML = '';
			this.fileList.innerHTML = 'Loading file list...';

			new Ajax.Request(url, options);
		}
	},

	showDirectoryCreateDialog: function() {
		var dirname = prompt('Enter a folder name:', '');
		if (dirname)
			this.createDirectory(dirname);
	},

	createDirectory: function(dirname) {
		var url = this.currentDirectory.fileManager;
		var options = {
				parameters: 'a=createdir&p=' + (this.currentDirectory.path || '') + '&d=' + dirname,
				onSuccess: this.createDirectorySuccessful.bind(this),
				onFailure: this.createDirectoryFailed.bind(this)
			};

		this.filePreview.innerHTML = '';
		this.fileList.innerHTML = 'Loading file list...';

		new Ajax.Request(url, options);
	},

	createDirectorySuccessful: function(transport) {
		this.refresh(this.currentDirectory.path);
	},

	createDirectoryFailed: function(transport) {
		this.refresh(this.currentDirectory.path);
		alert(transport.responseText);
	},

	showPreview: function(url) {

		// Clear preview pane
		while(this.filePreview.firstChild)
			Element.remove(this.filePreview.firstChild);

		var ext = url.substring(url.lastIndexOf('.')+1);
		if (!ext || !$w('jpeg jpg gif png bmp').include(ext.toLowerCase()))
			return;

		var image = new Element('img');
		var loaded = false;

		image.onload = function(e) {
				// Event fires again when adding to the preview frame
				if (!loaded) {
					loaded = true;

					var origWidth = image.width;
					var origHeight = image.height;

					// Figure out maximum dimensions and current ratios
					var maxWidth = this.filePreview.offsetWidth - 6;
					var maxHeight = this.filePreview.offsetHeight - 6;
					var widthRatio = image.width / maxWidth;
					var heightRatio = image.height / maxHeight;

					// Adjust to best fit
					if (widthRatio > 1 && widthRatio >= heightRatio) {
						image.width = Math.floor(image.width / widthRatio);
						image.height = Math.floor(image.height / widthRatio);
					} else if (heightRatio > 1) {
						image.width = Math.floor(image.width / heightRatio);
						image.height = Math.floor(image.height / heightRatio);
					}

					// Add to preview pane
					image.setStyle({
						'position': 'absolute',
						'top': Math.round((maxHeight - image.height) / 2) + 'px',
						'left': Math.round((maxWidth - image.width) / 2) + 'px',
						'backgroundColor': '#FFFFFF',
						'border': 1});
					this.filePreview.appendChild(image);

					if (this.options.previewListener)
						this.options.previewListener(origWidth, origHeight);
				}
			}.bindAsEventListener(this);

		image.onerror = function(e) {
				// Clear preview pane
				while(this.filePreview.firstChild)
					Element.remove(this.filePreview.firstChild);
				if (this.options.previewListener)
					this.options.previewListener('', '');
			}.bindAsEventListener(this);

		image.src = url;

	},

	createFileRow: function(record, table) {
		var row = table.insertRow(table.rows.length);

		var cell = row.insertCell(0);
		cell.className = '_pp_filechooser_filerow';
		cell.width = 10;
		cell.appendChild(new Element('img',
			{'src': this.options[(record.image || record.type) + 'Image']}));

		cell = row.insertCell(1);
		cell.className = '_pp_filechooser_filerow';
		cell.appendChild(new Element('div', {'style': 'overflow:hidden;'})
			.update(record.name));

		cell = row.insertCell(2);
		cell.className = '_pp_filechooser_filerow';
		cell.align = 'right';

		if (record.size !== undefined) {
			var sizeDesc;
			if (record.type == 'directory')
				sizeDesc = record.size + ' items';
			else
				sizeDesc= this.formatFileSize(record.size);
			cell.innerHTML = '<nobr>' + sizeDesc + '</nobr>';
		} else {
			cell.innerHTML = '&nbsp;';
		}

		row.onmousedown = this.fileSelectListener(record);
		if (record.type == 'file')
			row.ondblclick = this.fileOpenListener(record);
		else
			row.ondblclick = this.directoryOpenListener(record);
		row.onselectstart = function() { return false; };

		record.element = row;

		return row;
	},

	formatFileSize: function(bytes) {
		if (!bytes) bytes = 0;
		if (bytes < 1024) {
			return bytes + ' bytes';
		} else if (bytes < 1024*1024) {
			return this.twoDecimals(bytes / 1024) + ' KB';
		} else {
			return this.twoDecimals(bytes / (1024*1024)) + ' MB';
		}
	},

	twoDecimals: function(num) {
		return Math.round(num * 100) / 100;
	},

	fileSelectListener: function(record) {
		return function(e) {	
				this.selectRow(record);
				return false;
			}.bindAsEventListener(this);
	},

	directoryOpenListener: function(record) {
		return function(e) {
				this.refresh(record.path);
			}.bindAsEventListener(this);
	},

	fileOpenListener: function(record) {
		return function(e) {
				if (this.options.openListener)
					this.options.openListener(record);
			}.bindAsEventListener(this);
	},

	keyPressListener: function() {
		return function(e) {
				if (this.element.parentNode) {
					switch(e.keyCode) {
						case Event.KEY_DELETE:
							this.showDeleteDialog();
							break;
						case Event.KEY_RETURN:
							if (this.selectedFile) {
								if (this.selectedFile.type == 'file')
									this.fileOpenListener(this.selectedFile)();
								else
									this.directoryOpenListener(this.selectedFile)();
							}
							break;
						case Event.KEY_UP:
							var idx = this.selectedIndex() - 1;
							if (idx < 0) idx = 0;
							this.selectRow(this.entries[idx]);
							break;
						case Event.KEY_DOWN:
							var idx = this.selectedIndex() + 1;
							if (idx >= this.entries.length) idx = this.entries.length - 1;
							this.selectRow(this.entries[idx]);
							break;
						case 33: // PgUp
							var visibleRows = Math.floor(this.fileList.offsetHeight / this.entries[0].element.offsetHeight);
							var idx = this.selectedIndex() - visibleRows;
							if (idx < 0) idx = 0;
							this.selectRow(this.entries[idx]);
							break;
						case 34: // PgDn
							var visibleRows = Math.floor(this.fileList.offsetHeight / this.entries[0].element.offsetHeight);
							var idx = this.selectedIndex() + visibleRows;
							if (idx >= this.entries.length) idx = this.entries.length - 1;
							this.selectRow(this.entries[idx]);
							break;
						case 35: // End
							if (this.entries)
								this.selectRow(this.entries[this.entries.length - 1]);
							break;
						case 36: // Home
							if (this.entries)
								this.selectRow(this.entries[0]);
							break;
						default:
							return;
					}
					Event.stop(e);
				}
			}.bindAsEventListener(this);
	},

	selectRow: function(record) {
		if (this.selectedFile != record) {
			if (this.selectedFile)
				Element.removeClassName(this.selectedFile.element, '_pp_highlight')

			this.selectedFile = record;
			Element.addClassName(record.element, '_pp_highlight')
			if (record.url) {
				this.showPreview(record.url);
				if (this.options.standalone)
					this.fileLocation.value = record.url;
				if (this.options.selectListener)
					this.options.selectListener(record.url);
			} else {
				this.showPreview('');
				if (this.options.selectListener)
					this.options.selectListener('');
			}
		}

		if (record.element.offsetTop < this.fileList.scrollTop)
			this.fileList.scrollTop = record.element.offsetTop;
		else if (record.element.offsetTop + record.element.offsetHeight > this.fileList.scrollTop + this.fileList.offsetHeight)
			this.fileList.scrollTop = (record.element.offsetTop + record.element.offsetHeight) - this.fileList.offsetHeight;
	},

	selectedIndex: function() {
		for (index = 0; index < this.entries.length; ++index)
			if (this.entries[index] == this.selectedFile)
				return index;
		return -1;
	}

});

Protoplasm.register('filechooser', Control.FileChooser);
