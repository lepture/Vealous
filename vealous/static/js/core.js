function postDoubanMiniblog(){
    $.post('/god/douban/miniblog', $('#noteform').serialize(),
    function(data){
        $('.message').html(data);
        $('.message').fadeIn();
    },'text');
}
function postTwitterStatus() {
    $.post('/god/twitter/status', $('#noteform').serialize(),
    function(data){
        $('.message').html(data.text);
        $('.message').fadeIn();
    },'json');
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

    DEMO = setTimeout(auto_save, 120000);
}
function stopSave(){
    clearTimeout(DEMO);
}
