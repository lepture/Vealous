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
    douban_miniblog();
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
function douban_miniblog() {
    $('#notebook').submit(function(){
        $.ajax({
            type: "POST",
            data: $("#notebook").serialize(),
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
                $('.soga .message').text('Server Error');
                $('.soga .message').fadeIn();
            }
        });
        return false;
    });
}
