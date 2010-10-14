$(function(){
    showNofity();
    tweetClick();
    autoSaveArticle();
    disqusModerate();
    delNote();
    $('#noteform').submit(function(){
        var note= $('#noteform input[name="note"]');
        var douban = $('#noteform input[name="douban"]');
        var twitter = $('#noteform input[name="twitter"]');
        if(note.is(':checked')){
            postNote();
        }
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
});
