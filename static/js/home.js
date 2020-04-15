console.log('js called')

var socket = io.connect('http://' + document.domain + ':' + location.port);
console.log('socket connecteed') 
// alert('Connected') 
function CreateNodes() {
  console.log('Creating game...');
  // alert('Creating game')
  // var number_nodes = document.getElementById("nodes").value;
  var form = document.forms["no_nodes"];
  console.log('Creating game...');
  var number_nodes = form.elements["nodes"].value
  console.log('Creating game...');
  // alert('emiting create')
  socket.emit('create', {nodes: number_nodes, dictionary: 'Simple'});
  // alert('Eitted')
  console.log('Creating game...');
}

function checkStatus(){
    console.log('Checking Status...');
    socket.emit('check_clients', {});

}
var numbers_received = [];
$(document).ready(function(){
    //connect to the socket server.
    var socket = io.connect('http://' + document.domain + ':' + location.port);
    var numbers_received = [];

    socket.on('connect', function(msg) {
        console.log("Connected")
    });

    //receive details from server
    socket.on('clients', function(msg) {
        console.log("Received number" + msg.number);

        //maintain a list of ten numbers
        if (numbers_received.length >= 1){
            numbers_received.shift()
        }            
        // numbers_received.push(msg.number);
        // numbers_string = 'Connected Clients: ';
        // for (var i = 0; i < numbers_received.length; i++){
        //     numbers_string = numbers_string + '<p>' + numbers_received[i].toString() + '</p>';
        // }
        $('#nodes').html(msg.number);
    });

    socket.on('Reply', function(msg) {
        console.log("Reply received" + msg.reply);

        reply_string = 'Reply: ' + '<p>' + msg.reply.toString() + '</p>';
        $('#reply').html(reply_string);
    });

});
