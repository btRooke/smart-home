function addDevice(){
  var details = {
    "device_name": document.getElementById("device_name").value,
    "device_ip": document.getElementById("device_ip").value,
    "auth_key": document.getElementById("auth_key").value,
    "session_key": getCookie("sessionKey")
  };

  var req = new ApiRequest("add_device");

  req.setCalledOnResponse(
    function(response){
      if (response.status.code != 1){
        alert("Problem creatign device: \n\n" + response.status.text);
      }

      else{
        alert("Successful adding; redirecting to list devices!")
        document.location.href = "/list_devices.html";
      };
      
      var add_button = document.getElementById("add_device_button");
      add_button.innerHTML = "Add Device";

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
  
  var add_button = document.getElementById("add_device_button");
  add_button.innerHTML = "Adding...";

  req.send();
}
