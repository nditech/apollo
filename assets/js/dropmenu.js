    $(document).ready(function(){
	jQuery("#dropmenu ul").css({display:"none"});
	// For 1 Level
	jQuery("#dropmenu li:has(ul) a").append('<span>&nbsp;</span>');
	jQuery("#dropmenu li ul a span").text('');
	// For 2 Level
	jQuery("#dropmenu li ul li:has(ul) a").append('<span>&nbsp;</span>');
	jQuery("#dropmenu li ul li ul a span").text('');
	// For 3 Level
	jQuery("#dropmenu li ul li ul li:has(ul) a").append('<span>&nbsp;</span>');
	jQuery("#dropmenu li ul li ul li ul li a span").text('');
	
	// For 4 Level
	jQuery("#dropmenu li ul li ul li ul li:has(ul) a").append('<span>&nbsp;</span>');
	jQuery("#dropmenu li ul li ul li ul li ul li a span").text('');
	
	// For 5 Level
	jQuery("#dropmenu li ul li ul li ul li ul li:has(ul) a").append('<span>&nbsp;</span>');
	jQuery("#dropmenu li ul li ul li ul li ul li ul li a span").text('');
	
	// For 6 Level
	jQuery("#dropmenu li ul li ul li ul li ul li ul li:has(ul) a").append('<span>&nbsp;</span>');
	jQuery("#dropmenu li ul li ul li ul li ul li ul li ul li a span").text('');
	
	// For 7 Level
	jQuery("#dropmenu li").hover(function(){
	jQuery(this).find("ul:first").fadeIn('fast');
	},
	function(){
	jQuery(this).find("ul:first").fadeOut('fast');
	}); });