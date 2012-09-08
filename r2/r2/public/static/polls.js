var Poll = {};

Poll.submitBallot = function (form) {
    var ownerThing = Thing.getThingRow(form);
    var ownerThingID = _id(ownerThing);

    if (!logged) {
        showcover(true, "vote_" + ownerThingID);
        return;
    }

    var data = {uh: modhash, owner_thing: ownerThingID};

    for(var i = 0; i < form.elements.length; i++) {
        if(! form.elements[i].id || !id || 
           _id(form.elements[i]) == id) {
            var f = field(form.elements[i]);
            if (f) {
                data[form.elements[i].name] = f;
            }
        }
    }

    result = redditRequest('submitballot', data, null, true);
};
