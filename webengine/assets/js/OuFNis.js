$(document).ready(function() {
    var socket = io.connect('http://' + document.domain + ':' + location.port);
    var target_btn = document.getElementById('target_btn');
    
    target_btn.onclick = function(){
        socket.emit('target');   
        //location.reload();
    }
})
