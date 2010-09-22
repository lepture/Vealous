/* message */
$(function(){
    $('a[rel="external"]').attr('target','_blank');
    var message = $('.message');
    if (message.text()) {
        message.fadeIn('slow');
    }
    message.click(function(){
        message.fadeOut();
    });
});
