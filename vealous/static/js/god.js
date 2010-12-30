// basic
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
function showNofity() {
    var message = $('.message');
    if (message.text()) {
        message.fadeIn();
    }
    message.click(function(){
        message.fadeOut();
    });
}
function melodyLable(arg) {
    $('.melodyspace').html('');
    var choice = '.choices .' + arg;
    $('.melodyspace').html($(choice).html());
}
function tweetClick() {
    $('a.reply').click(function(){
        var who = $(this).attr('href').replace('#','@') + ' ';
        $('#noteform #note').val(who);
        $('#noteform #note').focus();
        return false;
    });
    $('a.rt').click(function(){
        var who = $(this).attr('href').replace('#','@') + ' ';
        var text = $(this).parentsUntil('.widow').siblings('.tw-content').text();
        var text = 'RT ' + who + text;
        $('#noteform #note').val(text);
        $('#noteform #note').focus();
        return false;
    });
    $('a.fav').live('click', function(){
        var status_id = $(this).attr('href').replace('#','');
        addTwitterFav(status_id);
        $(this).text('UnFav');
        $(this).removeClass('fav');
        $(this).addClass('unfav');
        return false;
    });
    $('a.unfav').live('click', function(){
        var status_id = $(this).attr('href').replace('#','');
        delTwitterFav(status_id);
        $(this).text('Fav');
        $(this).removeClass('unfav');
        $(this).addClass('fav');
        return false;
    });
}
// ajax
function postNote() {
    var notelen = $('#note').val().length;
    if (notelen < 1) {
        $('.message').text('You said nothing');
        $('.message').fadeIn();
        return false
    }
}
function postDoubanMiniblog(){
    $.post('/god/douban/miniblog', $('#noteform').serialize(),
    function(data){
        $('.message').html(data.text);
        $('.message').fadeIn();
    },'json');
}
function postTwitterStatus() {
    $.post('/god/twitter/status', $('#noteform').serialize(),
    function(data){
        $('.message').html(data.text);
        $('.message').fadeIn();
    },'json');
}
function addTwitterFav(status_id) {
    $.getJSON('/god/twitter/addfav/' + status_id,
    function(data){
        $('.message').html(data.text);
        $('.message').fadeIn();
    });
}
function delTwitterFav(status_id) {
    $.getJSON('/god/twitter/delfav/' + status_id,
    function(data){
        $('.message').html(data.text);
        $('.message').fadeIn();
    });
}

function disqusModerate() {
    $('.disqus .action a').click(function(){
        var action = $(this).text().toLowerCase();
        var label = $(this).parent().siblings('.bitch').find('.status');
        var comment_id = $(this).attr('class');
        var url = $(this).attr('href');
        $.getJSON(url, function(data){
            if(data.succeeded){
                $('.message').text('Moderate comment succeeded');
                $('.message').fadeIn();
            }
        });
        if ('approve' == action){
            $(this).text('Spam');
            label.text('approved');
        }else if ('spam' == action){
            $(this).text('Approve')
            label.text('spam');
        }else if ('delete' == action){
            $(this).parent().parent().fadeOut('slow');
        }else{
            return false
        }
        return false
    });
}
// auto save article
var DEMO;
function autoSave() {
    var title = $('#id_title').val();
    var slug = $('#id_slug').val();
    var text = $('#id_text').val();
    var keyword = $('#id_keyword').val();
    localStorage.title = title;
    localStorage.slug = slug;
    localStorage.text = text;
    localStorage.keyword = keyword;
    $('.message').text('auto saved');
    $('.message').fadeIn('slow');
    $('.message').fadeOut(1500);

    DEMO = setTimeout(autoSave, 120000);
}
function stopSave(){
    clearTimeout(DEMO);
}
function autoSaveArticle(){
    if('box' == $('#articleform').attr('class')){
        $('#id_title').val(localStorage.title);
        $('#id_slug').val(localStorage.slug);
        $('#id_text').val(localStorage.text);
        $('#id_keyword').val(localStorage.keyword);
    }
    $('#articleform').submit(function(){
        localStorage.clear();
    });
    if($('.autosave').is(':checked')){
        autoSave();
    }
    $('.autosave').change(function(){
        if($('.autosave').is(':checked')){
            autoSave()
        }else{ stopSave();}
    });
}
$(function(){
    showNofity();
    tweetClick();
    autoSaveArticle();
    disqusModerate();
    $('#noteform').submit(function(){
        var note= $('#noteform input[name="note"]');
        var douban = $('#noteform input[name="douban"]');
        var twitter = $('#noteform input[name="twitter"]');
        if(douban.is(':checked')){
            postDoubanMiniblog();
        }
        if(twitter.is(':checked')){
            postTwitterStatus();
        }
        $('#note').val('');
        return false;
    });

    var arg = $('#id_label').val();
    melodyLable(arg);
    $('#id_label').change(function(){
        var arg = $(this).val();
        melodyLable(arg);
    });
    $('.nav-more>a').click(function(){
        $(this).next('ul').slideToggle('fast');
        return false;
    });
    $('#preview').live('click', function(){
        var converter = new Showdown.converter();
        $(this).attr('id', 'write');
        $(this).val('Write');
        var txt = $('#id_text').val();
        var html = converter.makeHtml(txt);
        $("#text-preview").html(html);
        $('#id_text').hide();
        $('#text-preview').show();
    });
    $('#write').live('click', function(){
        $(this).attr('id', 'preview');
        $(this).val('Preview');
        $('#text-preview').hide();
        $('#id_text').show();
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
