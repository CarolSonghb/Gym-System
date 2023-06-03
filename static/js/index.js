
debugger;
anotherEventListener("keypress", function(event) {
    console.log(event);
});

const currenYear = new Date().getFullYear();
// return the current year
document.getElementById("year").innerHTML = currenYear;


// Path: static/js/index.js
$(document).ready(function(){
    $('#myTable').dataTable();
});


