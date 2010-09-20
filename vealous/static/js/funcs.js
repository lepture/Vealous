/* message */
$(function(){
    var message = $('.soga .message');
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
        //var twitter = $('#noteform input[name="twitter"]');
        if(douban.is(':checked')){
            douban_miniblog();
        }
        $('#note').val('');
        return false;
    });
    del_note();
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
                $('.soga .message').text('Moderate comment succeeded');
                $('.soga .message').fadeIn();
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
        $('.soga .message').text('You said nothing');
        $('.soga .message').fadeIn();
        return false
    }
    $.ajax({
        type: "POST",
        data: $("#noteform").serialize(),
        url: '/god/note/add',
        cache: false,
        dataType: 'json',
        success: function(data, textStatus){
            $('.soga .message').text(data.text)
            $('.soga .message').fadeIn();
            if (data.succeeded){
                $('.notewrap').prepend(data.html);
            }
        },
        error: function(XMLHttpRequest, textStatus, errorThrown){
            $('.soga .message').text('Note Save Server Error');
            $('.soga .message').fadeIn();
        }
    });
}
function douban_miniblog() {
    $.ajax({
        type: "POST",
        data: $("#noteform").serialize(),
        url: '/god/third/douban/miniblog_saying',
        cache: false,
        dataType: 'json',
        success: function(data, textStatus){
            if(data.succeeded){
                $('.soga .message').text('Post to Douban Success');
            }else{
                $('.soga .message').text('Post to Douban Failed');
            }
            $('.soga .message').fadeIn();
        },
        error: function(XMLHttpRequest, textStatus, errorThrown){
            $('.soga .message').text('Post to Douban Server Error');
            $('.soga .message').fadeIn();
        }
    });
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
            $('.soga .message').text(data.text);
            $('.soga .message').fadeIn();
        });
        return false;
    });
}
