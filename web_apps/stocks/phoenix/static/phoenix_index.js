var app = angular.module('phoenix_app', []);

app.controller('phoenix_controller', ['$scope', '$http', function($scope, $http) {

    /*
      Initialize variables
    */
    $scope.data = [];
    $scope.have_data = false;
    var url = 'report'

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
