var fileTemplateSource   = $("#file-template").html();
var folderTemplateSource = $("#folder-template").html();
var PhotographerOptionTemplateSource = $("#photographer-option-template").html();
var fileTemplate = Handlebars.compile(fileTemplateSource);
var folderTemplate = Handlebars.compile(folderTemplateSource);
var PhotographerOptionTemplate = Handlebars.compile(PhotographerOptionTemplateSource);

var getParameterByName = function(name) {
    name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]");
    var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
        results = regex.exec(location.search);
    return results === null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
}

var reloadDirectory = function(offset){
  $('.rows .row').remove();
  var $rows = $('.rows');
  var opts = {scale: 5.25 }
  var spinner = new Spinner(opts).spin();
  $rows.append(spinner.el);
  var path = getParameterByName('path');
  var photographer_id = getPhotographer();
  var query_array = []
  if (path) {
    path = 'path='+path;
    query_array.push(path);
  }
  if (photographer_id) {
    photographer_id = 'photographer_id='+photographer_id;
    query_array.push(photographer_id);
  }
  var query = '?' + query_array.join('&');
  $.getJSON('/api/' + query,
    function(data){
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
      if (offset) {
        $(document).scrollTop(offset);
      }
    }).fail(function(jqXHR) {
      if (jqXHR.status == 403) {
          alert("Permission denied for " + window.location.search);
      } else {
          alert("An error occured.");
      }
  });
}

var deleteFile = function(path){
  var currentOffset = $(document).scrollTop();
  var r = confirm("Are you sure?");
  if(r==true){
    $.ajax({
      url: '/api/?path=' + path,
      type: 'DELETE',
      success: function(result) {
          reloadDirectory(currentOffset);
      }
    });
  }
}

var populatePhotographers = function(){
  $.getJSON('/api/photographer/', function(data){ 
    var photographers = data['results'];
    for (var i=0; i<photographers.length; i++){
      var photographer = photographers[i];
      var context = {
        "value": photographer.id,
        "name": photographer.name};
      if (getPhotographer() === photographer.id) {
        context.selected = true;
      }
      $('#photographers').append(PhotographerOptionTemplate(context));
    }
  }); 
}

var setPhotographer = function(id) {
  $('#photographer-id').val(id);
  return Cookies.set('photographer', id);
}

var getPhotographer = function() {
  return parseInt(Cookies.get('photographer'));
}

$('#photographers').on('change', function() {
  setPhotographer($(this).val());
  reloadDirectory();
});


reloadDirectory();
populatePhotographers();
