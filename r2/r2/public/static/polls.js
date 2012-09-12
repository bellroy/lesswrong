var Poll = {};

Poll.submitBallot = function (form) {
    var ownerThing = Thing.getThingRow(form);
    var ownerThingID = _id(ownerThing);
    var votingArea = jQuery(form).find(".poll-voting-area");

    if (!logged) {
        showcover(true, "vote_" + ownerThingID);
        return;
    }

    var data = {uh: modhash, owner_thing: ownerThingID};

    for(var i = 0; i < form.elements.length; i++) {
        var value = field(form.elements[i]);
        if (value)
            data[form.elements[i].name] = value;
    }

    function done() {
        votingArea.removeClass("inprogress");
    }

    votingArea.addClass("inprogress");
    result = redditRequest("submitballot", data, null, true, {cleanup_func: done});
};
