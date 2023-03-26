from pyspark import SparkContext
import os
JAVA_HOME = '/root/bigdata/jdk'
os.environ['JAVA_HOME'] = JAVA_HOME

PYSPARK_PYTHON = "/miniconda2/envs/py365/bin/python"
os.environ['PYSPARK_PYTHON'] = PYSPARK_PYTHON
os.environ['PYSPARK_DRIVER_PYTHON'] = PYSPARK_PYTHON

if __name__ == '__main__':
    # 创建sparkcontext参数1 spark集群的master地址参数2应用的名字
    sc = SparkContext('local', 'pvcount')
    rdd1 = sc.textFile('file:///root/tmp/access.log')
    rdd2 = rdd1.map(lambda x:('pv', 1)).reduceByKey(lambda a, b: a + b)
    print(rdd2.collect())

    pass
