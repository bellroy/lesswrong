if (typeof Protoplasm == 'undefined')
	throw('protoplasm.js not loaded, could not intitialize accordion');
if (window.Control == undefined) Control = {};

/**
 * class Control.Accordion
 * 
 * Stacked title bars slide up and down to reveal different
 * sections of content.
**/
Control.Accordion = Class.create({

	initialize: function(container, options) {
		this.container = $(container);
		this.lastExpandedTab = null;
		this.accordionTabs = new Array();
		this.setOptions(options);
		this._attachBehaviors();

		// Set the initial visual state...
		for (var i=1; i < this.accordionTabs.length; i++) {
			this.accordionTabs[i].collapse();
			this.accordionTabs[i].content.style.display = 'none';
		}

		this.lastExpandedTab = this.accordionTabs[0];
		// TODO: Determine height from parent div?
		this.lastExpandedTab.content.style.height = this.options.panelHeight + "px";
		this.lastExpandedTab.showExpanded();
	},

	setOptions: function(options) {
		this.options = Object.extend({
			panelHeight: 200,
			onHideTab: null,
			onShowTab: null
		}, options || {});
	},

	showTabByIndex: function(anIndex, animate) {
		var doAnimate = arguments.length == 1 ? true: animate;
		this.showTab(this.accordionTabs[anIndex], doAnimate);
	},

	showTab: function(accordionTab, animate, skipCallback) {

		var doAnimate = arguments.length == 1 ? true: animate;

		if (this.options.onHideTab)
			this.options.onHideTab(this.lastExpandedTab);

		this.lastExpandedTab.showCollapsed(); 
		this.lastExpandedTab.content.style.height = (this.options.panelHeight - 1) + 'px';
		accordionTab.content.style.display = '';

		var accordion = this;
		var lastExpandedTab = this.lastExpandedTab;

		if (doAnimate) {
			new Control.Accordion.Animation(this.lastExpandedTab.content,
									accordionTab.content,
									1,
									this.options.panelHeight,
									100, 10,
									{ complete: function() { accordion.showTabDone(lastExpandedTab, skipCallback); } }
								);
			this.lastExpandedTab = accordionTab;
		} else {
			this.lastExpandedTab.content.style.height = "1px";
			accordionTab.content.style.height = this.options.panelHeight + "px";
			this.lastExpandedTab = accordionTab;
			this.showTabDone(lastExpandedTab);
		}
	},

	showTabDone: function(collapsedTab, skipCallback) {
		collapsedTab.content.style.display = 'none';
		this.lastExpandedTab.showExpanded();
		if (!skipCallback && this.options.onShowTab)
			this.options.onShowTab(this.lastExpandedTab);
	},

	_attachBehaviors: function() {
		var panels = this._getDirectChildrenByTag(this.container, 'DIV');
		for (var i = 0; i < panels.length; i++) {
			var tabChildren = this._getDirectChildrenByTag(panels[i],'DIV');
			if (tabChildren.length != 2)
				continue; // unexpected
			var tabTitleBar = tabChildren[0];
			var tabContentBox = tabChildren[1];
			this.accordionTabs.push(new Control.Accordion.Tab(this,tabTitleBar,tabContentBox));
		}
	},

	_getDirectChildrenByTag: function(e, tagName) {
		var kids = new Array();
		var allKids = e.childNodes;
		for(var i = 0; i < allKids.length; i++)
			if (allKids[i] && allKids[i].tagName && allKids[i].tagName == tagName)
				kids.push(allKids[i]);
		return kids;
	}

});

Control.Accordion.Tab = Class.create({

	initialize: function(accordion, titleBar, content) {
		this.accordion = accordion;
		this.titleBar = titleBar;
		this.content = content;
		this._attachBehaviors();
	},

	collapse: function() {
		this.showCollapsed();
		this.content.style.height = "1px";
	},

	showCollapsed: function() {
		this.expanded = false;
		if (this.accordion.options.collapsedClass)
			this.titleBar.className = this.accordion.options.collapsedClass
		this.content.style.overflow = "hidden";
	},

	showExpanded: function() {
		this.expanded = true;
		if (this.accordion.options.expandedClass)
			this.titleBar.className = this.accordion.options.expandedClass;
		this.content.style.overflow = "visible";
	},

	titleBarClicked: function(e) {
		if (this.accordion.lastExpandedTab != this)
			this.accordion.showTab(this);
	},

	hover: function(e) {
		if (!this.expanded && this.accordion.options.hoverClass)
			this.titleBar.className = this.accordion.options.hoverClass;
	},

	unhover: function(e) {
		if (this.expanded) {
			if (this.accordion.options.expandedClass)
				this.titleBar.className = this.accordion.options.expandedClass;
		} else {
			if (this.accordion.options.collapsedClass)
				this.titleBar.className = this.accordion.options.collapsedClass;
		}
	},

	_attachBehaviors: function() {
		this.titleBar.onclick = this.titleBarClicked.bindAsEventListener(this);
		this.titleBar.onmouseover = this.hover.bindAsEventListener(this);
		this.titleBar.onmouseout = this.unhover.bindAsEventListener(this);
	}
});

Control.Accordion.Animation = Class.create({

   initialize: function(e1, e2, start, end, duration, steps, options) {
      this.e1       = $(e1);
      this.e2       = $(e2);
      this.start    = start;
      this.end      = end;
      this.duration = duration;
      this.steps    = steps;
      this.options  = arguments[6] || {};

      this.accordionSize();
   },

   accordionSize: function() {

      if (this.isFinished()) {
         // just in case there are round errors or such...
         this.e1.style.height = this.start + "px";
         this.e2.style.height = this.end + "px";

         if(this.options.complete)
            this.options.complete(this);
         return;
      }

      if (this.timer)
         clearTimeout(this.timer);

      var stepDuration = Math.round(this.duration/this.steps) ;

      var diff = this.steps > 0 ? (parseInt(this.e1.offsetHeight) - this.start)/this.steps : 0;
      this.resizeBy(diff);

      this.duration -= stepDuration;
      this.steps--;

      this.timer = setTimeout(this.accordionSize.bind(this), stepDuration);
   },

   isFinished: function() {
      return this.steps <= 0;
   },

   resizeBy: function(diff) {
      var h1Height = this.e1.offsetHeight;
      var h2Height = this.e2.offsetHeight;
      var intDiff = parseInt(diff);
      if ( diff != 0 ) {
         this.e1.style.height = (h1Height - intDiff) + "px";
         this.e2.style.height = (h2Height + intDiff) + "px";
      }
   }

});

Protoplasm.register('accordion', Control.Accordion);
