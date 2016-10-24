(function() {
    var app = angular.module('query-system', ['ui.bootstrap']);

    app.controller('SystemController', function() {
        this.disease_info = disease_info;
    });

    app.controller("TabController", function() {
        this.tab_list = new Array();
        this.result_list = new Array();

        this.selectTab = function(_tab) {
            console.log(typeof(_tab));
            if (! this.isSelected(_tab)) {
                this.tab_list.push(_tab);
            }else {
                console.log('is already selected');
                var idx = this.tab_list.indexOf(_tab);
                this.tab_list.splice(idx, 1);
                $(this).removeAttr('checked');
            }
            console.log(this.tab_list);
            this.showResult();
        };

        this.isSelected = function(_tab) {
            return (this.tab_list.indexOf(_tab) > -1 )
        };

        this.showResult = function() {
            console.log("in show Result");
            var idx = 0;
            var jdx = 0;
            var output = new Array();
            for (idx = 0; idx < this.tab_list.length; idx++) {
                //console.log(typeof(jQuery.makeArray(disease_info[idx]['paragraph_list'])));
                var title = this.tab_list[idx];
                console.log("checking " + title + " ...");
                for (jdx = 0; jdx < (disease_info[title]).length; jdx++) {
                    paragraph_id = disease_info[title][jdx];
                    output.push({
                        "title": paragraph_info[paragraph_id]["title"],
                        "snippet": paragraph_info[paragraph_id]["snippet"]
                    });
                    console.log(paragraph_info[paragraph_id]["title"])
                        console.log(paragraph_info[paragraph_id]["snippet"])
                }
            }
            this.result_list = Array.from(new Set(output));
            console.log(this.result_list);
        };
    });

    app.controller("TodoController", function($scope) {
        $scope.todos = [];
        $scope.filteredTodos = [];

        $scope.currentPage = 1;
        $scope.numPerPage = 10;
        $scope.maxSize = 5;

        $scope.$watch('currentPage + numPerPage', updateFilteredItems);

        makeTodos();

        function updateFilteredItems() {
            var begin = (($scope.currentPage - 1) * $scope.numPerPage);
            var end = begin + $scope.numPerPage;
            $scope.filteredTodos = $scope.todos.slice(begin, end);
        }

        function makeTodos() {
            console.log("in todocontroller");
            console.log();
            $scope.todos = [];
            for (i = 1; i <= 12; i++) {
                $scope.todos.push({
                    text: 'todo ' + i,
                    done: false
                });
            }
        }
    });

    var disease_info = {
        "Symptom": [
            "para_id1",
        'para_id2',
        'para_id3',
        ],
        "Cause": [
            "para_id1",
        'para_id4',
        'para_id5',
        ]
    };

    var paragraph_info = {
        "para_id1": {
            "title": "title of para_id1",
            "snippet": "snippet of para_id1",
            "content": "content of praragah_id1"
        },
        'para_id2': {
            "title": "title of para_id2",
            "snippet": "snippet of para_id2",
            "content": "content of praragah_id2"
        },
        'para_id3': {
            "title": "title of para_id3",
            "snippet": "snippet of para_id3",
            "content": "content of praragah_id3"
        },
        'para_id4': {
            "title": "title of para_id4",
            "snippet": "snippet of para_id4",
            "content": "content of praragah_id4"
        },
        'para_id5': {
            "title": "title of para_id5",
            "snippet": "snippet of para_id5",
            "content": "content of praragah_id5"
        }
    };

    var disease_info2 = [
    {
        title: "Symptom",
            paragraph_list: [
                'para_id1',
            'para_id2',
            'para_id3'
                ]
    },
    {
        title: "Cause",
        paragraph_list: [
            'para_id1',
        'para_id4',
        'para_id5'
            ]
    }
    ];

})();
