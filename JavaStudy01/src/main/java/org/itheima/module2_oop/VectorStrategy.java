package org.itheima.module2_oop;

public class VectorStrategy implements SearchStrategy {
    @Override
    public String search(String query) {
        return "向量查询中："+query;
    }
}
