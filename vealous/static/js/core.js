function postTwitterStatus() {
    $.post('/god/twitter/status', $('#noteform').serialize(),
    function(data){
        $('.message').html(data.text);
        $('.message').fadeIn();
    },'json');
}
