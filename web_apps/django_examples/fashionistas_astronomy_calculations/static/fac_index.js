var app = angular.module('fashionistas_solar_app', []);

app.controller('fashionistas_solar_controller', ['$scope', '$http', function($scope, $http) {
	
	/* 
	   Find the user's time zone
	 */
	var timezone = 'GMT' + Date().toString().split('GMT')[1].split(' ')[0]

	/*
	  Initialize variables
	*/
	$scope.timezone = timezone
	$scope.latitude = 33.1192;
	$scope.longitude = -117.0864;
	$scope.have_result = false;
	var url = 'http://localhost:8000/a-fashionistas-astronomy-calculations/logic';

	/*
	  Process data
	*/
	$scope.buttonClicked = function() {
	    $scope.have_result = false;
	    if ($scope.fashionistas_form.$valid) {
		var data_to_send = {}
		data_to_send['timezone'] = $scope.timezone;
		data_to_send['latitude'] = $scope.latitude;
		data_to_send['longitude'] = $scope.longitude;
		$http({
			method : 'POST',
			    data : data_to_send,
			    url : url,
			    }).then(function successCallback(response) {
				    console.log(response);
				    $scope.utc_noon = response['data']['utc_noon'];
				    $scope.local_noon = response['data']['local_noon'];
				    $scope.have_result = true;
				}, function errorCallback(response) {
				});
	    }

	};

    }]);