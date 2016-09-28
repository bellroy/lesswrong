var upm = "up mod";
var upr = "up";
var downm = "down mod";
var downr = "down";

var upcls    = [upr,   upr,   upm  ];
var downcls  = [downm, downr, downr];
var scorecls = ["votes dislikes", "votes", "votes likes"];


//cookie setting junk
function cookieName(name) {
    return (logged || '') + "_" + name;
}

function createLCookie(name,value,days) {
    var domain = "; domain=" + cur_domain;
    if (days) {
        var date = new Date();
        date.setTime(date.getTime()+(days*24*60*60*1000));
        var expires="; expires="+date.toGMTString();
    }
    else expires="";
    document.cookie=name+"="+ escape(value) +expires+domain+"; path=/";
}

function createCookie(name, value, days) {
  return createLCookie(cookieName(name), value, days);
}

function readLCookie(nameEQ) {
    nameEQ=nameEQ+'=';
    var ca=document.cookie.split(';');
    /* walk the list backwards so we always get the last cookie in the list */
    for(var i = ca.length-1; i >= 0; i--) {
        var c = ca[i];
        while(c.charAt(0)==' ') c=c.substring(1,c.length);
        if(c.indexOf(nameEQ)==0) {
          /* we can unescape even if it's not escaped */
          return unescape(c.substring(nameEQ.length,c.length));
        }
    }
    return '';
}

function readCookie(name) {
    var nameEQ=cookieName(name);
    return readLCookie(nameEQ);
}

/*function setModCookie(id, c) {
    createCookie("mod", readCookie("mod") + id + "=" + c + ":");
    }*/

function set_score(id, dir, context) {
    var label = vl[id];
    var score = context ? jQuery(context).find("#score_" + id)[0] : $("score_" + id);
    if(score) {
        score.className = scorecls[dir+1];
        score.textContent = label[dir+1]['label'];
        jQuery(score).qtip('option', 'content.text', label[dir+1]['hover']);
    }
}

function castVote(button, voteHash) {
    if (!logged)
        return

    voteHash = voteHash || "";
    var id = _id(button);
    var thing = new Thing(id, Thing.getThingRow(button));
    var up = thing.$("up");
    var down = thing.$("down");
    var status = thing.$("status");
    var spinner = thing.$("votespinner");
    var dir = /\bmod\b/.test(button.className) ? 0 : button === up ? 1 : -1;

    if (status)
        hide(status);

    function cleanup_func(r) {
        $(spinner.parentNode).removeClassName("inprogress");

        if (r.response && r.response.update)  // "update" is only set on errors
            return;

        var things = Thing.findAll(id);
        for (var t = 0, tl = things.length; t < tl; ++t) {
            var up = things[t].$("up"),
                down = things[t].$("down");
            if (up && down) {
                things[t].$("up").className    = upcls   [dir+1];
                things[t].$("down").className  = downcls [dir+1];
                set_score(id, dir, things[t].row);
            }
        }
    }

    // Initiate the ajax request to vote.
    var data = {id: id, uh: modhash, dir: dir, vh: voteHash};
    redditRequest("vote", data, null, false, {cleanup_func: cleanup_func});
    $(spinner.parentNode).addClassName("inprogress");
}
