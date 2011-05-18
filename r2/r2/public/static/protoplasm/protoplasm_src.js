// Only define once if multiple ?load=... instances are included
if (typeof Protoplasm == 'undefined') {

/**
 * class Protoplasm
 *
 * Protoplasm is the core class for the control framework.
 * On page load, [[Protoplasm.load]] is called, which initializes
 * the loading framework and enables the use of [[Protoplasm.use]].
 *
 * To use a control in a page, add the following code in your &lt;head&gt;
 * section:
 *
 * 	Protoplasm.use('datepicker');
 *
 * Once a control is loaded, the easiest way to use Protoplasm controls
 * is by using [[Protoplasm.transform]] to automatically create controls
 * out of all elements that match a CSS selector:
 *
 * 	Protoplasm.transform('datepicker', 'input.datepicker');
 *
 * Since [[Protoplasm.use]] returns a [[Protoplasm.Transformer]] instance,
 * a common shortcut is using method chaining to creating controls:
 *
 * 	Protoplasm.use('datepicker').transform('input.datepicker');
**/
	var Protoplasm = function() {

		var REQUIRED_PROTOTYPE = '1.7.0.0';
		var REQUIRED_SCRIPTACULOUS = '1.8.3';
		var protoUrl = 'https://ajax.googleapis.com/ajax/libs/prototype/'
			+REQUIRED_PROTOTYPE+'/prototype.js';
		var scriptyUrl = 'https://ajax.googleapis.com/ajax/libs/scriptaculous/'
			+REQUIRED_SCRIPTACULOUS+'/';

		var full = source = loaded = failed = used = false;
		var path;
		var scripts = [];
		var pending = [];
		var controls = {};

		return {

/**
 * Protoplasm.Version -> String
 *
 * The library version.
 **/
			Version: '0.1',

/**
 * Protoplasm.base(control) -> String
 * - control (String): A control identifier.
 *
 * Get the base URL for a specific control.
**/
			base: function(control) {
				return path+control+'/';
			},

/**
 * Protoplasm.load() -> null
 *
 * Initialize the framework.  This method is called automatically when
 * protoplasm.js is loaded.
**/
			load: function() {
				function convertVersionString(versionString) {
					var v = versionString.replace(/_.*|\./g, '');
					v = parseInt(v + '0'.times(4-v.length));
					return versionString.indexOf('_') > -1 ? v-1 : v;
				}

				failed = false;
				if (typeof Prototype=='undefined') {
					Protoplasm.require(protoUrl, Protoplasm.load);
					return;
				} else if (convertVersionString(Prototype.Version) <
							convertVersionString(REQUIRED_PROTOTYPE)) {
					failed = true;
					throw("Protoplasm requires the Prototype JavaScript framework >= " +
						REQUIRED_PROTOTYPE);
				}

				var js = /protoplasm(_[a-z]*)?\.js(\?.*)?$/;
				$$('head script[src]').findAll(function(s) {
					return s.src.match(js);
				}).each(function(s) {
					var matches = s.src.match(js),
						includes = s.src.match(/\?.*load=([a-z,]*)/);
					path = s.src.replace(js, '');
					loaded = true;
					// Full version, no need to include
					if (matches[1] == '_full') {
						full = true;
						Protoplasm.loadStylesheet(path+'protoplasm_full.css');
						return;
					}
					if (matches[1] == '_src')
						source = true;
					var toload = (includes ? includes[1].split(',') : pending);
					if (toload) toload.each(Protoplasm.use)
				});
			},

/**
 * Protoplasm.loadStylesheet(stylesheet[, control]) -> null
 * - stylesheet (String): The stylesheet URL.  If control is specified, this should be a relative path.
 * - control (String): A control identifier.
 *
 * Load a stylesheet into the current page.  If a control is specified, the
 * result of [[Protoplasm.base]](control) will be prepended to `stylesheet`.
**/
			loadStylesheet: function(stylesheet, control) {
				if (control)
					stylesheet = full
						? path+'/protoplasm_full.css'
						: path+control+'/'+stylesheet;
				if (!$$('head link[rel=stylesheet]').find(function(s) {
					return s.href == stylesheet;
				})) {
					var css = new Element('link', { 'rel': 'stylesheet', 'type': 'text/css', 'href': stylesheet });
					$$('head')[0].appendChild(css);
				}
			},

/**
 * Protoplasm.register(control, class) -> null
 * - control (String): The control identifier.
 * - class (Object): A reference to the control class.
 *
 * Register a control with the Protoplasm framework.  The `class` object 
 * must take a DOM Element as its first parameter.
**/
			register: function(control, constructor) {
				controls[control] = constructor;
			},

/**
 * Protoplasm.require(url[, callback]) -> null
 * - url (String): The script URL to include.  Scripts will only be included
 *   once - subsequent calls for the same URL will do nothing.
 * - callback (Function): A callback function that will be called when the
 *   script is loaded and ready to use.
 *
 * Include a remote javascript file for use in the current page.  If a `callback`
 * is specified, it will be called when the script is loaded and ready to use.
**/
			require: function(url, callback) {
				if (scripts.indexOf(url) > -1) {
					if (callback) callback();
					return;
				}
				scripts.push(url);
				try {
					if (document.loaded)
						throw('Already loaded');
					// Pre-dom:loaded, writing out script tag ensures proper execution order
					document.write('<scr'+'ipt type="text/javascript" src="'+url+'"><\/scr'+'ipt>');
					if (callback) {
						var cb = '_script_onload_'+scripts.length;
						window[cb] = callback;
						document.write('<scr'+'ipt type="text/javascript">');
						document.write('window.'+cb+'(); delete window.'+cb+';');
						document.write('<\/scr'+'ipt>');
					}
				} catch(e) {
					// Fall back to DOM methods
					var done = false;
					var script = new Element('script', { 'type': 'text/javascript', 'src': url });
					if (callback) {
						script.onload = script.onreadystatechange = function() {
							var rs = this.readyState;
							if (done || (rs && rs != 'complete' && rs != 'loaded')) return;
							done = true;
							callback();
						};
					}
					$$('head')[0].appendChild(script);
				}
			},

/**
 * Protoplasm.transform(control, selector) -> Protoplasm.Transformer
 * - control (String): A control identifier.
 * - selector (String): A CSS selector rule.
 *
 * Transform all elements in the document that match `selector`
 * into the specified `control`. If this method is called before the
 * document is loaded, it will execute in the document's `dom:loaded`
 * event.
**/
			transform: function(control, selector) {
				var params = Array.prototype.slice.call(arguments, 2);
				function transformer(e) {
					if (control in controls)
						$$(selector).each(function(elt) {
							var c = new controls[control](elt, params[0], params[1], params[2], params[3]);
						});
				}
				if (document.loaded)
					transformer();
				else
					document.on('dom:loaded', transformer);
				return new Protoplasm.Transformer(control);
			},

/**
 * Protoplasm.use(control[, callback]) -> Protoplasm.Transformer
 * - control (String): A control identifier.
 * - callback (Function): A callback function that will be called when the
 *   control is ready to use.
 *
 * Include a control for use in the current page.
**/
			use: function(control, callback) {
				if (Object.isArray(control)) {
					control.each(Protoplasm.use);
					return;
				}
				if (failed)
					throw("Protoplasm loading failed, cannot include controls");
				else if (!loaded)
					pending.push(control);
				else if (!full && !(control in controls)) {
					used || Protoplasm.loadStylesheet(path+'protoplasm.css');
					used = true;
					Protoplasm.require(path+control+'/'+control+(source?'_src':'')+'.js', callback);
				}
				return new Protoplasm.Transformer(control);
			},

/**
 * Protoplasm.useScriptaculous(lib[, callback]) -> null
 * - lib (String): The script.aculo.us library to load
 * - callback (Function): A callback function that will be called when the
 *   library is ready to use.
 *
 * Include a script.aculo.us library.
 *
 * 	// Load script.aculo.us effects.js
 * 	Protoplasm.useScriptaculous('effects');
**/
			useScriptaculous: function(lib, callback) {
				Protoplasm.require(scriptyUrl+lib+'.js', callback);
			},

/**
 * class Protoplasm.Transformer
 *
 * Enables method chaining from [[Protoplasm.use]] calls.
**/

/**
 * new Protoplasm.Transformer(control)
 * - control (String): A control identifier.
 *
 * Enables method chaining from [[Protoplasm.use]] calls.
**/
			Transformer: function(control) {
				return {

/** alias of: Protoplasm.use
 * Protoplasm.Transformer#use(control[, callback]) -> Protoplasm.Transformer
 * - control (String): A control identifier.
 * - callback (Function): A callback function that will be called when the
 *   control is ready to use.
 *
 * Include a control for use in the current page.
**/
					use: Protoplasm.use,

/**
 * Protoplasm.Transformer#transform(selector) -> Protoplasm.Transformer
 * - selector (String): A CSS selector rule.
 *
 * Transform all elements in the document that match `selector`
 * into the same control from the previous method in this chain.
 * If this method is called before the document is loaded, it
 * will execute in the document's `dom:loaded` event.
**/
					transform: function() {
						var args = Array.prototype.slice.call(arguments, 0);
						args.unshift(control);
						return Protoplasm.transform.apply(Protoplasm, args);
					}
				}
			},

/**
 * Protoplasm.extend(element, methods) -> Element
 * - element (Element | String): The element to extend
 * - methods (Hash): A hash of methods to extend the element with
 *
 * Adds the given methods to `element` in a reversible way.
 *
 * See [[Protoplasm.revert]]
**/
			extend: function(e, x) {
				e = $(e);
				x = $H(x);
				x.each(function(i) {
					if (i.key in e)
						e['_'+i.key] = e[i.key];
					e[i.key] = i.value;
				});
				e.store('_extensions', x);
				return e;
			},

/**
 * Protoplasm.revert(element) -> Element
 * - element (Element | String): The element to revert
 *
 * Reverts an element that was previously extended with
 * [[Protoplasm.extend]] to its original state.
 *
 * See [[Protoplasm.extend]]
**/
			revert: function(e) {
				e = $(e);
				var ext = e.retrieve('_extensions');
				if (ext) {
					ext.each(function(i) {
						if ('_'+i.key in e) {
							e[i.key] = e['_'+i.key];
							e['_'+i.key] = null;
						} else {
							e[i.key] = null;
						}
					});
				}
				return e;
			}

		}

	}();

}

// Call after every include to grab new ?load=... controls
Protoplasm.load();

/**
 * == Controls ==
 *
 * Control reference.
**/

/** section: Controls
 * Control
 *
 * Namespace for all Protoplasm user input controls.
**/
