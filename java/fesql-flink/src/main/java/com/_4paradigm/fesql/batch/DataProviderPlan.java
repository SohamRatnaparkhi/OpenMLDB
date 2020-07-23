package com._4paradigm.fesql.batch;

import com._4paradigm.fesql.common.FesqlPlanContext;
import com._4paradigm.fesql.vm.PhysicalDataProviderNode;
import org.apache.flink.table.api.Table;

public class DataProviderPlan {

    public static Table gen(FesqlPlanContext planContext, PhysicalDataProviderNode dataProviderNode) {
        String tableName = dataProviderNode.GetName();
        String sqlText = "select * from " + tableName;
        return planContext.getBatchTableEnvironment().sqlQuery(sqlText);
    }

}
