

// Change some defaults
$.featherlight.prototype.closeOnClick = 'anywhere';

// Add a caption to each figure, based on alt attribute of img tag
$.featherlight.prototype.afterContent = function() {
  var caption = this.$currentTarget.find('img').attr('alt');
  this.$instance.find('.caption').remove();
  $('<div class="caption">').text(caption).appendTo(this.$instance.find('.featherlight-content'));
};

// For figures:
$(function() {
    $('figure.zoomable').each(function(index, value){
        var figcaption = $(this).find('figcaption');
        var img = $(this).find('img');
        if(figcaption.length) {
            img.attr('alt', figcaption.text());
        }
        $(this).first('a').attr('data-featherlight', img.attr('src'));
    });
});
