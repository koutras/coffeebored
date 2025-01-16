
	// Note: This example requires that you consent to location sharing when
	// prompted by your browser. If you see a blank space instead of the map, this
	// is probably because you have denied permission for location sharing.

	var map;

	function initialize() {
	  var mapOptions = {
		 zoom: 6
	  };
	  map = new google.maps.Map(document.getElementById('map-canvas'),
			mapOptions);

	  // Try HTML5 geolocation
	  if(navigator.geolocation) {
		 navigator.geolocation.getCurrentPosition(function(position) {
			var pos = new google.maps.LatLng(position.coords.latitude,
														position.coords.longitude);

			
	//		var infowindow = new google.maps.InfoWindow({
	//		  map: map,
	//		  position: pos,
	//		  content: 'Location found using HTML5.'
	//		});
			//include snippet from stack overflow to post into server
			//my code to send two parameters
			var postData = new Array();
			postData['latitude']=position.coords.latitude;
			postData['longitude']=position.coords.longitude;

			post('/myLocation', postData, 'post');

			
			map.setCenter(pos);
		 }, function() {
			handleNoGeolocation(true);
		 });
	  } else {
		 // Browser doesn't support Geolocation
         alert('no geolocation');
		 handleNoGeolocation(false);
	  }
	}

	function handleNoGeolocation(errorFlag) {
	  if (errorFlag) {
		 var content = 'Error: The Geolocation service failed.';
	  } else {
		 var content = 'Error: Your browser doesn\'t support geolocation.';
	  }

	  var options = {
		 map: map,
		 position: new google.maps.LatLng(60, 105),
		 content: content
	  };

	  var infowindow = new google.maps.InfoWindow(options);
	  map.setCenter(options.position);
	}

	//google.maps.event.addDomListener(window, 'load', initialize);

	//Snippet from stack overflow to handle post 
	function post(path, params, method) {
    method = method || "post"; // Set method to post by default if not specified.

    // The rest of this code assumes you are not using a library.
    // It can be made less wordy if you use one.
    var form = document.createElement("form");
    form.setAttribute("method", method);
    form.setAttribute("action", path);

    for(var key in params) {
        if(params.hasOwnProperty(key)) {
            var hiddenField = document.createElement("input");
            hiddenField.setAttribute("type", "hidden");
            hiddenField.setAttribute("name", key);
            hiddenField.setAttribute("value", params[key]);

            form.appendChild(hiddenField);
         }
    }

    document.body.appendChild(form);
    form.submit();
	}


function SetupAndSendRequest(time) {
	var request = new XMLHttpRequest();
	var transcript = document.getElementById("chat_messages");

	request.onreadystatechange = function() {
		//Wait until the request is done. Done == ready state 4.
		if (request.readyState !=4){
			return;
		}
		var xmlData = request.responseXML.documentElement;
		if (xmlData !=null){
			transcript.innerHTML = "";
			messages = xmlData.getElementsByTagName("p");
			for (var x=0; x<messages.length; x++){
				transcript.innerHTML += "<p>" +
					messages[x].childNodes[0].nodeValue + "</p>";
			}
			newtime = xmlData.getAttribute("time");

//			setTimeout(SetupAndSendRequest(newtime),3000);
			
		} else {
			transcript.innerHTML += "<p> Σφάλμα ανανέωσης του chat </p>";
		}
	}
	setTimeout(request.open("GET", "latest?time=" + time, true),3000);
	setTimeout(request.send(),3000);
}

//function init() {
//	SetupAndSendRequest(0);
//}

//window.onload = init;

function LoadOnlineFriends() {
	var request = new XMLHttpRequest();
    //get the resource /onlineFriends
	var transcript = document.getElementById("onlineFriends");
    //var transcript= friendForm.getElementById("onlineFriends");
	request.onreadystatechange = function() {
		//Wait until the request is done. Done == ready state 4.
		if (request.readyState !=4){
			return;
		}
        if (request.responseXML!=null){
            try{
            var xmlData = request.responseXML.documentElement;
            }
            catch(err){
                return;
            }
        }else return;
        if (xmlData==null)return; //return in case xml data is not ready a.k
		if (xmlData !=null){
            if (transcript==null)
                return;
			transcript.innerHTML = "";
            //online friends 
            transcript.innerHTML+='<optgroup label="Συνδεδεμένοι Φίλοι">';
			persons = xmlData.getElementsByTagName("friend");
			for (var x=0; x<persons.length; x++){
                var k=x+1;
                var name =persons[x].getElementsByTagName("name")[0].innerHTML;
                var id =persons[x].getElementsByTagName("id")[0].innerHTML;
				transcript.innerHTML +='<option value="'+id+'">'+
					name + '</option>';
			}
            transcript.innerHTML+='</optgroup>';
            transcript.innerHTML+='<optgroup label="Συνδεδεμένοι φίλοι φίλων">';
			persons = xmlData.getElementsByTagName("fof");
            //friends of friends
           	for (var x=0; x<persons.length; x++){
                var k=x+1;
                var name =persons[x].getElementsByTagName("name")[0].innerHTML;
                var id =persons[x].getElementsByTagName("id")[0].innerHTML;
				transcript.innerHTML +='<option value="' +id+ '">'+ 
					name + '</option>';
			}
            transcript.innerHTML+='</optgroup>';

		} else {
			transcript.innerHTML += "<p> Σφάλμα ανανέωσης</p>";
		}
	}
	request.open("GET", "onlineFriends", true);
	request.send();
}


function LoadNearbyCafeterias() {
	var request = new XMLHttpRequest();
	var transcript = document.getElementById("nearbyCafeterias");
    //var transcript= friendForm.getElementById("onlineFriends");
	request.onreadystatechange = function() {
		//Wait until the request is done. Done == ready state 4.
		if (request.readyState !=4){
			return;
		}
        if (request.responseXML!=null){
            try{
            var xmlData = request.responseXML.documentElement;
            }
            catch(err){
                return;
            }
         if (xmlData==null)return; //return in case xml data is not ready a.k
		if (xmlData !=null){
            if (transcript==null)
                return;
			transcript.innerHTML = "";
			messages = xmlData.getElementsByTagName("p");
			for (var x=0; x<messages.length; x++){
                var k=x+1;
				transcript.innerHTML +='<option value=' +k+'>'+
					messages[x].childNodes[0].nodeValue + '</option>';
			}
		} else {
			transcript.innerHTML += "<p> Σφάλμα ανανέωσης</p>";
		}
        }
	}
	request.open("GET", "nearbyCafeterias", true);
	request.send();
}

function friendsAndCafeterias(){
    LoadNearbyCafeterias();
    LoadOnlineFriends();
//    initialize();//initialize also google location
}

function httpGet(theUrl)
{
    var xmlHttp = null;

    xmlHttp = new XMLHttpRequest();
    xmlHttp.open( "GET", theUrl, false );
    xmlHttp.send( null );
    return xmlHttp.responseText;
}
window.onload = friendsAndCafeterias;
/*
window.onbeforeunload = function(){ httpGet('logout');} 

window.addEventListener("beforeunload", function(e){
    httpGet('logout');
}, false);
*/



