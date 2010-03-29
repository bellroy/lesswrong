
function submitballot(form)
{
    var ballots = {uh: modhash};
    ballots.comment = form.id
    
    for(var i = 0; i < form.elements.length; i++) {
        if(! form.elements[i].id || !id || 
           _id(form.elements[i]) == id) {
            var f = field(form.elements[i]);
            if (f) {
            	//ballots.append({"name": form.elements[i].name, "response": f});
                ballots["poll_" + form.elements[i].name] = f;
            }
        }
    }
    
    result = redditRequest('submitballot', ballots, null, true); 
    return false;
}

