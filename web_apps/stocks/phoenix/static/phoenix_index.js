var app = angular.module('phoenix_app', []);

app.controller('phoenix_controller', ['$scope', '$http', function($scope, $http) {

    /*
      Initialize variables
    */
    $scope.data = [];
    var url = 'http://ec2-35-160-25-103.us-west-2.compute.amazonaws.com:8080/phoenix/report'

    /*
      call for data
     */
    $http({
        method : 'POST',
        data : {},
        url : url,
    }).then(function successCallback(response) {
	$scope.data = response['data']['data'];
    }, function errorCallback(response) {
    });
}]);
