package org.itheima.module2_oop;

public class KeywordStrategy implements SearchStrategy {
    @Override
    public String search(String query) {
        return "关键词查询:"+query;
    }

}
