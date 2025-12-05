package org.itheima.module2_oop;

import java.util.Scanner;

public class RAGSystem {
    public String process(SearchStrategy strategy, String query) {
        return strategy.search(query);
    }

    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        RAGSystem ragSystem = new RAGSystem();
        SearchStrategy strategy;

        System.out.println("输入查询词");
        String query = scanner.next();
        System.out.println("是否为vip");
        String isVip = scanner.next();

        if(isVip.equals("vip")){
            strategy = new VectorStrategy();
//            String result = ragSystem.process(strategy, query);
//            System.out.println(result);
        } else {
            strategy = new KeywordStrategy();
//            String result = ragSystem.process(strategy, query);
//            System.out.println(result);
        }
        String result = ragSystem.process(strategy, query);
        System.out.println(result);
    }
}

