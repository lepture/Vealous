/* message */
$(function(){
    var message = $('.message');
    if (message.text()) {
        message.fadeIn('slow');
    }
    message.click(function(){
        message.fadeOut();
    });
});
