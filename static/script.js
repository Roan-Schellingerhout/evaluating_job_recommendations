$(document).ready(function() {
  var direction = document.getElementById("direction-store").textContent;

  if (direction != 'bedrijf') {
    $("#graph1").toggle();
    $("#graph2").toggle();
  } else {
    $("#graph1").toggle();
    $("#text1").toggle();
  }


  $('.toggle').change(function() {
    var target = $(this).data('target');
    $('#' + target).toggle();
    
    if ($(this).prop('checked')) {
      $(this).parent().addClass('disabled');
      $(this).addClass('checked');
    } else {
      $(this).parent().removeClass('disabled');
      $(this).removeClass('checked');
    }
  });
});



