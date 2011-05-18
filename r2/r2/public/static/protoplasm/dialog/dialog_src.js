if (typeof Protoplasm == 'undefined')
	throw('protoplasm.js not loaded, could not intitialize dialog');
if (typeof Effect == 'undefined')
	Protoplasm.useScriptaculous('effects');

/** section: Controls
 * Dialog
 * 
 * Namespace for all dialog classes.
**/
var Dialog = {

/**
 * Dialog.active -> Dialog.Base
 *
 * The currently displayed dialog window.
**/
	active: null,

/**
 * Dialog.close() -> null
 *
 * Close the currently active dialog window.
 *
 * Calls `Dialog.active.close()`
**/
	close: function() {
		if (Dialog.active)
			Dialog.active.close();
	},

/**
 * Dialog.success(value) -> null
 * - value (Object): The success callback value
 *
 * Close the active dialog window, and call any onSuccess callbacks.
 *
 * Internally calls `Dialog.active.success(value)`
**/
	success: function() {
		if (Dialog.active)
			Dialog.active.success();
	},

/**
 * Dialog.failure(value) -> null
 * - value (Object): The failure callback value
 *
 * Close the active dialog window, and call any onFailure callbacks.
 *
 * Internally calls `Dialog.active.failure(value)`
**/
	failure: function() {
		if (Dialog.active)
			Dialog.active.failure();
	}
}

/**
 * class Dialog.Base
 * 
 * Base class for all overlay dialogs.
**/
Dialog.Base = Class.create({
	
/**
 * new Dialog.Base(elt[, options])
 *
 * Create a new dialog window, using the given element as its
 * contents.
 *
 * Available options:
 *
 * * width: The dialog width in pixels
 * * height: The dialog width in pixels
 * * ignoreClicks: Ignore clicks outside the dialog
 *   (default: clicks close the dialog)
 * * ignoreEsc: Ignore presses of the ESC key
 *   (default: ESC closes the dialog)
 * * dialogClass: The class name to assign the dialog container
 * * onOpen: A callback function that is called when the dialog opens
 * * onClose: A callback function that is called when the dialog closes
 * * onSuccess: A callback function that is called when the dialog succeeds
 * * onFailure: A callback function that is called when the dialog fails
**/
	initialize: function(elt, options) {

		elt = $(elt);

		this.options = Object.extend({
			}, options || {});

		this.createComponents();

		this.contents = $(elt);
		this.dialog.appendChild(this.contents);

		this.keyListener = null;

		// Public API
		Object.extend(elt, {
			show: this.show.bind(this),
			hide: this.close.bind(this),
			success: this.success.bind(this),
			failure: this.failure.bind(this)
		});
	},

	createComponents: function() {

		if (!this.overlay) {

			this.overlay = new Element('div');

			this.overlay.setStyle({
					'position': 'fixed',
					'top': 0,
					'left': 0,
					'zIndex': 90,
					'width': '100%',
					'height': '100%',
					'backgroundColor': '#000',
					'display': 'none'
				});

			document.body.appendChild(this.overlay);
			if (!this.options.ignoreClicks)
				this.overlay.on('click', this.close.bindAsEventListener(this));

		}

		if (!this.dialog) {

			this.dialog = new Element('div');

			this.dialog.setStyle({
					'position': 'fixed',
					'display': 'none',
					'zIndex': 91
				});

			console.log(this.options.height);
			if (this.options.width || this.options.height) {
				this.dialog.style.overflow = 'auto';
				if (this.options.width)
					this.dialog.style.width = this.options.width + 'px';
				if (this.options.height)
					this.dialog.style.height = this.options.height + 'px';
			}

			if (this.options.dialogClass)
				this.dialog.addClassName(this.options.dialogClass);

			document.body.appendChild(this.dialog);

		}

	},

/**
 * Dialog.Base#baseShow() -> null
 *
 * Displays the dialog on the screen.  Subclasses that need
 * to override [[Dialog.Base#show]] should always call this
 * method.
**/
	baseShow: function() {

		if (this.shown && Dialog.active == this)
			return;

		Dialog.close();
		Dialog.active = this;

		if(typeof Effect == 'undefined') {
			this.overlay.show();
			this.dialog.show();
		} else {
			new Effect.Appear(this.overlay, { duration: 0.1, from: 0.0, to: 0.3 });
			new Effect.Appear(this.dialog, { duration: 0.1 });
		}

		this.resize();

		this.keyListener = document.on('keydown', function(e) {
			if (e.keyCode == Event.KEY_ESC) {
				if (!this.options.ignoreEsc)
					this.close();
				Event.stop(e);
			}
			if (!(Event.findElement(e, '#dialog_box')
					|| e.shiftKey || e.altKey
					|| e.metaKey || e.ctrlKey))
				Event.stop(e);
		}.bindAsEventListener(this));

		if (this.options.onOpen)
			this.options.onOpen(this.contents);

		this.shown = true;

	},

/** alias of: Dialog.Base#baseShow
 * Dialog.Base#show() -> null
 *
 * Display the dialog on the screen.
**/
	show: function() {
		this.baseShow();
	},

	resize: function() {

		var boxDims = Element.getDimensions(this.dialog);
		var contDims = Element.getDimensions(this.contents);
		var viewDims = document.viewport.getDimensions();

		this.dialog.style.left = ((viewDims.width - boxDims.width)/2) + 'px';

		if (boxDims.height > (viewDims.height - 100)) {
			// Scroll dialog, too tall
			var contDiff = boxDims.height - contDims.height;
			this.dialog.style.top = '50px';
			this.dialog.style.height = (viewDims.height - 100) + 'px';
			this.contents.style.height = (viewDims.height - 100 - contDiff) + 'px';
			this.contents.style.overflow = 'auto';
		} else {
			// Show dialog slightly higher than centered on the page
			this.dialog.style.top = ((viewDims.height - boxDims.height)/2)*.7 + 'px';
		}

	},
	
/**
 * Dialog.Base#close() -> null
 *
 * Close the dialog window, and call any onClose callbacks.
**/
	close: function(e) {

		if (!this.shown)
			return;

		if (this.keyListener) {
			this.keyListener.stop();
			this.keyListener = null;
		}

		if (Dialog.active == this)
			Dialog.active = null;

		if(typeof Effect == 'undefined') {
			this.overlay.hide();
			this.dialog.hide();
			if (this.options.onClose)
				this.options.onClose()
		} else {
			new Effect.Fade(this.overlay, { duration: 0.1 });
			new Effect.Fade(this.dialog, {
				duration: 0.1,
				afterFinish: function() {
					if (this.options.onClose)
						this.options.onClose()
				}.bind(this)});
		}

		if (this.options.onClose)
			this.options.onClose(this.contents);

		if (e)
			Event.stop(e);

		this.shown = false;

	},

/**
 * Dialog.Base#success(value) -> null
 * - value (Object): The success callback value
 *
 * Close the dialog window, and call any onSuccess callbacks.
**/
	success: function(value) {
		this.close();
		if (this.options.onSuccess)
			this.options.onSuccess(value, this.contents);
	},

/**
 * Dialog.Base#failure(value) -> null
 * - value (Object): The failure callback value
 *
 * Close the dialog window, and call any onFailure callbacks.
**/
	failure: function(value) {
		this.close();
		if (this.options.onFailure)
			this.options.onFailure(value, this.contents);
	}

});

/**
 * class Dialog.HTML < Dialog.Base
 * 
 * An overlay dialog with static HTML content.
**/
Dialog.HTML = Class.create(Dialog.Base, {

/**
 * new Dialog.HTML(elt[, options])
 *
 * Create a new dialog window, using the given element as its
 * contents.
 *
 * Available options:
 *
 * * width: The dialog width in pixels
 * * height: The dialog width in pixels
 * * ignoreClicks: Ignore clicks outside the dialog
 *   (default: clicks close the dialog)
 * * ignoreEsc: Ignore presses of the ESC key
 *   (default: ESC closes the dialog)
 * * dialogClass: The class name to assign the dialog container
 * * onClose: A callback function that is called when the dialog closes
 * * onSuccess: A callback function that is called when the dialog succeeds
 * * onFailure: A callback function that is called when the dialog fails
**/
	initialize: function($super, html, options) {
		if (Object.isString(html))
			$super(new Element('div').update(html), options);
		else
			$super(html, options);
	}

});

/**
 * class Dialog.Frame < Dialog.Base
 * 
 * An overlay dialog with static HTML content, styled using
 * the default window frame.
**/
Dialog.Frame = Class.create(Dialog.Base, {

/**
 * new Dialog.Frame(elt[, options])
 *
 * Create a new dialog window, using the given element or HTML
 * as its contents.
 *
 * Available options:
 *
 * * width: The dialog width in pixels
 * * height: The dialog width in pixels
 * * ignoreClicks: Ignore clicks outside the dialog
 *   (default: clicks close the dialog)
 * * ignoreEsc: Ignore presses of the ESC key
 *   (default: ESC closes the dialog)
 * * dialogClass: The class name to assign the dialog container
 * * onClose: A callback function that is called when the dialog closes
 * * onSuccess: A callback function that is called when the dialog succeeds
 * * onFailure: A callback function that is called when the dialog fails
**/
	initialize: function($super, title, html, options) {
		var elt = Object.isString(html) ? new Element('div').update(html) : html;
		var frame = new Element('div', { 'class': '_pp_dialog _pp_panel' });
		if (options && options.height) {
			frame.style.height = options.height+'px';
			delete options.height;
		}
		frame.appendChild(new Element('div', { 'class': '_pp_title' }).update(title));
		frame.appendChild(elt);
		$super(frame, options);
	}

});

/**
 * class Dialog.Ajax < Dialog.Base
 * 
 * An overlay dialog that fetches content from the server
 * via AJAX calls.
**/
Dialog.Ajax = Class.create(Dialog.Base, {

/**
 * new Dialog.Ajax(url[, options])
 *
 * Create a new dialog window, loading content from the
 * specified URL via XHR.  Any forms in the dialog will
 * be modified to submit via XHR, and the response will
 * be passed back to onSuccess or onFailure callbacks.
 *
 * Available options:
 *
 * * width: The dialog width in pixels
 * * height: The dialog width in pixels
 * * ignoreClicks: Ignore clicks outside the dialog
 *   (default: clicks close the dialog)
 * * ignoreEsc: Ignore presses of the ESC key
 *   (default: ESC closes the dialog)
 * * dialogClass: The class name to assign the dialog container
 * * loadingIcon: A loading icon to display while waiting for contents
 * * onClose: A callback function that is called when the dialog closes
 * * onSuccess: A callback function that is called when the dialog succeeds
 * * onFailure: A callback function that is called when the dialog fails
**/
	initialize: function($super, url, options) {
		$super(new Element('div'), options);
		this.url = url;
	},

	show: function() {

		var loading = '<div style="text-align: center; color: #999;">Loading...</div>';
		if (this.options.loadingIcon)
			loading = '<div style="text-align: center;"><img src="' +
				this.options.loadingIcon + '" /></div><br />' + loading;
			this.contents.update(loading);

		new Ajax.Updater(this.contents, this.url, {
			method: 'get',
			onComplete: function(response) {
			}
		});

		this.baseShow();

	}

});

Protoplasm.register('dialog', Dialog.HTML); 
