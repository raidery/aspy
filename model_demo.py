import logging
from aspy.aslgen import analytic_server

logger = logging.getLogger('aspy')

a = analytic_server("rhe701.fyre.ibm.com",9080,False,"admin","test")




rs = a.create_pipeline().read_datasource("DRUG1N").select("lambda x: x.Age>10").derive("ratio","lambda x:x.Na/x.K").run()
#rs = a.create_pipeline().read_datasource("DRUG1N").tree_chaid(conf_tree,conf_outcon).run()


logger.info("Execute : %s" % "rhe701.fyre.ibm.com")

for row in rs:
    print(str(row))

"""
for row in rs:
    print(str(row))


print(str(rs.toPandas()))
"""

"""
conf_tree = {"InputFieldList": ["Age","Sex","BP","Cholesterol"],"TargetField": "Drug","TreeGrowingMethod": "Chaid"}
conf_outcon = [{"export": True,"name": "PMML","uri": "/pmml.con"},{"export": True,"name": "StatXML","uri": "/stat.con"}]
modeling = a.create_pipeline().read_datasource("DRUG1N").select("lambda x: x.Age>10").derive("ratio","lambda x:x.Na/x.K").tree(conf_tree,conf_outcon).run()
"""


"""
scoreConf = {"isOutputInputData": True}
scoreInputConf = [{"export": True,"name": "InputPMML","uri": "/pmml.con"}]
scoring = a.create_pipeline().read_datasource("DRUG1N").scoring(scoreConf,scoreInputConf).run()
"""

buildConf = {"InputFieldList": ["Sex","BP","Cholesterol"],"TargetField": "Age"}
inputConf = [{"export": True,"name": "PMML","uri": "/pmml.con"},{"export": True,"name": "StatXML","uri": "/stat.con"}]
modeling = a.create_pipeline().read_datasource("DRUG1N").select("lambda x: x.Age>10").linear(buildConf,inputConf).run()