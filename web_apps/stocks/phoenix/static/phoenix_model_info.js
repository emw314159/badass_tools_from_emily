var app = angular.module('phoenix_model_info_app', []);


app.config(['$httpProvider', function($httpProvider) {
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.headers.common["X-CSRFToken"] = window.csrf_token;
}]);

app.controller('phoenix_model_info_controller', ['$scope', '$http', function($scope, $http) {
        
    /*
      Initialize variables
    */
    $scope.data = [];
    $scope.have_data = false;
    var url = 'http://35.160.51.97:8080/phoenix/modelreport'

    /*
      call for data
     */
    $http({
        method : 'POST',
        data : {},
        url : url,
    }).then(function successCallback(response) {
	$scope.data = response['data']['data'];
	$scope.have_data = true;
    }, function errorCallback(response) {
    });
}]);
