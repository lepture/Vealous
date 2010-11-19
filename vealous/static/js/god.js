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
});
