function login(){
  var details = {
    "username": document.getElementById("username").value,
    "password": document.getElementById("password").value
  };

  var req = new ApiRequest("login");

  req.setCalledOnResponse(
    function(response){
      if (response.status.code != 1){
        alert("Problem logging in: \n\n" + response.status.text);
      }

      else{
        // Expiry is set as late as possible.
        document.cookie = "sessionKey=" + response.session_key + "; expires=Fri, 31 Dec 9999 23:59:59 GMT; path=/";
        document.location.href = "/list_devices.html";
      };

      return;
    }
  );

  if (VERBOSE){
    console.log("Details added to ApiRequest object:");
  };

  for (detail in details){
    if (VERBOSE){
      console.log(detail + ": " + details[detail]);

    };
    req.addContent(details[detail], detail);
  }

  req.send();
}

function goToListDevicesIfSessionKeyValid(){
  var sessionKey = getCookie("sessionKey");

  if (! sessionKey){
    if (VERBOSE){
      console.log("No session key.")
    };

    return;
  };

  var req = new ApiRequest("is_session_key_valid");

  req.setCalledOnResponse(
    function(response){
      if (response.status.code != 1){
        alert("Error, code " + response.status.code.toString() + ": " + response.status.text)
        return;
      };

      if (response.is_valid == "true"){
        document.location.href = "/list_devices.html";
        return;
      }
      else {
        console.log("Session key invalid or not active.");
      };
    }
  );

  req.addContent(sessionKey, "session_key");

  req.send()
}
