(function() {
    var app = angular.module('query-system', ['ui.bootstrap']);

    app.controller('SystemController', function() {
        this.disease_info = disease_info;
    });

    app.controller('InputController', ['$scope', function($scope) {
      $scope.query = function(_disease) {
         $scope.input_disease = _disease
         console.log('input disease is: ', $scope.input_disease);
      };
    }]);


    app.controller("TagController", function($scope, Data) {
        this.tag_list = new Array();
        $scope.result_list = [];

        this.selectTag = function(_tag) {
            if (! this.isSelected(_tag)) {
                this.tag_list.push(_tag);
            }else {
                console.log('is already selected');
                var idx = this.tag_list.indexOf(_tag);
                this.tag_list.splice(idx, 1);
                $(this).removeAttr('checked');
            }
            console.log(this.tag_list);
        };

        this.isSelected = function(_tag) {
            return (this.tag_list.indexOf(_tag) > -1 )
        };

        this.generateResultList = function() {
            var idx = 0;
            var jdx = 0;
            var output = new Array();
            for (idx = 0; idx < this.tag_list.length; idx++) {
                var title = this.tag_list[idx];
                for (jdx = 0; jdx < (disease_info[title]).length; jdx++) {
                    paragraph_id = disease_info[title][jdx];
                    output.push({
                        "title": paragraph_info[paragraph_id]["title"],
                        "snippet": paragraph_info[paragraph_id]["snippet"]
                    });
                }
            }
            $scope.result_list = Array.from(new Set(output));   // make an array to set
        };

        $scope.$watch('result_list', function(newVal, oldVal) {
            if (newVal != oldVal ) {
                Data.setData(newVal);
            }
        });
    });

    app.controller('PageController', function($scope, Data) {
        $scope.currentPage = 1;
        $scope.numPerPage = 10;
        $scope.maxSize = 30;                // max selectable page
        $scope.filtered_result_list = [];   // result_list will be shown in a page
        $scope.result_list = []

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

    app.factory("Data", function() {
        var data = {
            result_list: []
        };

        var result_list = [];
        return {
            getData: function() {
                         return result_list;
                         //return data.result_list;
                     },
        setData: function(_data) {
                     result_list = _data;
                     //data.result_list = _data;
                 }
        }
    });

    var disease_info = {
        "Symptom": [
            "para_id_1",
        'para_id_2',
        'para_id_3',
        'para_id_13',
        'para_id_21',
        'para_id_34',
        'para_id_53',
        'para_id_23',
        'para_id_224',
        'para_id_225',
        'para_id_10'
            ],
        "Cause": [
            "para_id_1",
        'para_id_431',
        'para_id_52'
            ]
    };

    var paragraph_info = {
        "para_id_1": {
            "title": "標題-段落編號1",
            "snippet": "片段-段落編號1",
            "content": "內文-段落編號1"
        },
        'para_id_2': {
            "title": "標題-段落編號2",
            "snippet": "片段-段落編號2",
            "content": "內文-段落編號2"
        },
        'para_id_3': {
            "title": "標題-段落編號3",
            "snippet": "片段-段落編號3",
            "content": "內文-段落編號3"
        },
        'para_id_4': {
            "title": "標題-段落編號4",
            "snippet": "片段-段落編號4",
            "content": "內文-段落編號4"
        },
        'para_id_5': {
            "title": "標題-段落編號5",
            "snippet": "片段-段落編號5",
            "content": "內文-段落編號5"
        },
        'para_id_52': {
            "title": "標題-段落編號52",
            "snippet": "片段-段落編號52",
            "content": "內文-段落編號52"
        },
        'para_id_431': {
            "title": "標題-段落編號431",
            "snippet": "片段-段落編號431",
            "content": "內文-段落編號431"
        },
        'para_id_13': {
            "title": "標題-段落編號13",
            "snippet": "片段-段落編號13",
            "content": "內文-段落編號13"
        },
        'para_id_21': {
            "title": "標題-段落編號21",
            "snippet": "片段-段落編號21",
            "content": "內文-段落編號21"
        },
        'para_id_34': {
            "title": "標題-段落編號34",
            "snippet": "片段-段落編號34",
            "content": "內文-段落編號34"
        },
        'para_id_53': {
            "title": "標題-段落編號53",
            "snippet": "片段-段落編號53",
            "content": "內文-段落編號53"
        },
        'para_id_23': {
            "title": "標題-段落編號23",
            "snippet": "片段-段落編號23",
            "content": "內文-段落編號23"
        },
        'para_id_10': {
            "title": "標題-段落編號10",
            "snippet": "片段-段落編號10",
            "content": "內文-段落編號10"
        },
        'para_id_224': {
            "title": "標題-段落編號224",
            "snippet": "片段-段落編號24",
            "content": "內文-段落編號225"
        },
        'para_id_225': {
            "title": "標題-段落編號225",
            "snippet": "片段-段落編號225",
            "content": "內文-段落編號225"
        }
    };

    var disease_info2 = [
    {
        title: "Symptom",
            paragraph_list: [
                'para_id_1',
            'para_id_2',
            'para_id_3'
                ]
    },
    {
        title: "Cause",
        paragraph_list: [
            'para_id_1',
        'para_id_4',
        'para_id_5'
            ]
    }
    ];

})();
