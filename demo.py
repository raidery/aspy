import logging
from aspy.aslgen import analytic_server

logger = logging.getLogger('aspy')
a = analytic_server("ga1.fyre.ibm.com",9080,False,"admin","test")
rs = a.create_pipeline().read_datasource("DRUG1N").select("lambda x: x.Age>30").derive("ratio","lambda x:x.Na/x.K").aggregate(["BP"],["count","mean_ratio"]).run()
for row in rs:
    print(str(row))



print(str(rs.toPandas()))