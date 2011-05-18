if (typeof Protoplasm == 'undefined')
	throw('protoplasm.js not loaded, could not intitialize upload');
if (typeof Control == 'undefined') Control = {};

Protoplasm.loadStylesheet('upload.css', 'upload');

/**
 * class Control.FileUpload
 * 
 * Creates a user-friendly file upload control out of a
 * normal &lt;input type="file"&gt; field.
 *
 * Control ID: `upload`
 *
 * Features:
 *
 * * Supports uploading multiple files.
 * * Allows inline uploading without reloading the page.
 * * Displays upload progress in Chrome, FF, Safari.
 *
 * Example: <a href="http://jongsma.org/software/protoplasm/control/upload">File
 * Upload demo</a>
**/
Control.FileUpload = Class.create(function() {

	// Static vars
	var separator = /[\/\\]/g;

	return {

/**
 * new Control.FileUpload(element, options)
 * - element (Element | String): A DOM element (or element ID)
 * - options (Hash): Additional options for the control.
 *
 * Create a new file upload control.  This control can handle
 * uploading multiple files at one time, and will display upload
 * progress for each file (with a server-side callback script.)
 *
 * Additional options:
 *
 * * `multiple`: Allow multiple uploads (default: false)
 * * `inline`: Upload files immediately without reloading the
 *   page instead of submitting with the parent form. (default: false)
 * * `progress`: Display upload progress in supported browsers.
 *   Has no effect if `inline` is false.  This requires submitting
 *   data to the server in a different format - see the
 *   <a href="/software/protoplasm/control/upload#handler">online
 *   documentation</a> for further details. (default: true)
 * * `batch`: Use batch mode. Requires manually submission instead
 *   of uploading files as they are selected.  Has no effect
 *   if `inline` is false. (default: false)
 * * `onSuccess`: Callback function when a file upload succeeds.
 * * `onFailure`: Callback function when a file upload fails.
 * * `onComplete`: Callback function when all file uploads are complete.
 *
 * Callback functions take the uploaded filename as a parameter.
**/
		initialize: function(element, options) {
			
			element = $(element);

			// Element must be an input[type=file] in a form
			if (!element || element.nodeName != 'INPUT'
					|| element.type != 'file' || !element.form)
				throw('element is not a file input.');

			// If element has a control attached, destroy it first
			if (c = element.retrieve('fileupload'))
				c.destroy();

			options = Object.extend({
				multiple: false,
				batch: false,
				inline: false,
				progress: true,
				progressUrl: null,
				onSuccess: Prototype.emptyFunction,
				onFailure: Prototype.emptyFunction,
				onComplete: Prototype.emptyFunction
			}, options || {});

			wrapper = element.wrap('div');
			button = element.wrap('div', { 'class': '_pp_upload_input _pp_button' }).insert('Select File(s)...');
			element.setOpacity(0);

			changeListener = element.on('change', this.fileAdded.bindAsEventListener(this));

			listeners = [
				changeListener,
				Event.on(window, 'unload', this.destroy.bind(this))
			];
			if (options.inline)
				listeners.push(element.form.on('submit', this.submit.bindAsEventListener(this)));

			element.store('fileupload', this);

/**
 * Control.FileUpload#element -> Element
 * 
 * The currently active file input element for this control.
 *
 * Note: this is not static and may change over time for
 * multiple-file upload controls.
**/
			this.element = element;
			this.options = options;
			this.wrapper = wrapper;
			this.button = button;
			this.files = wrapper.appendChild(new Element('ul', { 'class': '_pp_upload_files' }));

			this.handler = this.createHandler();
			this.uploads = [];

			this.changeListener = changeListener;
			this.listeners = listeners;

		},

		createHandler: function() {
			if (typeof File != 'undefined'
					&& typeof Ajax.getTransport().upload != 'undefined'
					&& this.options.progress) {
				return new Control.FileUpload.AjaxHandler(this);
			} else {
				return new Control.FileUpload.IFrameHandler(this);
			}
		},

		fileAdded: function(e) {

			var file = this.element;

			var accepted = $H(this.handler.add(file));

			accepted.each(function(f) {

				var id = f.key;
				var name = f.value;

				if (!this.options.multiple) {
					for (var i = 0; i < this.uploads.length; i++) {
						this.cancel(i);
						this.uploads[i] && this.uploads[i].remove();
					}
				}

				var row = new Element('li');
				row.appendChild(new Element('div', { 'class': '_pp_upload_progress' }));
				row.appendChild(new Element('div', { 'class': '_pp_upload_label' })).update(name);
				row.appendChild(file);
				this.files.appendChild(row);

				if (this.options.multiple) {

					this.changeListener.stop();

					var remove = new Element('div', { 'class': '_pp_upload_change' });
					var icon = remove.appendChild(new Element('img', {
						'src': Protoplasm.base('upload')+'remove.png' }));
					icon.on('click', function(e) {
						if (!(id in this.uploads && this.handler.cancel(id)))
							row.remove();
						Event.stop(e);
					}.bindAsEventListener(this));
					row.insert({ top: remove });

					var newFile = file.clone();
					newFile.store('fileupload', this);
					var changeListener = newFile.on('change', this.fileAdded.bindAsEventListener(this));
					this.listeners.push(changeListener);
					this.changeListeners = changeListener;
					this.button.insert({ 'top': newFile });
					file.hide();

					this.element = newFile;

				} else {

					var change = new Element('div', { 'class': '_pp_upload_change' });
					var icon = change.appendChild(new Element('img', {
						'src': Protoplasm.base('upload')+'change.png' }));
					row.insert({ top: change });
					this.button.hide();

				}

				this.uploads[id] = row;

				if (!this.options.batch && this.options.inline)
					this.upload(id);

			}.bind(this));

		},

/**
 * Control.FileUpload#destroy() -> null
 *
 * Destroy this control and return the underlying element to
 * its original behavior.
**/
		destroy: function() {
			for (var i = 0; i < this.listeners.length; ++i)
				this.listeners[i].stop();
			this.wrapper.replace(this.element);
			this.element.show();
			this.element.store('fileupload', null);
		},

/**
 * Control.FileUpload#submit() -> null
 *
 * Upload all added files (has no effect unless batch mode is on.)
**/
		submit: function(e) {
			if (e) Event.stop(e);
			for (var i = 0; i < this.uploads.length; ++i) {
				this.upload(i);
			}
		},

		upload: function(id) {
			if (id in this.uploads) {
				var row = this.uploads[id];
				row.down('div._pp_upload_label').addClassName('_pp_upload_loading');
				this.handler.upload(id);
			}
		},

/**
 * Control.FileUpload#cancel() -> null
 *
 * Cancel all current uploads.
**/
		cancel: function() {
			for (var i = 0; i < this.uploads.length; ++i) {
				this.handler.cancel(i);
			}
		},

		onProgress: function(id, sent, total) {
			if (id in this.uploads) {
				var row = this.uploads[id];
				var width = row.getLayout().get('width')*(sent/total);
				row.down('div._pp_upload_progress').style.width = width+'px';
			}
		},

		onSuccess: function(id, filename, file) {
			this.options.onSuccess(filename);
			this.uploadComplete(id, filename, file, true);
		},

		onFailure: function(id, filename, file) {
			this.options.onFailure(filename);
			this.uploadComplete(id, filename, file, false);
		},

		uploadComplete: function(id, filename, file, succeeded) {
			if (id in this.uploads) {
				var row = this.uploads[id];
				var label = row.down('div._pp_upload_label')
				label.removeClassName('_pp_upload_loading');
				row.down('div._pp_upload_progress').remove();
				row.down('div._pp_upload_change').remove();
				if (succeeded) {
					row.addClassName('_pp_upload_success');
					label.addClassName('_pp_upload_complete');
				} else {
					row.addClassName('_pp_upload_error');
					label.addClassName('_pp_upload_failed');
				}
				delete this.uploads[id];
			}
			if (this.uploads.filter(Prototype.K).size() == 0)
				this.options.onComplete(filename);
			file.remove();
		},

		basename: function(f) {
			return f ? f.split(separator).pop() : f;
		},

		dirname: function(f) {
			return f && f.match(separator) ? f.split(separator).slice(0,-1).join('/') : '';
		}

	}

}());

Control.FileUpload.AjaxHandler = Class.create(function() {
	return {
		
		initialize: function(control) {

			this.control = control;
			this.action = control.element.form.action;
			this.method = control.element.form.method;

			this.params = null;
			if (fields = control.options.includeFields) {
				var values = {};
				var elements = control.element.form.elements;
				fields.each(function (f) { values[f] = elements[f].value });
				this.params = $H(values).toQueryString();
			}

			this.uploads = {};
			this.active = {};
		},

		add: function(file) {
			accepted = {};
			if (file.files) {
				$A(file.files).each(function(f) {
					var id = Control.FileUpload.activeCount++;
					this.uploads[id] = [file, f];
					accepted[id] = f.name;
				}.bind(this));
			} else {
				throw('Browser does not support XHR File API');
			}
			return accepted;
		},

		upload: function(id) {
			if (id in this.uploads) {

				u = this.uploads[id];
				var input = u[0];
				var file = u[1];
				var filename = file.name ? file.name : this.control.basename(file.value);

				var headers = { 'Content-Disposition': 'attachment; filename='+filename };
				if (this.params)
					headers['X-Upload-Parameters'] = this.params;

				var request = new Ajax.UploadRequest(this.action, {
					method: this.method,
					contentType: 'application/octet-stream',
					requestHeaders: headers,
					postBody: file,
					onProgress: function(loaded, total) {
						this.control.onProgress(id, loaded, total);
					}.bind(this),
					onSuccess: function(response) {
						delete this.uploads[id];
						if (this.active[id]) {
							delete this.active[id];
							this.control.onSuccess(id, filename, input);
						}
					}.bind(this),
					onFailure: function(response) {
						delete this.uploads[id];
						if (this.active[id]) {
							delete this.active[id];
							this.control.onFailure(id, filename, input);
						}
					}.bind(this)
				});

				this.active[id] = request;

			}

		},

		cancel: function(id) {
			if (id in this.uploads) {
				if (id in this.active) {

					var u = this.uploads[id];
					var input = u[0];
					var file = u[1];
					var filename = file.name ? file.name : this.control.basename(file.value);
				
					var transport = this.active[id].transport;
					delete this.active[id];
					transport.abort();

					this.control.onFailure(id, filename, input);

					return true;
				}
				delete this.uploads[id];
			}
			return false;
		}

	};
}());

Control.FileUpload.IFrameHandler = Class.create(function() {
	return {
		
		initialize: function(control) {
			this.control = control;
			this.progressUrl = control.options.progressUrl;

			var values = {};
			if (fields = control.options.includeFields) {
				var elements = control.element.form.elements;
				fields.each(function (f) { values[f] = elements[f].value });
			}
			this.params = $H(values);

			this.uploads = {};
		},

		add: function(file) {
			var id = Control.FileUpload.activeCount++;
			this.uploads[id] = file;
			accepted = {};
			if (file.multiple && file.files)
				accepted[id] = $A(file.files).pluck('name').join('<br />\n');
			else
				accepted[id] = this.control.basename(file.value);
			return accepted;
		},

		upload: function(id) {

			if (id in this.uploads) {

				file = this.uploads[id];
				file.store('parent', file.parentNode);

				var iframe = file.parentNode.appendChild(new Element('iframe', {
					'name': 'upload_iframe_'+id,
					'class': '_pp_upload_iframe' }));
				iframe.store('load', iframe.on('load', this.completeListener(
					id, file, this.control.onSuccess.bind(this.control))));
				iframe.store('error', iframe.on('error', this.completeListener(
					id, file, this.control.onFailure.bind(this.control))));

				var form = new Element('form', {
					action: file.form.action,
					method: file.form.method,
					enctype: 'multipart/form-data',
					target: iframe.name
					});

				form.store('iframe', iframe);
				form.appendChild(file);
				if (this.params.size()) {
					this.params.each(function(f) {
						form.appendChild(new Element('input', { 'type': 'hidden', 'name': f.key, 'value': f.value }));
					});
				}
				form.hide();
				document.body.appendChild(form);
				form.submit();

				if (this.progressUrl) {
					var handler = this.progressHandler(id, file);
					this.progressChecker = setTimeout(function() { handler(handler); }, 1000);
				}

				return [id];

			}

		},

		completeListener: function(id, file, callback) {
			return function(e) {
				file.form.remove();
				file.retrieve('parent').appendChild(file);
				if (callback) {
					if (file.multiple && file.files) {
						$A(file.files).each(function(f) {
							callback(id, f.name, file);
						});
					} else {
						callback(id, this.control.basename(file.value), file);
					}
				}
				if (this.progressChecker) {
					clearTimeout(this.progressChecker);
					this.progressChecker = null;
				}
			}.bind(this);
		},

		cancel: function(id) {
			if (id in this.uploads) {

				var file = this.uploads[id];
				var iframe = file.form.retrieve('iframe');
				delete this.uploads[id];

				if (iframe) {
					iframe.retrieve('load').stop();
					iframe.retrieve('error').stop();
					iframe.src = 'javascript:false;';
					this.completeListener(id, file, this.control.onFailure.bind(this.control))();
					return true;
				}

			}
			return false;
		},

		checkProgressLater: function(handler) {
			if (this.progressChecker)
				this.progressChecker = setTimeout(function() { handler(handler); }, 1000);
		},

		progressHandler: function(id, file) {

			if (this.progressUrl) {

				var params = this.progressUrl.toQueryParams();
				if (file.multiple && file.files)
					params.files = file.files.pluck('name').map(escape).join(',');
				else
					params.files = escape(this.control.basename(file.value));

				return function(next) {
					new Ajax.Request(this.progressUrl, {
						parameters: params,
						onSuccess: function(transport) {
							// TODO: what format should this response be in
							console.log(transport.responseText);
							this.checkProgressLater(next);
						}.bind(this),
						onFailure: function(transport) {
							this.checkProgressLater(next);
						}.bind(this)
					});
				}.bind(this);
			
			}

			return Prototype.emptyFunction;

		}

	};
}());

Control.FileUpload.activeCount = 0;

Ajax.UploadRequest = Class.create(Ajax.Request, {
	initialize: function($super, url, options) {
		Ajax.Base.prototype.initialize.bind(this)(options);
		this.transport = Ajax.getTransport();
		if (options.onProgress) {
			if (this.transport.upload) {
				this.transport.upload.addEventListener('progress', function(e) {
					options.onProgress(e.loaded, e.total);
				}.bindAsEventListener(this), false);
			} else {
				try {
					this.transport.onprogress = function(e) {
						options.onProgress(e.position, e.totalSize);
					}.bindAsEventListener(this);
				} catch(e) { }
			}
		}
		this.request(url);
	}
});

Protoplasm.register('upload', Control.FileUpload);
