// basic
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

function disqusModerate() {
    $('.disqus .action a').click(function(){
        var action = $(this).text().toLowerCase();
        var label = $(this).parent().siblings('.bitch').find('.status');
        var comment_id = $(this).attr('class');
        var url = $(this).atrr('href');
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
