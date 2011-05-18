if (typeof Protoplasm == 'undefined')
	throw('protoplasm.js not loaded, could not intitialize expander');
if (window.Control == undefined) Control = {};

/**
 * class Control.Expander
 * 
 * Expands / hides a content panel when the header is clicked. 
**/
Control.Expander = Class.create({
	initialize: function(container, options) {
		this._initialize(container, options);
	},
	_initialize: function(container, options) {
		this.container = $(container);
		this.options = Object.extend({
				expandedClass: null,
				collapsedClass: null,
				hoverClass: null,
				triggerElement: null,
				onexpand: Prototype.emptyFunction,
				oncollapse: Prototype.emptyFunction
			}, options || {});

		Element.cleanWhitespace(this.container);
		if (this.container.childNodes.length == 2) {
			this.title = this.container.childNodes[0];
			this.body = this.container.childNodes[1];
			this.trigger = this.options.triggerElement || this.title;
		}

		if (!this.options.expand)
			this.collapse(true);

		this.applyBehavior(this.trigger, this.body);
	},
	applyBehavior: function(trigger, body) {
		trigger.onclick = function(e) {
				if(this.expanded)
					this.collapse();
				else
					this.expand();
			}.bindAsEventListener(this);
		trigger.onmouseover = this.hover.bindAsEventListener(this);
		trigger.onmouseout = this.restore.bindAsEventListener(this);
		// Block text selection
		trigger.onmousedown = function(e) { return false; }.bindAsEventListener(this);
		trigger.onselectstart = function(e) { return false; }.bindAsEventListener(this);
	},
	expand: function() {
		Element.removeClassName(this.title, this.options.collapsedClass);
		Element.addClassName(this.title, this.options.expandedClass);
		this.body.style.display = 'block';
		this.expanded = true;
		if (this.options.onexpand)
			this.options.onexpand(this);
	},
	collapse: function(noEvent) {
		Element.removeClassName(this.title, this.options.expandedClass);
		Element.addClassName(this.title, this.options.collapsedClass);
		this.body.style.display = 'none';
		this.expanded = false;
		if (this.options.oncollapse && !noEvent)
			this.options.oncollapse(this);
	},
	hover: function() {
		Element.addClassName(this.title, this.options.hoverClass);
	},
	restore: function() {
		Element.removeClassName(this.title, this.options.hoverClass);
	}
});

Protoplasm.register('expander', Control.Expander);
