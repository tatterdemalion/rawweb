var fileTemplateSource   = $("#file-template").html();
var folderTemplateSource = $("#folder-template").html();
var fileTemplate = Handlebars.compile(fileTemplateSource);
var folderTemplate = Handlebars.compile(folderTemplateSource);

var reloadDirectory = function(){
  var $rows = $('.rows');
  var opts = {scale: 5.25 }
  var spinner = new Spinner(opts).spin();
  $rows.append(spinner.el);
  $.getJSON('/api/' + window.location.search, function(data){
    var paths = data['results']['paths'];
    var i,j,temparray,chunk = 3;
    for (i=0, j=paths.length; i<j; i+=chunk) {
      temppaths = paths.slice(i,i+chunk);
      var div = '<div class="row">';
      for (var k=0; k<temppaths.length; k++) {
        var path = temppaths[k];
        if(path.pathtype == 'directory') {
          div += folderTemplate(path);
        }
        else if (path.pathtype == 'file') {
          div += fileTemplate(path);
        }  
      }
      div += '</div>';
      $rows.append(div);
    }
    $('.spinner').remove();
  }).fail(function(jqXHR) {
    if (jqXHR.status == 403) {
        alert("Permission denied for " + window.location.search);
    } else {
        alert("An error occured.");
    }
  });
}

reloadDirectory();
