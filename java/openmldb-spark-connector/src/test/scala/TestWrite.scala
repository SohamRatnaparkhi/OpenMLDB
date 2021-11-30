/*
 * Copyright 2021 4Paradigm
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import com._4paradigm.openmldb.sdk.SdkOption
import com._4paradigm.openmldb.sdk.impl.SqlClusterExecutor
import org.apache.spark.sql.SparkSession
import org.scalatest.FunSuite

import java.lang.Thread.currentThread

class TestWrite extends FunSuite {

  test("Test write a local file to openmldb") {
    val sess = SparkSession.builder().master("local[*]").getOrCreate()
    val readFilePath = currentThread.getContextClassLoader.getResource("test.csv")
    val df = sess.read.option("header", "true")
      // spark timestampFormat is DateTime, so in test.csv, the value of c9 can't be long int.
      .schema("c1 boolean, c2 smallint, c3 int, c4 bigint, c5 float, c6 double,c7 string, c8 date, c9 timestamp, " +
        "c10_str string")
      .csv(readFilePath.toString)
    df.show()

    val zkCluster = "127.0.0.1:6181"
    val zkPath = "/onebox"
    val db = "db"
    val table = "spark_write_test"
    val options = Map("db" -> db, "table" -> table, "zkCluster" -> zkCluster, "zkPath" -> zkPath)

    // create db.t1 for saving, openmldb table column type accepts bool, not boolean
    val option = new SdkOption
    option.setZkCluster(zkCluster)
    option.setZkPath(zkPath)
    val executor = new SqlClusterExecutor(option)
    executor.createDB(db)
    executor.executeDDL(db, "create table " + table + "(c1 bool, c2 smallint, c3 int, c4 bigint, c5 float, c6 double," +
      "c7 string, c8 date, c9 timestamp, c10_str string);")

    // batch write can't use ErrorIfExists
    df.write
      //      .format("com._4paradigm.openmldb.spark.OpenmldbSource")
      .format("openmldb")
      .options(options).mode("append").save()
  }
}
