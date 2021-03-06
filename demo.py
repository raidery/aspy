import logging
from aspy.aslgen import analytic_server

a = analytic_server("rhe701.fyre.ibm.com",9080,False,"admin","test")
rs = a.create_pipeline().read_datasource("DRUG1N").select("lambda x: x.Age>30").derive("ratio","lambda x:x.Na/x.K").aggregate(["BP"],["count","mean_ratio"]).run()
for row in rs:
    print(str(row))



print(str(rs.toPandas()))