if (typeof Protoplasm == 'undefined')
	throw('protoplasm.js not loaded, could not intitialize treelist');
if (window.Control == undefined) Control = {};

Protoplasm.loadStylesheet('treelist.css', 'treelist');

/**
 * class Control.TreeList
 * 
 * Creates a collapsible tree out of an unordered list
 * element.
 *
 * Control ID: `treelist`
 *
 * For the layout to work correctly, the list should be formatted
 * like the following (note that the sub-list items FOLLOW the
 * item they collapse under, rather than being inside the &lt;li&gt;):
 *
 * 	<ul class="treelist">
 * 	    <li>Item 1</li>
 * 	    <li>Item 2</li>
 * 	    <li>Submenu</li>
 * 	    <ul id="submenu">
 * 	        <li>Item 3</li>
 * 	        <li>Item 4</li>
 * 	    </ul>
 * 	</ul>
 *
 * Example: <a href="http://jongsma.org/software/protoplasm/control/treelist">Tree
 * List demo</a>
**/
Control.TreeList = Class.create({

/**
 * new Control.TreeList(element[, options])
 * - element (String | Element): A `<ul>` element (or DOM ID).
 * - options (Hash): Additional options for the control.
 *
 * Create a new tree list from the given `<ul>`
 * element.
 *
 * Additional options:
 *
 * * selectable: Allow clicking to select and highlight an item (default: true)
 * * onSelect: A function to call when an item is clicked on.
 *   Two arguments are passed: the opened item's `id` (or text content),
 *   and the `<li>` element itself.
 * * onOpen: A function to call when an item is double-clicked on.
 *   Two arguments are passed: the opened item's `id` (or text content),
 *   and the `<li>` element itself.
 * * childLoader: A callback function that dynamically loads submenu
 *   elements when a submenu is expanded.  The function takes two
 *   arguments: the submenu `<ul>` element's `id`, and a
 *   callback function to pass the child elements (as an array of
 *   `<li>` and `<ul>` elements.)  Only called the first time a
 *   menu is opened.
**/
	initialize: function(element, options) {

		element = $(element);

		if (c = element.retrieve('treelist'))
			c.destroy();

		options = Object.extend({
				'selectable': true
			}, options || {});

		var base = Protoplasm.base('treelist');
		if (!options.collapsedIcon)
			options.collapsedIcon = base+'collapsed.png';
		if (!options.collapsedHoverIcon)
			options.collapsedHoverIcon = base+'collapsed-hover.png';
		if (!options.expandedIcon)
			options.expandedIcon = base+'expanded.png';
		if (!options.expandedHoverIcon)
			options.expandedHoverIcon = base+'expanded-hover.png';

/**
 * Control.TreeList#element -> Element
 *
 * The underlying `<ul>` element passed to the constructor.
**/
		this.element = element;
		this.options = options;
		this.listeners = [
			element.on('selectstart', function(e) { Event.stop(e); }.bindAsEventListener(this)),
			element.on('mousedown', function(e) { Event.stop(e); }.bindAsEventListener(this)),
			Event.on(window, 'unload', this.destroy.bindAsEventListener(this))
		];
		this.selected = null;

		element.addClassName('_pp_treelist');

		this.extended = [
			Protoplasm.extend(element, { destroy: this.destroy.bind(this) })
		];

		element.select('li').each(this.initListItem.bind(this));

		element.store('treelist', this);
	},

/**
 * Control.TreeList#destroy() -> null
 *
 * Destroy this control and return the underlying element to
 * its original behavior.
**/
	destroy: function() {
		this.extended.each(Protoplasm.revert);
		this.listeners.invoke('stop');
		var e = this.element;
		// Remove icons
		e.select('._pp_treelist_icon').invoke('remove');
		e.select('ul').invoke('show');
		// Remove wrappers
		e.select('._pp_treelist_selectable').each(function(w) {
			while (w.firstChild)
				w.parentNode.insertBefore(
					w.firstChild, w.parentNode.firstChild);
			w.remove();
		});
		// Remove highlighted item
		e.select('._pp_highlight').invoke('removeClassName', '_pp_highlight');
		e.removeClassName('_pp_treelist');
		e.store('treelist', null);
	},

	initListItem: function(li) {

		var ul = li.next();
		var wrapper = new Element('span', { 'class': '_pp_treelist_selectable' });
		while(li.firstChild) wrapper.appendChild(li.firstChild);
		li.appendChild(wrapper);

		if (ul && ul.tagName == 'UL') {
			ul.hide();
			var icon = new Element('div', { 'class': '_pp_treelist_icon' });
			li.insert({ 'top': icon });
			var open = this.open(li, icon, ul);
			var close = this.close(li, icon, ul);
			var toggle = this.toggle(icon, open, close);
			this.listeners.push(icon.on('click', toggle));
			this.listeners.push(li.on('dblclick', toggle));
			this.extended.push(Protoplasm.extend(li, {
				open: open,
				close: close,
				toggle: toggle
				}));
		}

		if (this.options.onOpen)
			this.listeners.push(li.on('dblclick', open));

		if (this.options.selectable) {
			this.listeners.push(li.on('click', function(e) {
					if (this.selected)
						this.selected.removeClassName('_pp_highlight');
					wrapper.addClassName('_pp_highlight');
					this.selected = wrapper;
					this.select(li);
				}.bindAsEventListener(this)));
		}

	},

	close: function(li, icon, ul) {
		return function(e) {
			if (icon.hasClassName('_pp_treelist_icon_expanded')) {
				icon.removeClassName('_pp_treelist_icon_expanded');
				ul.select('ul').invoke('hide');
				ul.select('._pp_treelist_icon_expanded').invoke(
					'removeClassName', '_pp_treelist_icon_expanded');
				ul.hide();
			}
			if (e)
				Event.stop(e);
		}.bindAsEventListener(this);
	},

	open: function(li, icon, ul) {
		return function(e) {
			if (!icon.hasClassName('_pp_treelist_icon_expanded')) {
				icon.addClassName('_pp_treelist_icon_expanded');
				if (ul.childElements().length == 0)
					this.loadChildItems(ul);
				ul.show();
			}
			if (this.options.onOpen)
				this.options.onOpen(li.id ? li.id : li.textContent, li);
			if (e)
				Event.stop(e);
		}.bindAsEventListener(this);
	},

	toggle: function(icon, open, close) {
		return function(e) {
			if (icon.hasClassName('_pp_treelist_icon_expanded'))
				close();
			else
				open();
		}.bindAsEventListener(this);
	},

	loadChildItems: function(ul) {
		if (ul.id && this.options.childLoader) {
			var updater = this.listUpdater(ul);
			ul.update(new Element('li', { 'class': '_pp_treelist_loading' }).update('Loading...'));
			var children = this.options.childLoader(ul.id, updater);
			if (children)
				updater(children);

		}
	},

	listUpdater: function(ul) {
		return function(children) {
			ul.update();
			children.each(ul.insert.bind(ul));
			ul.select('li').each(this.initListItem.bind(this));
		}.bind(this);
	},

	select: function(li) {
		if (this.options.onSelect)
			this.options.onSelect(li.id ? li.id : li.textContent || li.innerText, li);
	}

});

Protoplasm.register('treelist', Control.TreeList);
