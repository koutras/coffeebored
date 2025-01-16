function jar_horizontal(){  
	
	$(function() {
			$("#jar").animate({left:"+=530px"},{duration:24000, queue:false});
			$("#ripple").animate({left:"+=530px"},{queue:false,duration:24000});
	});
}  
function ripple(){
   $("#ripple").animate({opacity:".1"},1000).animate({opacity:"1"},1000);  
	setTimeout("ripple()",2000);
}
function cloud1(){  
    $("#cloud1").animate({left:"+=850px"},10000).animate({left:"-150px"}, 0)  
    setTimeout("cloud1()",10000);  
}  
function cloud2(){  
    $("#cloud2").animate({left:"+=950px"},9000).animate({left:"-250px"}, 0)  
    setTimeout("cloud2()",9000);  
}  
function cloud3(){  
    $("#cloud3").animate({left:"+=800px"},6000).animate({left:"-100px"}, 0)  
    setTimeout("cloud3()",6000);  
}  
function jar_vertical(){

	$("#jar").animate({top:"105px"},1000).animate({top:"110px"},1000); 
	setTimeout("jar_vertical()",2000);
}

function welcome(){
	$("#welcome").animate({top:"10px"},{queue:false,duration:600, easing:'easeOutBounce'});
}

function animation(){  
	 jar_vertical(); 
    jar_horizontal();  
	 ripple();
    cloud1();  
    cloud2();  
    cloud3();  
}  

function onReady(){
	var horizPixels=0;
	var stringPixels;
	setTimeout("animation()",300);
	setTimeout("welcome()",6500);

}

$(document).ready(onReady);
