$(document).ready(function(){
    //connect to the socket server.
    console.log("What the fuck")
    var socket = io.connect('http://' + document.domain + ':' + location.port);
    var numbers_received = [];
    alert("connected");

    //receive details from server
    socket.on('newnode', function(msg) {
        console.log("Received number" + msg.number);
        //maintain a list of ten numbers
        if (numbers_received.length >= 10){
            numbers_received.shift()
        }            
        numbers_received.push(msg.number);
        numbers_string = '';
        for (var i = 0; i < numbers_received.length; i++){
            numbers_string = numbers_string + '<p>' + numbers_received[i].toString() + '</p>';
        }
        $('#new').html(numbers_string);
    });

});