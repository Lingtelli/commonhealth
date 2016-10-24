(function() {
   var app = angular.module('query-system', ['ui.bootstrap']);

   app.controller('SystemController', ['$scope', 'Data', function($scope, Data) {

      $scope.query = function(_disease) {
         Data.setInputDisease(_disease);
      };
   }]);

   /***************************************************************
    *    In charge of type selection and generate the query result
    * *************************************************************/
   app.controller("TypeController", function($scope, Data) {

      this.selectType = function(_type) {
         if (! this.isSelected(_type)) {
            var idx = $scope.deselected_types.indexOf(_type);
            $scope.deselected_types.splice(idx, 1);
         }else {
            $scope.deselected_types.push(_type);
            $(this).removeAttr('checked');
         }
         console.log($scope.deselected_types);
      };

      this.isSelected = function(_type) {
         return ($scope.deselected_types.indexOf(_type) == -1 )
      };

      function initialTypes(_disease_clusters) {
         var temp_types = [];
         var dates = [];
         for (var idx = 0; idx < _disease_clusters.length; idx++) {
            var cluster = _disease_clusters[idx];

            for (var jdx in cluster['member'])
               temp_types = temp_types.concat(cluster['member'][jdx]['types']);

            for (var jdx in cluster['member'])
               dates.push(cluster['member'][jdx]['date'])
         }

         $scope.types = Array.from(new Set(temp_types));
         $scope.deselected_types = [];

         var earliest_date = dates.reduce(function (pre, cur) {
            return Date.parse(pre) > Date.parse(cur) ? cur : pre;
         });
         var latest_date = dates.reduce(function (pre, cur) {
            return Date.parse(pre) < Date.parse(cur) ? cur : pre;
         });

         //set time range
         $('#daterange').daterangepicker({
            startDate: earliest_date,
            endDate: latest_date,
            minDate: earliest_date,
            maxDate: latest_date,
            locale: {
               applyLabel: '選取',
               cancelLabel: '取消',
               toLabel: '至',
               format: 'YYYY-MM-DD',
               daysOfWeek: ["日", "一", "二", "三", "四", "五", "六"],
               monthNames: ["一月","二月","三月","四月","五月","六月","七月","八月","九月","十月","十一月","十二月"],
            }
         });
         $scope.start_date = Date.parse(earliest_date);
         $scope.end_date = Date.parse(latest_date);
      };
      
      $scope.generateSnippet = function(content) {
         return content.slice(0, 5);
      };

      $scope.generateQueryResults = function() {
         var temp_results = [];
         angular.copy($scope.disease_info, temp_results);

         // get the time range, the block of code can be places somewhere.
         $('#daterange').on('apply.daterangepicker', function(ev, picker) {
            $scope.start_date = Date.parse(picker.startDate.format('YYYY-MM-DD'));
            $scope.end_date = Date.parse(picker.endDate.format('YYYY-MM-DD'));
         });
         
         for (var idx  = 0; idx < temp_results.length; ++idx) {
            var cluster = temp_results[idx];

            for (var jdx in cluster['member']) {

               // If types of a paragraph are subarray of deselected_types,
               // delte the paragraph from results.
               if ( isSubArray(cluster['member'][jdx]['types'],$scope.deselected_types) ) {
                  delete(temp_results[idx]['member'][jdx]);
                  continue;
               }
               
               // check if the date of the paragraph is between max & min date selected.
               //console.log(cluster['member'][jdx]);
               var article_created_date = Date.parse(cluster['member'][jdx]['date']);
               if (article_created_date < $scope.start_date || article_created_date > $scope.end_date) {
                  try {
                     delete(temp_results[idx]['member'][jdx]);
                  }catch(err) {
                     console.log('the paragraph is deleted.');
                  }
               }
            }

            // delte cluster with no member.
            temp_results[idx]['member'] = temp_results[idx]['member'].filter(Boolean);
            if ( temp_results[idx]['member'].length == 0 ) {
               console.log('cluster has no member');
               temp_results.splice(idx, 1);
               idx -= 1;
            }
         }
         $scope.results = temp_results; 
      };
      
      // watch for new disease input
      $scope.$watch( function() {return Data.getInputDisease(); }, function(newVal, oldVal) {
         if (newVal != oldVal) {
            $scope.disease_info = newVal;
            initialTypes(newVal);
            $scope.generateQueryResults();
         }
      });

      // watch for new $scope.result
      $scope.$watch('results', function(newVal, oldVal) {
         if (newVal != oldVal) {
            Data.setPageData(newVal);
         }
      });
   });

   app.controller('PageController', function($scope, Data) {
      $scope.currentPage = 1;
      $scope.numPerPage = 10;
      $scope.maxSize = 30;                // max selectable page
      $scope.filtered_results = [];       // results will be shown in a page
      $scope.results = [];

      $scope.$watch( function() { return Data.getPageData(); }, function(newVal, oldVal) {
         if (newVal != oldVal ) {
            $scope.results = newVal;
            $scope.currentPage = 1;
            updateFilteredItems();
         }
      });

      $scope.$watch('currentPage + numPerPage', updateFilteredItems);

      function updateFilteredItems() {
         var begin = (($scope.currentPage - 1) * $scope.numPerPage);
         var end = begin + $scope.numPerPage;
         $scope.filtered_results = $scope.results.slice(begin, end);
      }
   });

   app.controller('ModalController', function($scope, $modal, $log) {
      /*
      $scope.content = [
         {
            'age': 31
         },
         {
            'age': 32
         }
      ];      
      */
      $scope.open = function(info) {
         console.log(info);
         var modalInstance = $modal.open({
            templateUrl: 'modalContent.html',
            controller: 'ModalInstanceController',
            resolve: {
               info: function() {
                  return info;
               }
            }
         });
      };
   });

   app.controller('ModalInstanceController', function($scope, $modalInstance, info) {
      console.log(info.title);
      //$scope.title = info.title;
      $scope.content = info.content;

      $scope.ok = function() {
         $modalInstance.close();
      };
   });

   app.factory("Data", ["$http", "$q",  function($http, $q) {
      var data = {
         result_list: []
      };

      var queried_disease = '';
      var results = [];

      return {
         getInputDisease: function() {
            return queried_disease;
         },
         setInputDisease: function(_disease) {
            function successCallback(resp) {
               console.log(resp.data);
               console.log(typeof(resp.data));
               queried_disease = JSON.parse(resp.data);
               //console.log(queried_disease);
            }
            ///*
            $http({
               method: 'POST',
               url: 'http://192.168.10.116:5011/?disease=' + encodeURIComponent(_disease),
               headers: {'Content-Type': 'application/x-www-form-encoded;charset=UTF-8'}
               //data: {'disease': input}
            }).then(successCallback);
            //*/
            //var data = {'disease': 'WonJinHo'};
            //$http.post('http://192.168.10.108:5010', data).then(successCallback);
            /*
            var dd = '';
            function useReturnData(data){
               console.log(data.responseText);
                dd = JSON.parse(data.responseText);
                console.log(typeof(dd));
                queried_disease = dd;
            };
            $.ajax({
               async: false,
               type: 'GET',
               url: 'http://192.168.10.108:5010',
               dataType: "json",
               cache: false,
               statusCode: {
                  200: function(resp) {
                     console.log('hahaha');
                     useReturnData(resp);
                  }
               }
            });
            */
            /*
            dd = new Object();
            loadDisease(_disease).then(function(resp) {
               console.log('finish insetInput');
               queried_disease = resp;
               console.log(queried_disease);
            });
            */
            //queried_disease = resp;
            //console.log(queried_disease);
            //console.log('finish insetInput');
         },
         getPageData: function() {
            return results;
            //return data.result_list;
         },
         setPageData: function(_results) {
            results = _results;
            //data.result_list = _data;
         }
      }
   }]);
})();

function loadDisease(callback) {
   var url = 'http://192.168.10.108:5010';

   $.ajax({
      url: url,
      //headers: {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
      //contentType: "application/json; charset=utf-8",
      //crossOrigin: false,
      //method: "GET",
      dataType: "json",
      cache: false,
      success: function(data) {
         return data;
      } 
   });
   /*
   }).done(function(resp) {
      console.log(resp);
      console.log('in done');
   });
   */
};


function isSubArray (subArray, array) {
   for(var i = 0 , len = subArray.length; i < len; i++) {
      if($.inArray(subArray[i], array) == -1)
         return false;
   }
   return true;
}

