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
// ajax
function postNote() {
    var notelen = $('#note').val().length;
    if (notelen < 1) {
        $('.message').text('You said nothing');
        $('.message').fadeIn();
        return false
    }
    $.post('/god/note/add', $('#noteform').serialize(), function(data){
        $('.message').text(data.text)
        $('.message').fadeIn();
        $('.message').fadeOut(2000);
        if (data.succeeded){
            $('.notewrap').prepend(data.html);
        }
    }, 'json');
}
function delNote(){
    $('.notewrap .action a').click(function(){
        $(this).parentsUntil('.box').fadeOut();
        var url = $(this).attr('href');
        $.getJSON(url, function(data){
            $('.message').text(data.text);
            $('.message').fadeIn();
        });
        return false;
    });
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
        var url = '/god/third/disqus_moderate?action=' + action + '&post_id=' + comment_id;
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
    localStorage.slug = title;
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
