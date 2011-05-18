if (typeof Protoplasm == 'undefined')
	throw('protoplasm.js not loaded, could not intitialize treeselect');
if (window.Control == undefined) Control = {};

/**
 * class Control.TreeSelect
 * 
 * Creates a heirarchical select list.
 *
 * Written and maintained by Jeremy Jongsma (jeremy@jongsma.org)
**/
Control.TreeSelect = function(element, options) {

	// Private members
	var showTimer = null;

	function trim(str) {
		str = str.replace(/^\s+/, '');
		for (var i = str.length - 1; i >= 0; i--) {
			if (/\S/.test(str.charAt(i))) {
				str = str.substring(0, i + 1);
				break;
			}
		}
		return str;
	}

	function findElementsByClassName(classname, root) {
		var res = [];
		var elts = (root||document).getElementsByTagName('*')
		var re = new RegExp('\\b'+classname+'\\b');
		for (var i = 0; i < elts.length; ++i)
			if (elts[i].className.match(re))
				res[res.length] = elts[i];
		return res;
	}

	function addClass(el, c) {
		cl = el.className ? el.className.split(/ /) : [];
		for (var i = 0; i < cl.length; ++i)
			if (cl[i] == c)
				return;
		cl[cl.length] = c;
		el.className = cl.join(' ');
	}

	function removeClass(el, c) {
		if (!el.className) return;
		cl = el.className.split(/ /);
		var nc = [];
		for (var i = 0; i < cl.length; ++i)
			if (cl[i] != c)
				nc[nc.length] = cl[i];
		el.className = nc.join(' ');
	}

	function stopEvent(e) {
		var ev = window.event||e;
		if (ev.stopPropagation)
			ev.stopPropagation();
		else
			ev.cancelBubble = true;
	}

	function addEvent(el, name, handler) {
		if (el.addEventListener) {
			el.addEventListener(name, handler, false);
		} else {
			el.attachEvent('on'+name, handler);
		}
	}

	function removeEvent(el, name, handler) {
		if (el.removeEventListener) {
			el.removeEventListener(name, handler, false);
		} else {
			el.detachEvent('on'+name, handler);
		}
	}

	function selectItem(li) {
		return function(e) {
			if (showTimer) {
				clearTimeout(showTimer);
				showTimer = null;
			}
			listvalue.value = li.id;
			if (listname.nodeName.toUpperCase() == 'INPUT')
				listname.value = trim(li.childNodes[0].nodeValue);
			else
				listname.innerHTML = trim(li.childNodes[0].nodeValue);
			stopEvent(e);
			hideList(e);
			return false;
		}
	}

	function openItem(li) {
		return function(e) {
			if (showTimer) {
				clearTimeout(showTimer);
				showTimer = null;
			}
			showTimer = setTimeout(function() {
				var show = [];
				if (li.getElementsByTagName('ul').length)
					show[0] = li.getElementsByTagName('ul')[0];
				var p = li.parentNode;
				while (p && p != element) {
					if (p.nodeName.toUpperCase() == 'UL')
						show[show.length] = p;
					p = p.parentNode;
				}
				var hide = [];
				var uls = element.getElementsByTagName('ul');
				for (var i = 0; i < uls.length; ++i) {
					var found = false;
					for (var j = 0; j < show.length; ++j)
						if (show[j] == uls[i]) {
							found = true;
							break;
						}
					if (!found)
						hide[hide.length] = uls[i];
				}

				for (var i = 0; i < show.length; ++i) {
					show[i].style.display = 'block';
					show[i].style.zIndex = 99;
					addClass(show[i].parentNode, 'active');
				}
				for (var i = 0; i < hide.length; ++i) {
					hide[i].style.display = 'none';
					hide[i].style.zIndex = 0;
					removeClass(hide[i].parentNode, 'active');
				}
				showTimer = null;
				}, 200);
			stopEvent(e);
			return false;
		}
	}

	function addListBehavior(li) {
		if (!li.id && li.getElementsByTagName('ul').length)
			addEvent(li, 'click', openItem(li));
		else
			addEvent(li, 'click', selectItem(li));
		addEvent(li, 'mouseover', openItem(li));
		var sublists = li.getElementsByTagName('ul');
		if (sublists.length)
			addClass(li, 'submenu');
	}

	// Constructor
	var listvalue = findElementsByClassName('itemvalue', element)[0];
	var listname = findElementsByClassName('itemname', element)[0];
	var datalist = element.getElementsByTagName('ul')[0];

	function toggleList(e) {
		if (datalist.style.display == 'block')
			datalist.style.display = 'none';
		else {
			return showList(e);
		}
	}

	function showList(e) {
		datalist.style.display = 'block';
		addEvent(document, 'click', hideList);
		stopEvent(e);
		return false;
	}

	function hideList(e) {
		var uls = datalist.getElementsByTagName('ul');
		for (var i = 0; i < uls.length; ++i) {
			uls[i].style.display = 'none';
			uls[i].style.zIndex = 0;
			removeClass(uls[i].parentNode, 'active');
		}
		datalist.style.display = 'none';
		removeEvent(document, 'click', hideList);
	}

	var dropdown = document.createElement('img');
	dropdown.src = '/images/dropdown.png';
	dropdown.style.verticalAlign = 'middle';
	if (listname.nextSibling)
		listname.parentNode.insertBefore(dropdown, listname.nextSibling);
	else
		listname.parentNode.appendChild(dropdown);

	addEvent(dropdown, 'click', toggleList);
	addEvent(listname, 'click', showList);
	listname.readOnly = true;

	var listitems = element.getElementsByTagName('li');
	for (var i = 0; i < listitems.length; ++i)
		addListBehavior(listitems[i]);

	return {
		// Public members
		'element': element
	}
}

Protoplasm.register('treeselect', Control.TreeSelect);
