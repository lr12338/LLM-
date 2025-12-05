package org.itheima.module5.concurrency.test;

/**
 * 作业：简单的异步 AI 任务编排
 * 场景: 用户输入一个 Prompt，我们需要同时做三件事：
 * 调用 敏感词检测服务 (模拟耗时 0.5s，返回 true/false)。
 * 调用 Embedding 向量化服务 (模拟耗时 1s，返回 String)。
 * 调用 主模型生成服务 (模拟耗时 2s，返回 String)。
 * 要求:
 * 使用 CompletableFuture 并行执行这三个任务。
 * 核心逻辑:
 * 如果“敏感词检测”返回 false (发现敏感词)，则不管其他两个任务完成没，直接在主线程输出 "❌ 内容违规，请求拦截"。
 * 如果检测通过，且所有任务都完成，输出 "✅ 结果: [向量: xxx] [回复: xxx]"。
 * 你需要查阅资料（或问我），了解如何处理 CompletableFuture 的组合逻辑。
 */

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;

public class ThreadLLM {

    public static void threadLLM(String prompt) throws ExecutionException, InterruptedException {
        CompletableFuture<Boolean> wordTask = CompletableFuture.supplyAsync(() -> {
            sleep(500);//封装一个sleep方法
            if (prompt.contains("敏感词")) {
                System.out.println("⚠️ [敏感词服务] 发现违规内容!");
                return false;
            } else {
                System.out.println("✅ [敏感词服务] 检测通过");
                return true;
            }});

        CompletableFuture<String> embeddingTask = CompletableFuture.supplyAsync(() -> {
            sleep(1000);
            System.out.println("✅ [Embedding] 向量化完成");
            return "向量化结果";});

        CompletableFuture<String> generateTask = CompletableFuture.supplyAsync(() -> {
            sleep(2000);
            System.out.println("✅ [LLM] 生成完成");
            return "模型回复结果";});

        //核心编排
        //方案A：简单通用，等待所有任务结束再分析
        CompletableFuture<Void> allTasks = CompletableFuture.allOf(wordTask,embeddingTask,generateTask);

        try{
            //阻塞主线程
            allTasks.join();
            Boolean result = wordTask.get();
            if(result){
                String bed =  embeddingTask.get();
                String llm = generateTask.get();
                System.out.println("输出结果，向量化 llm" +bed +llm);
            } else {System.out.println("检测异常");}
            //获取结果
        } catch (InterruptedException | ExecutionException e) {
            e.printStackTrace();
        }
        }
    // 辅助工具方法：让代码不被 try-catch 淹没
    private static void sleep(long millis) {
        try {
            Thread.sleep(millis);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }
    public static void main(String[] args) throws InterruptedException, ExecutionException {
        String prompt = "敏感词";
        threadLLM(prompt);
//        System.out.println(result);
    }
    }


