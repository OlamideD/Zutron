/**
 * Created by jvfiel on 9/27/17.
 */
$(function() {
	// $('.dropdown-help').hide();  // or .remove();
	console.log("removing help...");
	console.log($('.dropdown-help'));
	$('.dropdown-help').remove();
	//dropdown dropdown-help dropdown-mobile open
	$("[data-type='help']").remove();
});