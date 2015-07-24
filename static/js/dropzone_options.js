Dropzone.options.upload = {
  method: "put",
  paramName: "image",
  maxFilesize: 30, // MB
  accept: function(file, done) {
    var ext = file.name.split('.').pop();
    if (ext == "NEF" || ext == "SRW") {
      done();
    }
    else {  
      done("Please upload only supported raw images. (NEF, SRW)");
    }
  }
};

