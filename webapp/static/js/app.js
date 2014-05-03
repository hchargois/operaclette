var operacletteApp = angular.module('operacletteApp', [
		'ngRoute',
		'ui.bootstrap',
		'operacletteControllers'
		]);

operacletteApp.config(['$routeProvider',
		function($routeProvider) {
			$routeProvider.when('/list', {
				templateUrl: 'static/partials/list.html',
				controller: 'SpectacleListCtrl'
			}).otherwise({
				redirectTo: '/list'
			});
		}]);
