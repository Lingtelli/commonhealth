(function() {
   var app = angular.module('query-system', ['ui.bootstrap']);

   app.controller('SystemController', ['$scope', 'Data', function($scope, Data) {
      $scope.input_disease = '';

      $scope.query = function(_disease) {
         $scope.input_disease = _disease;
         /*
         getDiseaseInfo(_disease).then(function(disease_info) {
            console.log(disease_info);
            console.log('finish setInput');
         });
         */
         Data.setInputDisease(_disease);
         console.log('finish setInput');
      };
   }]);

   /***************************************************************
    *    In charge of type selection and generate the query result
    * *************************************************************/
   app.controller("TypeController", function($scope, Data) {
      $scope.selected_type_list = [];
      $scope.type_list = [];
      $scope.type_list = [];
      $scope.result_list = [];
      $scope.diseaseddd = '';

      this.selectType = function(_type) {
         console.log($scope.selected_type_list);
         if (! this.isSelected(_type)) {
            $scope.selected_type_list.push(_type);
         }else {
            console.log('is already selected');
            var idx = $scope.selected_type_list.indexOf(_type);
            $scope.selected_type_list.splice(idx, 1);
            $(this).removeAttr('checked');
         }
         console.log($scope.selected_type_list);
      };

      this.isSelected = function(_type) {
         return ($scope.selected_type_list.indexOf(_type) > -1 )
      };

      function initialTypeList(data) {
         $scope.selected_type_list = Object.keys(data);
         $scope.type_list = Object.keys(data);
      };
      
      $scope.generateSnippet = function(content) {
         console.log(typeof(content));
         return 'this is the snippet of ' + content;
         console.log(typeof(content));
      };

      $scope.generateResultList = function() {
         var idx = 0;
         var jdx = 0;
         var output = new Array();
         var fragment_id_list = [];
         console.log($scope.diseaseddd);
         for (idx = 0; idx < $scope.selected_type_list.length; idx++) {
            var title = $scope.selected_type_list[idx];
            fragment_id_list = Object.keys($scope.diseaseddd[title]);
            for (jdx = 0; jdx < fragment_id_list.length; jdx++) {
               fragment_id = fragment_id_list[jdx];
               output.push({
                  'title': $scope.diseaseddd[title][fragment_id]['title'],
                  // make snippet
                  'snippet': $scope.generateSnippet($scope.diseaseddd[title][fragment_id]['content']),
                  'content': $scope.diseaseddd[title][fragment_id]['content'],
                  'article_link': $scope.diseaseddd[title][fragment_id]['article_id']
               });
            }
         }
         $scope.result_list = Array.from(new Set(output));   // make an array to set
      };

      $scope.$watch( function() {return Data.getInputDisease(); }, function(newVal, oldVal) {
         if (newVal != oldVal) {
            $scope.diseaseddd = newVal;
            console.log($scope.diseasedddd);
            initialTypeList(newVal);
            $scope.generateResultList();
         }
      });

      $scope.$watch('result_list', function(newVal, oldVal) {
         if (newVal != oldVal) {
            Data.setData(newVal);
         }
      });

   });

   app.controller('PageController', function($scope, Data) {
      $scope.currentPage = 1;
      $scope.numPerPage = 10;
      $scope.maxSize = 30;                // max selectable page
      $scope.filtered_result_list = [];   // result_list will be shown in a page
      $scope.result_list = [];

      $scope.$watch( function() { return Data.getData(); }, function(newVal, oldVal) {
         if (newVal != oldVal ) {
            $scope.result_list = newVal;
            $scope.currentPage = 1;
            updateFilteredItems();
         }
      });

      $scope.$watch('currentPage + numPerPage', updateFilteredItems);

      function updateFilteredItems() {
         var begin = (($scope.currentPage - 1) * $scope.numPerPage);
         var end = begin + $scope.numPerPage;
         $scope.filtered_result_list = $scope.result_list.slice(begin, end);
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
         console.log('info is:');
         console.log(info.content);
         var modalInstance = $modal.open({
            templateUrl: 'modalContent.html',
            controller: 'ModalInstanceController',
            resolve: {
               info: function() {
                  console.log('going to return');
                  return info;
               }
            }
         });
      };
   });

   
   app.controller('ModalInstanceController', function($scope, $modalInstance, info) {
      console.log(info);
      $scope.title = info.title;
      $scope.content = info.content;

      $scope.ok = function() {
         $modalInstance.close();
      };
   });


   app.factory("Data", ["$http", "$q",  function($http, $q) {
      var data = {
         result_list: []
      };

      var input_disease = '';
      var result_list = [];
      /*
         function getDiseaseInfo(_disease) {
         var url = '';
         var promise =  $http({
         url: url,
         method: "GET",
         });
         return promise;
         }
      */

      return {
         getInputDisease: function() {
            return input_disease;
         },
            setInputDisease: function(_disease) {
               /*
               getDiseaseInfo(_disease).then(function(disease_info) {
                  console.log('waiting for data');
                  //console.log(disease_info);
                  input_disease = getDiseaseInfo(_disease);
                  console.log('finish insetInput');
               });
               */
               input_disease = disease_info
               //console.log('finish insetInput');
            },
            getData: function() {
               return result_list;
               //return data.result_list;
            },
            setData: function(_data) {
               result_list = _data;
               //data.result_list = _data;
            }
      }
   }]);

})();


function getDiseaseInfo(disease) {
   //console.log(disease_info);
   return disease_info;
   //var url = 'http://www.lingtelli.com:8110/tasks/keywords/term?taskId=5667b65bd19300208759ac31&taskId=551b64f6d19300511c8f12f6&user=lingtellitest&stride=day&from=1441036800&to=1459353600&top=50';
   var url = 'http://api.flickr.com/services/feeds/photos_public.gne?jsoncallback=?';

   
   /*
   return fetch(url, {
      method: 'get',
      crossOrigin: true,
      datatype: 'jsonp',
      headers: {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
   }).then(function(rsponse){
      console.log(response);
      return response;
   });
   */
   /*
   console.log('in getDisease');
   return $.getJSON(url).then(function(response) {
      console.log('get data');
      return response;
   });
   */
   /*
   //$.when($.ajax({
   return $.ajax({
      url: url,
      headers: {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
      crossOrigin: true,
      method: "GET",
      dataType: "jsonp",
      statusCode: {
         200: function(disease_info) {
            console.log('get data succeed');
         }
      }
   }).done(function(retrieved_data) {
      //console.log(retrieved_data);
      console.log('in done');
      return disease_info
   });
   */
};


var disease_info2 = {
   "cluster1": [
      { 
         "fragment_id": "段落_id_1",
         "fragment_type": ["type1, type2"],
         "title": "文章id-1--標題",
         "article_id": "1",
         "fragment_content": "段落內容-id-1"
      },
      { 
         "fragment_id": "段落_id_2",
         "fragment_type": ["type1"],
         "title": "文章id-2--標題",
         "article_id": "1",
         "fragment_content": "段落內容-id-2"
      },
      { 
         "fragment_id": "段落_id_3",
         "fragment_type": ["type2"],
         "title": "文章id-3--標題",
         "article_id": "2",
         "fragment_content": "段落內容-id-3"
      },
   ],
   "cluster2": [
      { 
         "fragment_id": "段落_id_4",
         "fragment_type": ["type1, type3"],
         "title": "文章id-1--標題",
         "article_id": "1",
         "fragment_content": "段落內容-id-4"
      },
      { 
         "fragment_id": "段落_id_5",
         "fragment_type": ["type5", "type6", "type7"],
         "title": "文章id-3--標題",
         "article_id": "3",
         "fragment_content": "段落內容-id-5"
      },
      { 
         "fragment_id": "段落_id_6",
         "fragment_type": ["type2"],
         "title": "文章id-3--標題",
         "article_id": "1",
         "fragment_content": "段落內容-id-6"
      },
   ]
};


var disease_info2 = {
   "Symptom": {
      "fragment_id_1": { 
         "title": "標題-文章id-1",
         "article_id": "1",
         "content": "內容-id-1"
      },
      'fragment_id_2': {
         "title": "標題-文章id-2",
         "article_id": "2",
         "content": "內容-id-2"
      },
      'fragment_id_23': {
         "title": "標題-文章id-23",
         "article_id": "23",
         "content": "內容-id-23"
      },
      'fragment_id_72': {
         "title": "標題-文章id-72",
         "article_id": "72",
         "content": "內容-id-72"
      },
      'fragment_id_82': {
         "title": "標題-文章id-82",
         "article_id": "82",
         "content": "內容-id-82"
      },
      'fragment_id_21': {
         "title": "標題-文章id-21",
         "article_id": "21",
         "content": "內容-id-21"
      },
      'fragment_id_24': {
         "title": "標題-文章id-24",
         "article_id": "24",
         "content": "內容-id-24"
      },
      'fragment_id_90': {
         "title": "標題-文章id-90",
         "article_id": "90",
         "content": "內容-id-90"
      },
      'fragment_id_3': {
         "title": "標題-文章id-3",
         "article_id": "3",
         "content": "內容-id-3" 
      }
   },
   "Cause": {
      "fragment_id_1": {
         "title": "標題-文章id-1",
         "article_id": "1",
         "content": "內容-id-1"
      },
      'fragment_id_431': {
         "title": "標題-文章id-431",
         "article_id": "431",
         "content": "內容-id-431"
      },
      'fragment_id_24': {
         "title": "標題-文章id-24",
         "article_id": "24",
         "content": "內容-id-24"
      },
      'fragment_id_21': {
         "title": "標題-文章id-21",
         "article_id": "21",
         "content": "內容-id-21"
      },
      'fragment_id_222': {
         "title": "標題-文章id-222",
         "article_id": "222",
         "content": "內容-id-222"
      },
      'fragment_id_2': {
         "title": "標題-文章id-2",
         "article_id": "2",
         "content": "內容-id-2"
      },
      'fragment_id_345': {
         "title": "標題-文章id-345",
         "article_id": "345",
         "content": "內容-id-345"
      },
      'fragment_id_90': {
         "title": "標題-文章id-90",
         "article_id": "90",
         "content": "內容-id-90"
      },
      'fragment_id_127': {
         "title": "標題-文章id-127",
         "article_id": "127",
         "content": "內容-id-127"
      },
      'fragment_id_212': {
         "title": "標題-文章id-212",
         "article_id": "212",
         "content": "內容-id-212"
      },
      'fragment_id_52': {
         "title": "標題-文章id-52",
         "article_id": "52",
         "content": "內容-id-52"
      }
   }
};

