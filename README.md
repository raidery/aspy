# aspy

```
!pip install -U git+https://github.com/raidery/aspy.git
```

```
from aspy import analytic_server
```

```
val conf_read_1 = {"dataSource": "TrivialModelInput"}
val conf_pasw_tree_2 = {"InputFieldList": ["field1"],"TargetField": "field3","TreeGrowingMethod": "Chaid"}
val conf_pasw_tree_3 = [{"export": true,"name": "PMML","uri": "/pmml.con"},{"export": true,"name": "StatXML","uri": "/stat.con"}]
read(conf_read_1) ->
   cf_tree:tree(conf_pasw_tree_2,_,conf_pasw_tree_3)


val conf_read_1 = {"dataSource": "TrivialScoreInput"}
val conf_pasw_scoring_2 = {"isOutputInputData": true}
val conf_pasw_scoring_3 = [{"export": true,"name": "InputPMML","uri": "/pmml.con"}]
val conf_write_4 = {"dataModelDestination": "_chaidTrivial_score_output/_chaidTrivial_score_output.xml","dataDestination": "_chaidTrivial_score_output/_chaidTrivial_score_output.csv","type": "text/csv"}
read(conf_read_1) ->
   cf_scoring:scoring(conf_pasw_scoring_2,conf_pasw_scoring_3,_) ->
   write(conf_write_4)


```