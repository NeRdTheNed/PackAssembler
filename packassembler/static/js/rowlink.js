$(document).ready(function(){
    /*$('.linked').click(function(){
        window.location = $(this).data('href');
    });*/
    $('.linked').mousedown(function(e){
        if (e.which == 1)
            window.location = $(this).data('href');
        else{
            var w = window.open($(this).data('href'), '_blank');
            w.focus();
        }
    });
    $('.nolink').mousedown(function(e){
        e.stopPropagation();
    });
});