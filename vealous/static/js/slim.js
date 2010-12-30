function getScroll() {
    var t, l, w, h;
    if (document.documentElement && document.documentElement.scrollTop){
        t = document.documentElement.scrollTop;
        l = document.documentElement.scrollLeft;
        w = document.documentElement.scrollWidth;
        h = document.documentElement.scrollHeight;
    } else if (document.body){
        t = document.body.scrollTop;
        l = document.body.scrollLeft;
        w = document.body.scrollWidth;
        h = document.body.scrollHeight;
    }
    return {top: t, left: l, width: w, height: h};
}
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
    $("#gotop").click(function(){
        $("html, body").animate({'scrollTop': 0}, 400);
        return false;
    });
    $(window).scroll(function() {
        var s = getScroll();
        var g = $("#gotop");
        if (s.top > 300 && g.is(":hidden")) {
            g.fadeIn();
        } else if(s.top < 300 && g.is(":visible")) {
            g.fadeOut();
        }
    });
});
