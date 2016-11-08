(function() {
   var app = angular.module('query-system', ['ui.bootstrap']);

   app.controller('SystemController', ['$scope', 'Data', function($scope, Data) {

      $scope.query = function(query_words, author='', article_source='') {
         Data.setCurrentPage(1);
         // _query, _first_time, _author, _categories, _date_start, _date_end
         Data.setQuerySetting(query_words, true, null, null, null, null);
         Data.getApiData();
      };
   }]);

   /***************************************************************
    *    In charge of type selection and generate the query result
    * *************************************************************/
   app.controller("TypeController", function($scope, Data) {
      $scope.results = null;
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

      $scope.lookupCluster = function(clusterid) {
         console.log($scope.start_date, $scope.end_date, $('#author_input').val(), $('#source_input').val());
      }

      $scope.generateQueryResults = function() {

         var selected_groups = $("input[name='selected_center']:checked");
         if (selected_groups != null) {
            var groups = [];
            for (var idx = 0; idx < selected_groups.length; ++idx) {
               groups.push(selected_groups[idx].value);
            }
         }
         console.log('query: ', $scope.query_words, 'author:', $scope.query_author, 'source: ', $scope.query_article_source, 'group: ', groups);
         console.log('start: ', $scope.start_date, 'end: ', $scope.end_date);
         
         Data.setCurrentPage(1);
         // _query, _first_time, _author, _categories, _date_start, _date_end
         Data.setQuerySetting($scope.query_words, false, $scope.query_author, $scope.query_article_source, $scope.start_date, $scope.end_date);
         Data.getApiData();
      };
      
      $scope.exportJSON = function() {
         var json_data = new Blob([JSON.stringify($scope.results)], { type: 'text/json' });
         var link = document.createElement("a");
         link.setAttribute("href", window.URL.createObjectURL(json_data));
         link.setAttribute("download", "query_result.json");
         document.body.appendChild(link);
         link.click();
      };

      // watch for new disease input
      $scope.$watch( function() {return Data.getInputDisease(); }, function(newVal, oldVal) {
         if (newVal != oldVal) {
            $scope.results = Array.from(newVal);
            if (Data.isFirstQuery()) {
               $('#source_input').val('');
               $('#author_input').val('');
               $('#source_input').html('');
               $('#author_input').html('');
               $scope.query_author = null;
               $scope.query_article_source = null;
               $scope.info_sidebar = newVal;
               $scope.info_sidebar = Array.from($scope.info_sidebar);
               $scope.totalDisplayed = 5;
               initialTypes(newVal);
            }
         }
      });

      $scope.loadMore = function() {
         $scope.totalDisplayed += 5;
      };

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
      $scope.maxSize = 20;                // max selectable page
      $scope.filtered_results = [];       // results will be shown in a page
      $scope.results = [];

      $scope.$watch( function() { return Data.getPageData(); }, function(newVal, oldVal) {
         if (newVal != oldVal ) {
            $scope.results = newVal;
            $scope.currentPage = Data.getCurrentPage();
            updateFilteredItems();
         }
      });
      
      $scope.$watch('currentPage + numPerPage', nextPageQuery);

      function nextPageQuery() {
         Data.setCurrentPage($scope.currentPage);
         console.log(Data.getCurrentPage());
         Data.getApiData();
      }
      

      function updateFilteredItems() {
         var begin = (($scope.currentPage - 1) * $scope.numPerPage);
         var end = begin + $scope.numPerPage;
         $scope.filtered_results = $scope.results.slice(begin, end);
      }
   });

   app.controller('ModalController', function($scope, $modal, $log) {
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
      var is_first_query = null;
      var results = [];
      var detail = [];

      var query = [];
      var categories = [];
      var author = null;
      var date_start = null;
      var date_end = null;
      var page_start = 1;
      var query_string = '';

      return {
         isFirstQuery: function() {
            return is_first_query; 
         },
         getInputDisease: function() {
            return query_resp;
         },
         setQuerySetting: function(_query, _first_time=false, _author=null, _categories=null, _date_start=null, _date_end=null) {
            
            query_string = '';
            query = _query;
            is_first_query = _first_time;
            categories = _categories;
            author = _author;
            date_start = _date_start;
            date_end = _date_end;

            if (_date_start != null) {
               date_start = msToDate(_date_start);
               date_end = msToDate(_date_end);
            }
            
            if (query != null) {
               query = query.split(' ');
               query_len = query.length;

               for (var idx = 0; idx < query_len; idx++)
                  if (idx < query_len - 1)
                     query_string += ('query=' + encodeURIComponent(query[idx]) + '&');
                  else
                     query_string += ('query=' + encodeURIComponent(query[idx]));
            }else {
               query_string += ('query=' + encodeURIComponent(' '));
            }

            if ((author != null) && (author.length > 0) ) 
               query_string += ('&author=' + encodeURIComponent(author));

            if (categories != null && (categories.length > 0)) {
               // 不知輸入是否為string?
               categories = categories.split(' ');
               category_size = categories.length;

               for (var idx = 0; idx < category_size; idx++)
                  if (idx < category_size - 1)
                     query_string += ('categories=' + encodeURIComponent(categories[idx]) + '&');
                  else
                     query_string += ('categories=' + encodeURIComponent(categories[idx]));
            }

            if ((date_start != null) && (date_end != null)) 
               query_string += ('&publish_date=' + encodeURIComponent(date_start) + '&publish_date=' + encodeURIComponent(date_end));
         },
         getApiData: function () {
            if (is_first_query == null)
               return 

            console.log(page_start);

            var temp_query_string = query_string;
            if (page_start != null) {
               var cluster_idx = (page_start - 1) * 10
               temp_query_string = temp_query_string + ('&cluster_idx=' + encodeURIComponent(cluster_idx));
            }
            console.log('http://lingtelli.com:5012/query/?' + temp_query_string);

            $http({
               method: 'POST',
               url: 'http://lingtelli.com:5012/query/?' + temp_query_string,
               headers: {'Content-Type': 'application/x-www-form-encoded;charset=UTF-8'}
            }).then(successCallback);

            function successCallback(resp) {
               query_resp = resp.data;
               console.log('resp received, reindering...');
               console.log(query_resp);
            };
         },
         getPageData: function() {
            return results;
         },
         setPageData: function(_results) {
            results = _results;
         },
         getQuerySetting: function() {
            console.log(words, source, author, date_start, date_end, groups, page_start);   
         },
         setCurrentPage: function(_page) {
            page_start = _page;
            console.log('current page is set to: ', page_start);
         },
         getCurrentPage: function() {
            return page_start;
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
