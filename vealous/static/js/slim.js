/* message */
$(function(){
    var minheight = document.documentElement.clientHeight;
    $('#mainbody').css('min-height', minheight);
    $('a[rel="external"]').attr('target','_blank');
    $("a[href*='http://']:not([href*='"+location.hostname+"'])").addClass("external").attr("target","_blank");
    var message = $('.message');
    if (message.text()) {
        message.fadeIn('slow');
    }
    message.click(function(){
        message.fadeOut();
    });
    $('.nav-more>a').click(function(){
        $(this).next('ul').slideToggle('fast');
        return false;
    });
});
