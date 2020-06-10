function create_user(){
  var details = {
    "new_username": document.getElementById("username").value,
    "new_password": document.getElementById("password").value 
  };
  
  
  var emailValue = document.getElementById("email").value;
  
  if (emailValue != ""){
	  details["email"] = emailValue;
  }

  var req = new ApiRequest("create_user");

  req.setCalledOnResponse(
    function(response){
      if (response.status.code != 1){
        alert("Problem logging in: \n\n" + response.status.text);
      }

      else{
        alert("Successful user creation, redirecting to login page")
        document.location.href = "/login.html";
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
