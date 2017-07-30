var app = angular.module('volume_movers_app', []);

app.controller('volume_movers_controller', ['$scope', '$http', function($scope, $http) {
        
    /*
      Initialize variables
    */
    $scope.data = [];
    var url = 'http://ec2-34-213-112-250.us-west-2.compute.amazonaws.com/volume-movers/report'

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
