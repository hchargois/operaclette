operacletteControllers = angular.module('operacletteControllers', []);

operacletteControllers.controller('SpectacleListCtrl', function($scope, $http) {
	// Get data
	$http.get('json/spectacles.json').success(function(data) {
		$scope.spectacles = data['spectacles'];
	});
	// Initialize model
	$scope.ckballet = true;
	$scope.ckopera = true;
	$scope.ckgarnier = true;
	$scope.ckbastille = true;
	$scope.ckfuture = true;
	$scope.filterpricelow = 10;
	$scope.filterpricehigh = 200;
	// Handlers
	$scope.filterMatch = function(s) {
		// I don't want to evaluate and return a huge one-liner boolean expression,
		// so let's break it up in chunks, shall we?
		if (s['type'] == "ballet" && !$scope.ckballet
			|| s['type'] == "opera" && !$scope.ckopera) {
				return false;
			}
		if (s['location'] == "Palais Garnier" && !$scope.ckgarnier
			|| s['location'] == "Opéra Bastille" && !$scope.ckbastille) {
				return false;
			}
		if (!$scope.ckpast || !$scope.ckfuture) {
			var past = new Date(s["last_representation"]) < Date.now();
			if (!$scope.ckpast && past) {
				return false;
			}
			if (!$scope.ckfuture && !past) {
				return false;
			}
		}
		if ($scope.ckdispo) {
			var okprices = s["prices_available"].filter(function(e){return e >= $scope.filterpricelow && e <= $scope.filterpricehigh});
			if (okprices.length == 0) {
				return false;
			}
		}
		return true;
	};
	$scope.getDetails = function(s) {
		$http.get('json/details/' + s.name_id + '.json').success(function(data) {
			s.details = data['details'];
		});
	};
	$scope.getPriceDetail = function(r, price) {
		var matchingcat = r["seats"].filter(function(e){return e["price"] == price});
		if (matchingcat.length == 0) {
			return null;
		} else {
			return matchingcat[0];
		}
	};
}).directive('pricedetail', function () {
	return {
		restrict: 'E',
		scope: {
			prdet: '=',
			url: '='
		},
		templateUrl: 'static/partials/pricedetail.html'
	};
});
