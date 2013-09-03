/* Fill in the given help content, and attach a handler for the form invalidate submission */
function fillInHelpDiv(elem, content) {
  elem.innerHTML = content;
  elem.select('.invalidate').first().observe('submit', function(e) {
    e.stop();
    elem.innerHTML = "Loading..."
    new Ajax.Request(this.getAttribute('action'), {
      method: 'post',
      parameters: {'skiplayout': 'on'},
      onSuccess: function(response) {
        fillInHelpDiv(elem, response.responseText)
      }
    })
  });
}

/* Perform an ajax get for the help content, and fill in the element */
function getHelpContent(elem) {
  new Ajax.Request("/wiki/Commentmarkuphelp", {
    method: 'get',
    parameters: {'skiplayout': 'on'},
    onSuccess: function(response) {
      fillInHelpDiv(elem, response.responseText)
    }});
}

function helpon(link, what, newlabel) {
    var id = _id(link);
    show(what+id);

    /* If not loaded help content, load it! */
    if (/\s*Loading/.match($(what+id).innerHTML)) {
      getHelpContent($(what+id))
    }

    var oldlabel = link.innerHTML;
    if(newlabel) {
        link.innerHTML = newlabel;
    }
    link.onclick = function() {
        return helpoff(link, what, oldlabel);
    };
    link.blur();
    return false;
}

function helpoff(link, what, newlabel) {
    var id = _id(link);
    hide(what+id);
    var oldlabel = link.innerHTML;
    if(newlabel) {
        link.innerHTML = newlabel;
    }
    link.onclick = function() {
        return helpon(link, what, oldlabel);
    };
    link.blur();
    return false;
}


function Comment(id, context) {
    this.__init__(id, context);
    var edit_body = this.get("edit_body");
    if(edit_body) {
        this.text = decodeURIComponent(edit_body.innerHTML.replace(/\+/g, " "));
    }
};

Comment.prototype = new Thing();

Comment.del = Thing.del;

// Works like $(), except uses the parent of context instead of context itself
Comment.prototype.$parent = function (id, context) {
    context = context || this._context;
    return this.$(id, context && context.parentNode);
}

Comment.prototype.cloneAndReIDNodeOnce = function(id) {
    var s = this.$parent(id);
    if (s)
        return s;
    var template = $(id) || $(id + '_');  // '_' is optional, consistent with re_id_node
    return re_id_node(template.cloneNode(true), this._id);
};

Comment.prototype.show_editor = function(listing, where, text) {
    var edit_box = this.cloneAndReIDNodeOnce("samplecomment");
    if (edit_box.parentNode != listing.listing) {
        if (edit_box.parentNode) {
            edit_box.parentNode.removeChild(edit_box);
        }
        listing.insert_node_before(edit_box, where);
    }
    else if (edit_box.parentNode.firstChild != edit_box) {
        var p = edit_box.parentNode;
        p.removeChild(edit_box);
        p.insertBefore(edit_box, p.firstChild);
    }
    var box = this.$parent("comment_reply");
    clearTitle(box);
    box.value = text;
    box.setAttribute("data-orig-value", text);
    show(edit_box);
    BeforeUnload.bind(Comment.checkModified, this._id);
    return edit_box;
};

Comment.prototype.edit = function() {
    this.show_editor(this.parent_listing(), this.row, this.text);
    this.$parent("commentform").replace.value = "yes";
    this.hide();
};

Comment.prototype.showFlamebaitOverlay = function (edit_box) {
    var comment = this;
    var overlay = this.$("flamebaitcommentoverlay");
    if (overlay)
        return;

    overlay = this.cloneAndReIDNodeOnce("flamebaitcommentoverlay");
    jQuery(edit_box).children().hide();
    edit_box.appendChild(overlay);
    show(overlay);

    function hideWarning() {
        overlay.remove();
        jQuery(edit_box).find("form").show();
    }
    function cancel() {
        comment.cancel();
    }

    jQuery(overlay).find(".flamebaitcomment-yes").bind("click", hideWarning);
    jQuery(overlay).find(".flamebaitcomment-no").bind("click", cancel);
};

Comment.prototype.reply = function (showFlamebaitOverlay) {
    var edit_box = this.show_editor(this.child_listing(), null, '');
    this.$parent("commentform").replace.value = "";
    if (showFlamebaitOverlay)
        this.showFlamebaitOverlay(edit_box);
    else
        this.$parent("comment_reply").focus();
};

Comment.prototype.cancel = function() {
    var edit_box = this.cloneAndReIDNodeOnce("samplecomment");
    hide(edit_box);
    BeforeUnload.unbind(Comment.checkModified, this._id);
    this.show();
};

Comment.comment = function(r, context) {
    var id = r.id;
    var parent_id = r.parent;
    new Comment(parent_id, context).cancel();
    new Listing(parent_id, context).push(unsafe(r.content));
    new Comment(r.id, context).show();
    vl[id] = r.vl;
};

Comment.checkModified = function(id) {
    var textarea = $("comment_reply_" + id);
    if (textarea.value !== textarea.getAttribute("data-orig-value"))
        return "You've started typing a comment but haven't submitted it.";
};

/* Commenting on a link is handled by the Comment API so defer to it */
Link.comment = Comment.comment;

Comment.morechildren = function(r, context) {
    var c = new Thing(r.id, context);
    if(c.row) c.del();
    var parent = new Thing(r.parent, context).child_listing();
    parent.append(unsafe(r.content));

    c = new Thing(r.id, context);
    c.show(true);
    vl[r.id] = r.vl;

    highlightNewComments();
};

Comment.editcomment = function(r, context) {
    var com = new Comment(r.id, context);
    com.get('body').innerHTML = unsafe(r.contentHTML);
    com.get('edit_body').innerHTML = unsafe(r.contentTxt);
    com.cancel();
    com.show();
};

Comment.submitballot = function(r) {
    var com = new Comment(r.id);
    com.get('body').innerHTML = unsafe(r.contentHTML);
    com.cancel();
    com.show();
};

Comment.prototype.collapse = function() { 
    hide(this.get('child'));
    hide(this.get('display'));
    hide(this.get('arrows'));
    show(this.get('collapsed'));
};

Comment.prototype.uncollapse = function() { 
    show(this.get('child'));
    show(this.get('display'));
    show(this.get('arrows'));
    hide(this.get('collapsed'));
};
    
function all_morechildren(elem) {
  $$('.morechildren a').each(function(ahref, i) {
    ahref.simulate('click');
  });
  return false;
};

function morechildren(form, link_id, children, depth) {
    var id = _id(form);
    //console.log("id="+id+" form="+form+" link_id="+link_id+" children="+children+" depth="+depth);
    form.innerHTML = _global_loading_tag;
    form.style.color="red";
    var ajaxData = {link_id: link_id, children: children, depth: depth, id: id};
    var context = jQuery(form).closest(".comment")[0];

    function showChildren(res_obj) {
        var obj = res_obj.response && res_obj.response.object;
        if (obj && obj.length) {
            for (var o = 0, ol = obj.length; o < ol; ++o)
                Comment.morechildren(obj[o].data, context);
        }
    }

    redditRequest('morechildren', ajaxData, null, false, {cleanup_func: showChildren, handle_obj: false});
    return false;
};

function getAttrTime(e) { return parseInt(e.readAttribute('time')); }

function highlightNewComments(last) {
  if (!last) {
    var lastViewed = $("comment-visits");
    if (!lastViewed) {
      lastViewed = $('lastViewed');
      if (!lastViewed)
        return;
      last = getAttrTime(lastViewed);
    }
    else {
      last = lastViewed.options[lastViewed.selectedIndex].value;
    }
  }

  $$('div.comment').each(function(div, i) {
    var t = getAttrTime(div.select('.comment-date')[0]);
    if (last<=0) {
      div.removeClassName('new-comment')
    }
    else if (last<t) {
      div.addClassName('new-comment')
    }
    else {
      div.removeClassName('new-comment')
    }
  });
}

// Display the 'load all comments' if there any to be loaded
document.observe("dom:loaded", function() {
  if ($$('.morechildren a').length > 0) {
    var loadAll = $$('#loadAllComments').first();
    if (loadAll) loadAll.show();
  }

  highlightNewComments();
});


function editcomment(id, link) {
    new Comment(id, Thing.getThingRow(link)).edit();
};

function cancelReply(canceler) {
    new Comment(_id(canceler), Thing.getThingRow(canceler)).cancel();
};


function reply(id, link, showFlamebaitOverlay) {
    if (logged) {
        var com = new Comment(id, Thing.getThingRow(link)).reply(showFlamebaitOverlay);
    }
    else {
        showcover(true, 'reply_' + id);
    }
};

function chkcomment(form) {
    if(checkInProgress(form)) {
        var r = confirm("Request still in progress\n(click Cancel to attempt to stop the request)");
        if (r==false)
          tagInProgress(form, false);
        return false;
    }

    var action = form.replace.value ? 'editcomment' : 'comment';
    var context = Thing.getThingRow(form);

    tagInProgress(form, true);

    function cleanup_func(res_obj) {
        tagInProgress(form, false);

        var obj = res_obj && res_obj.response && res_obj.response.object;
        if (obj && obj.length)
            for (var o = 0, ol = obj.length; o < ol; ++o)
                Comment[action](obj[o].data, context);
    }

    return post_form(form, action, null, null, true, null, {
        handle_obj: false,
        cleanup_func: cleanup_func
    });
};

function tagInProgress(form, inProgress) {
  if (inProgress)
    form.addClassName("inprogress");
  else
    form.removeClassName("inprogress");
}

function checkInProgress(form) {
  return form.hasClassName("inprogress");
}

function clearTitle(box) {
    if (box.rows && box.rows < 7 || 
        box.style.color == "gray" ||
        box.style.color == "#808080") {
        box.value = "";
        box.style.color = "black";
        if (box.rows) { box.rows = 7;}
        try{
            box.focus();
        }
        catch(e) {};
    }
}

function hidecomment(id, link) {
    var com = new Comment(id, Thing.getThingRow(link));
    com.collapse();
    return false;
}

function showcomment(id, link) {
    var com = new Comment(id, Thing.getThingRow(link));
    com.uncollapse();
    return false;
}


Message = Comment;
Message.message = Comment.comment;


