$(function(){
    showNofity();
    autoSaveArticle();
    disqusModerate();
    delNote();
    $('#noteform').submit(function(){
        postNote();
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
});
