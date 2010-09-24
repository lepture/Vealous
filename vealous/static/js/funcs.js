/* message */
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
        if(douban.is(':checked')){
            douban_update();
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
