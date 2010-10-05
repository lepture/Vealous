/* message */
$(function(){
    var minheight = document.documentElement.clientHeight;
    $('#mainbody').css('min-height', minheight);
    $('a[rel="external"]').attr('target','_blank');
    var message = $('.message');
    if (message.text()) {
        message.fadeIn('slow');
    }
    message.click(function(){
        message.fadeOut();
    });
    $('.nav-more>a').click(function(){
        $('.nav-more ul').slideToggle('fast');
        return false;
    });
});
