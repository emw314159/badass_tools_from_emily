var app = angular.module('fashionistas-solar-app', []);

app.controller('fashionistas-solar-controller', function($scope) {
	
	/* 
	   Find the user's time zone

	 */
	var tz = 'GMT' + Date().toString().split('GMT')[1].split(' ')[0]

	/*
	  Initialize variables
	*/
	$scope.tz = tz
	$scope.latitude = 33.1192;
	$scope.longitude = -117.0864;


    });