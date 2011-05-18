if (typeof Protoplasm == 'undefined')
	throw('protoplasm.js not loaded, could not intitialize tabstrip');
if (window.Control == undefined) Control = {};

Protoplasm.loadStylesheet('tabstrip.css', 'tabstrip');

/**
 * class Control.TabStrip
 * 
 * Converts a tree of elements into a tab strip widget to switch between
 * panels of content.
 *
 * Control ID: `tabstrip`
 *
 * For the control to work correctly, the element tree should be formatted
 * like the following:
 *
 * 	<div class="tabstrip">
 * 		<ul>
 * 	    	<li>Tab 1</li>
 * 	    	<li>Tab 2</li>
 * 		</ul>
 * 		<div>
 * 	    	<div>Panel 1</div>
 * 	    	<div>Panel 2</div>
 * 		</div>
 * 	</div>
 *
 * Example: <a href="http://jongsma.org/software/protoplasm/control/tabstrip">Tab
 * Strip demo</a>
**/
Control.TabStrip = Class.create({

/**
 * new Control.TabStrip(element[, options])
 * - element (String | Element): A base `<div>` element (or DOM ID).
 * - options (Hash): Additional options for the control.
 *
 * Create a new tab strip from the given element.
 *
 * Additional options:
 *
 * * activeClass: The CSS class to assign to the active tab (default: 'active')
 * * disabledClass: The CSS class to assign to the active tab (default: 'disabled')
 * * onClick: A function to call when a tab is clicked.  The argument will be
 *   the tab element.
 * * disabled: A list of DOM id's of tabs that should start out disabled.
**/
	initialize: function(element, options) {

		element = $(element);

		if (ts = element.retrieve('tabstrip'))
			ts.destroy();

		element.addClassName('_pp_tabstrip');

		options = Object.extend({
				activeClass: 'active',
				disabledClass: 'disabled',
				onClick: Prototype.emptyFunction,
				disabled: false
			}, options || {});

/**
 * Control.TabStrip#element -> Element
 *
 * The underlying `<ul>` element passed to the constructor.
**/
		this.element = element;
		this.options = options;

		this.tabs = [];
		this.panels = [];
		this.active = -1;
		this.disabled = [];

		this.listeners = [ Event.on(window, 'unload', this.destroy.bind(this)) ];

		this.createTabs(element, options);

		if (options.activeTab)
			this.switchTab(options.activeTab);

		element.store('tabstrip', this);
		
	},

	createTabs: function(cont) {

		if (cont.childElements().length == 2) {

			var tabCont = cont.childElements()[0];
			tabCont.cleanWhitespace();
			tabCont.addClassName('_pp_tabstrip_tabs');
			var tabs = tabCont.childElements();
			var scroller = tabCont.wrap('div', {'class': '_pp_tabstrip_scroller'});
			this.scroller = scroller;

			var panelCont = cont.childElements()[1];
			panelCont.addClassName('_pp_tabstrip_panels');
			var panels = panelCont.childElements();

			var d = this.options.disabled;
			var dc = this.options.disabledClass;

			if (tabs.length == panels.length) {

				for (var i = 0; i < tabs.length; i++) {
					
					var self = this;
					this.listeners.push(tabs[i].on('click', function(tab) {
							return function(e) {
									if (!tab.id || !this.disabled.include(tab.id))
										this.switchTab(tab);
								}.bindAsEventListener(self)
						}(tabs[i])
					));
					// Block text selection
					this.listeners.push(tabs[i].on('mousedown', function(e) {
							Event.stop(e); return false; }.bindAsEventListener(this)));
					this.listeners.push(tabs[i].on('selectstart', function(e) {
							Event.stop(e); return false; }.bindAsEventListener(this)));

					if ((d && d.include(tabs[i].id)) || (dc && tabs[i].hasClassName(dc)))
						this.disable(tabs[i]);

				}

				panels.invoke('hide');

				this.tabs = tabs;
				this.panels = panels;

				var last = this.tabs[this.tabs.length-1].getLayout();
				var right = last.get('left') + last.get('width');
				if (right > scroller.getLayout().get('width')) {
					var scrollbars = new Element('div', {'class': '_pp_tabstrip_scroll'});
					var left = new Element('div', {'class': '_pp_tabstrip_scroll_left'});
					var right = new Element('div', {'class': '_pp_tabstrip_scroll_right'});
					this.makeScroller(left, tabCont, scroller, 20);
					this.makeScroller(right, tabCont, scroller, -20);
					scrollbars.insert(left);
					scrollbars.insert(right);
					scroller.insert(scrollbars);
				}

				this.switchTabByIndex(0);

			}

		}
	},

	makeScroller: function(button, content, container, scroll) {
		var pressed = false;
		button.on('mousedown', function(e) {
			pressed = true;
			var repeater;
			setTimeout(function() {
				if (pressed)
					repeater = setInterval(function() {
						if (pressed) {
							var l1 = content.getLayout();
							this.scrollTo(content, container, l1.get('left') + scroll);
						} else
							clearInterval(repeater);
					}.bind(this), 50);
			}.bind(this), 500);
			var l1 = content.getLayout();
			this.scrollTo(content, container, l1.get('left') + scroll);
		}.bindAsEventListener(this));
		button.on('mouseup', function(e) {
			pressed = false;
			}.bindAsEventListener(this));
		button.on('mouseout', function(e) {
			pressed = false;
			}.bindAsEventListener(this));
		button.on('selectstart', function(e) {
			Event.stop(e);
			}.bindAsEventListener(this));
	},

	scrollTo: function(content, container, left) {
		var last = content.childNodes[content.childNodes.length-1];
		var l1 = last.getLayout();
		var width = l1.get('left') + l1.get('margin-box-width');
		var l2 = container.getLayout();
		var max = 0;
		var min = -(width - l2.get('width') + 29 + 3);
		if (left < min)
			left = min;
		else if (left > max)
			left = max;
		content.style.left = left+'px';
	},

	scrollVisible: function(tab) {
		var content = this.scroller.firstChild;
		var l1 = tab.getLayout();
		var l2 = content.getLayout();
		var l3 = this.scroller.getLayout();
		var left = -l2.get('left');
		var right = left + (l3.get('width') - 29);
		var newleft = -left;
		if (l1.get('left') < left) {
			newleft = -(l1.get('left') - 6);
		} else if (l1.get('left') + l1.get('margin-box-width') > right) {
			var maxright = l1.get('left') + l1.get('margin-box-width');
			newleft = -left - (maxright - right) - 9;
		}
		if (newleft != -left)
			this.scrollTo(content, this.scroller, newleft);
	},

/**
 * Control.TabStrip#enable(tab) -> null
 * - tab (Element | String): The tab to enable (element or DOM id)
 *
 * Enable a previously disabled tab.
**/
	enable: function(tab) {
		var tab = $(tab);
		if (tab) {	
			tab.removeClassName(this.options.disabledClass);
			this.disabled = this.disabled.without(tab.id);
		}
	},

/**
 * Control.TabStrip#disable(tab) -> null
 * - tab (Element | String): The tab to disable (element or DOM id)
 *
 * Disable a tab so that it cannot be clicked.
**/
	disable: function(tab) {
		var tab = $(tab);
		if (tab) {	
			tab.addClassName(this.options.disabledClass);
			if (!this.disabled.include(tab.id))
				this.disabled.push(tab.id);
		}
	},

/**
 * Control.TabStrip#destroy() -> null
 *
 * Destroy this control and return the underlying element to
 * its original behavior.
**/
	destroy: function() {
		this.switchTabByIndex(0);
		this.listeners.invoke('stop');
		this.element.select('._pp_tabstrip_tabs').invoke(
			'removeClassName', '_pp_tabstrip_tabs');
		this.element.select('._pp_tabstrip_panels').invoke(
			'removeClassName', '_pp_tabstrip_panels');
		this.element.removeClassName('_pp_tabstrip');
		this.scroller.parentNode.replaceChild(this.scroller.firstChild, this.scroller);
		this.element.store('tabstrip', null);
	},

/**
 * Control.TabStrip#switchTab(tab) -> null
 * - tab (Element | String): The tab to switch to (element or DOM id)
 *
 * Switch the view to the specified tab.
**/
	switchTab: function(tab) {
		tab = $(tab);
		for (var i = 0; i < this.tabs.length; ++i)
			if (this.tabs[i] == tab)
				return this.switchTabByIndex(i);
	},

	switchTabByIndex: function(index) {
		var tab = this.tabs[index];
		if (this.active != index) {
			if (this.active > -1) {
				this.tabs[this.active].removeClassName(this.options.activeClass);
				this.panels[this.active].hide();
			}
			Element.addClassName(tab, this.options.activeClass);
			this.scrollVisible(tab);
			this.panels[index].show();
			this.active = index;
			if (this.options.onClick)
				this.options.onClick(tab);
		}
	}

});

Protoplasm.register('tabstrip', Control.TabStrip);
