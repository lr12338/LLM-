package org.itheima.module5.concurrency;

/**
 * Future 与 异步编程 ：并行处理多个任务
 */

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;

public class AsynDemo {
    public static void main(String[] args) throws ExecutionException, InterruptedException {
        long start = System.currentTimeMillis();
        //任务1:模拟调用大模型推理
        CompletableFuture<String> llmTask = CompletableFuture.supplyAsync(() -> {
            try {
                Thread.sleep(5000);
            } catch (InterruptedException e) {}
            return "LLM 推理结果：";
        });

        //任务2:模拟查询数据库
        CompletableFuture<String> dbTask = CompletableFuture.supplyAsync(() -> {
            try {
                Thread.sleep(2000);
            } catch (InterruptedException e) {}
            return "数据库查询结果：";
        });

        System.out.println("所有任务已异步提交");

        //等待所有任务都完成
        CompletableFuture.allOf(llmTask,dbTask).join();

        //获取结果
        String llmResult = llmTask.get();
        String dbResult = dbTask.get();

        long end = System.currentTimeMillis();

        System.out.println("总计时间：" +  (end - start) + "ms");
        System.out.println("LLM推理"+ llmResult);
        System.out.println("数据库查询" + dbResult);
    }
}
