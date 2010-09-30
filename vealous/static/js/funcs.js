/* message */
var DEMO;
$(function(){
    var message = $('.message');
    if (message.text()) {
        message.fadeIn();
    }
    message.click(function(){
        message.fadeOut();
    });
    var arg = $('#id_label').val();
    swLabel(arg);
    $('#id_label').change(function(){
        var arg = $(this).val();
        swLabel(arg);
    });
    disqus_moderate();
    $('#noteform').submit(function(){
        post_note();
        var douban = $('#noteform input[name="douban"]');
        var twitter = $('#noteform input[name="twitter"]');
        if(douban.is(':checked')){
            douban_update();
        }
        if(twitter.is(':checked')){
            postTwitterStatus();
        }
        $('#note').val('');
        return false;
    });
    del_note();
    if($('#articleform').attr('class')){
        $('#id_title').val(localStorage.title);
        $('#id_slug').val(localStorage.slug);
        $('#id_text').val(localStorage.text);
        $('#id_keyword').val(localStorage.keyword);
        $('#articleform').submit(function(){
            localStorage.clear();
        });
        if($('.autosave').is(':checked')){
            auto_save();
        }
        $('.autosave').change(function(){
            if($('.autosave').is(':checked')){
                auto_save()
            }else{ stop_save();}
        });
    }
});
function swLabel(arg) {
    $('.melodyspace').html('');
    var choice = '.choices .' + arg;
    $('.melodyspace').html($(choice).html());
}
function disqus_moderate() {
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
function post_note() {
    var notelen = $('#note').val().length;
    if (notelen < 1) {
        $('.message').text('You said nothing');
        $('.message').fadeIn();
        return false
    }
    $.post('/god/note/add', $('#noteform').serialize(), function(data){
        $('.message').text(data.text)
        $('.message').fadeIn();
        if (data.succeeded){
            $('.notewrap').prepend(data.html);
        }
    }, 'json');
}
function douban_update() {
    $.post('/god/third/douban/update.json', $('#noteform').serialize(),
    function(data){
        $('.message').html(data.text);
        $('.message').fadeIn();
    },'json');
}
function update_twitter() {
    $.ajax({
        type: "POST",
        data: $("#noteform").serialize(),
        url: '/god/third/twitter/update_status',
        cache: false,
        dataType: 'json',
        success: function(data, textStatus){
            if(data.succeeded){
                $('.soga .message').text('Post to Twitter Success');
            }else{
                $('.soga .message').text('Post to Twitter Failed');
            }
            $('.soga .message').fadeIn();
        },
        error: function(XMLHttpRequest, textStatus, errorThrown){
            $('.soga .message').text('Post to Twitter Server Error');
            $('.soga .message').fadeIn();
        }
    });
}

function del_note(){
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

function auto_save() {
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

    DEMO = setTimeout(auto_save, 120000);
}
function stop_save(){
    clearTimeout(DEMO);
}
