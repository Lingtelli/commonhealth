(function() {
   var app = angular.module('query-system', ['ui.bootstrap']);

   app.controller('SystemController', ['$scope', 'Data', function($scope, Data) {

      $scope.query = function(query_words, author='', article_source='') {
         $scope.query_words = query_words;
         $scope.query_author = null;
         $scope.query_article_source = null;
         $scope.query_keyword = null;
         $scope.query_clusterid = null;
         //$scope.start_date = null;
         //$scope.end_date = null;

         //console.log('len author:', $scope.query_author.length, ' len source: ', $scope.query_article_source.length);
         //console.log('query: ', $scope.query_words, 'author:', $scope.query_author, 'source: ', $scope.query_article_source);
         Data.setInputDisease(query_words, first_time=true);
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
         var centers = [];
         var _centers = [];
         var publish_dates = [];
         var clusterids = [];
         var authors = [];

         for (var idx = 0; idx < _disease_clusters.length; idx++) {
            var cluster = _disease_clusters[idx];
            
            centers.push(cluster['centers'])
            clusterids.push(cluster['clusterid']);

            for (var jdx in cluster['member'])
               _centers = _centers.concat(cluster['member'][jdx]['_centers']);

            for (var jdx in cluster['member'])
               publish_dates.push(cluster['member'][jdx]['publish_date'])

            for (var jdx in cluster['member'])
               authors.push(cluster['member'][jdx]['author'])
         }
         $scope.clusterids = Array.from(clusterids);
         $scope.authors = Array.from(new Set(authors));
         $scope.types = Array.from(new Set(_centers));
         $scope.deselected_types = [];

         var earliest_date = publish_dates.reduce(function (pre, cur) {
            return Date.parse(pre) > Date.parse(cur) ? cur : pre;
         });
         var latest_date = publish_dates.reduce(function (pre, cur) {
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


         // get the time range, the block of code can be places somewhere.
         $('#daterange').on('apply.daterangepicker', function(ev, picker) {
            $scope.start_date = Date.parse(picker.startDate.format('YYYY-MM-DD'));
            $scope.end_date = Date.parse(picker.endDate.format('YYYY-MM-DD'));
         });


         $scope.start_date = Date.parse(earliest_date);
         $scope.end_date = Date.parse(latest_date);
      };
      
      $scope.generateSnippet = function(content) {
         return content.slice(0, 5);
      };

      $scope.generateQueryResults = function(author=null, article_source=null) {
         var selected_group = $("input[name='selected_center']:checked").val();  // get 'value' attribute
         if (selected_group != null) {
            console.log(selected_group);
            selected_group = selected_group.split('_');
            selected_center = selected_group[0];
            selected_clusterid = selected_group[1];
         }else {
            selected_center = null;
            selected_clusterid = null; 
         }
         $scope.query_author = author;
         $scope.query_article_source = article_source;

         console.log('query: ', $scope.query_words, 'author:', $scope.query_author, 'source: ', $scope.query_article_source);
         console.log('start: ', $scope.start_date, 'end: ', $scope.end_date, 'center: ', selected_center, 'clusterid: ', selected_clusterid);
         Data.setInputDisease($scope.query_words, false, $scope.query_author, $scope.query_article_source, selected_clusterid, selected_center, $scope.start_date, $scope.end_date);
      };
      
      // watch for new disease input
      $scope.$watch( function() {return Data.getInputDisease(); }, function(newVal, oldVal) {
         if (newVal != oldVal) {
            $scope.results = Array.from(newVal);
            var json_data = "text/json; charset=utf-8," + encodeURIComponent(JSON.stringify($scope.results));
            $("#export_container").html('<a href="data:' + json_data + '" download="query_result.json">匯出JSON</a>');
            if (Data.isFirstQuery()) {
               $scope.info_sidebar = newVal;
               $scope.info_sidebar = Array.from($scope.info_sidebar);
               initialTypes(newVal);
            }
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
      console.log(info.clusterid);
      //$scope.clusterid = info.clusterid;
      $scope.content = info.content;

      $scope.ok = function() {
         $modalInstance.close();
      };
   });

   app.factory("Data", ["$http", "$q",  function($http, $q) {
      var data = {
         result_list: []
      };

      var query_resp = '';
      var is_first_query = true;
      var results = [];

      return {
         isFirstQuery: function() {
            return is_first_query; 
         },
         getInputDisease: function() {
            return query_resp;
         },
         setInputDisease: function(query, first_time=false, author=null, article_source=null, clusterid=null, center=null, start=null, end=null) {
            if (start != null) {
               start = msToDate(start);
               end = msToDate(end);
            }
            query_str = '';
            query = query.split(' ');
            query_len = query.length;
            for (var idx = 0; idx < query_len; idx++)
               if (idx < query_len -1)
                  query_str += ('query=' + encodeURIComponent(query[idx]) + '&');
               else
                  query_str += ('query=' + encodeURIComponent(query[idx]));
            
            if ((author != null) && (author.length > 0) ) 
               query_str += ('&author=' + encodeURIComponent(author));
            if (article_source != null && (article_source.length > 0)) 
               query_str += ('&source=' + encodeURIComponent(article_source));
            if (center != null) 
               query_str += ('&center=' + encodeURIComponent(center));
            if (start != null) 
               query_str += ('&start=' + encodeURIComponent(start));
            if (end != null)
               query_str += ('&end=' + encodeURIComponent(end));
            if (clusterid != null)
               query_str += ('&clusterid=' + encodeURIComponent(clusterid));
            
             
            console.log(query_str);
            $http({
               method: 'POST',
               url: 'http://lingtelli.com:5012/commonhealth_api/?' + query_str,
               headers: {'Content-Type': 'application/x-www-form-encoded;charset=UTF-8'}
            }).then(successCallback);

            function successCallback(resp) {
               query_resp = resp.data;
               is_first_query = first_time;
            }
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

function isSubArray (subArray, array) {
   for(var i = 0 , len = subArray.length; i < len; i++) {
      if($.inArray(subArray[i], array) == -1)
         return false;
   }
   return true;
}

function msToDate(date_ms) {
   date_obj = new Date(date_ms);
   year = (date_obj.getFullYear()).toString();
   month = (date_obj.getMonth() + 1).toString();
   month = month.length > 1 ? month : '0'.concat(month); 
   date = (date_obj.getDate()).toString();
   date = date.length > 1 ? date : '0'.concat(date); 
   return [year, month, date].join('');
}
