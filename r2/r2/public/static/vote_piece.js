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

function set_score(id, dir) {
    var label = vl[id];
    var score = $("score_" + id);
    if(score) {
        score.className = scorecls[dir+1];
        score.innerHTML = label   [dir+1];
    }
}

function castVote(button, voteHash) {
    //logged is global
    var id = _id(button)
    var thing = new Thing(id, Thing.findThingRow(button))
    var up = thing.$("up");
    var down = thing.$("down");
    var status = thing.$("status");
    var dir = /\bmod\b/.test(button.className) ? 0 : button === up ? 1 : -1;
    var old_dir = up.className === upm ? 1 : down.className === downm ? -1 : 0;

    if (logged) {
        // Ensure the status field for this vote is hidden.
        if (status) hide(status);

        // Create the standard worker fn to handle the response.  It
        // will take care of updating and showing the status field.
        var action = 'vote';
        worker = handleResponse(action);

        function hard_worker(r) {
            // Invoke the standard worker to update and show the
            // status field if appropriate.
            worker(r);

            var r = parse_response(r).response;
            if (r && r.update) {
                // The ajax response did update and show the status
                // field so the vote was unsuccessful.  Update the vote
                // buttons and the score.
                up.className    = upcls   [old_dir+1];
                down.className  = downcls [old_dir+1];
                set_score(id, old_dir);
            }
        }

        // Initiate the ajax request to vote.
        redditRequest(action, {id: id, uh: modhash, dir: dir, vh: voteHash || ""}, hard_worker);
    }

    // Update the vote buttons and the score.
    up.className    = upcls   [dir+1];
    down.className  = downcls [dir+1];
    set_score(id, dir);
}
