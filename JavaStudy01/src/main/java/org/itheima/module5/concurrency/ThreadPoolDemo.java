package org.itheima.module5.concurrency;

/**
 * 模拟并发推理服务
 */

import javax.sound.midi.SysexMessage;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class ThreadPoolDemo {
    public static void main(String[] args) {
        System.out.println("--- AI推理中 ---");

        //1.创建一个固定大小的进程池 ，只有3个worker，只能同时处理3个并发请求
        ExecutorService threadPool = Executors.newFixedThreadPool(3);

        //2.模拟多个用户发来请求，10
        for (int i = 0; i < 10; i++) {
            final int taskId = i;

            //提交任务给进程池
            //execute() 接收一个 Runnable 对象
            threadPool.execute(() -> {
                System.out.println("任务" + taskId + " 正在处理...    [线程：" + Thread.currentThread().getName() + "]");
                try {
                    Thread.sleep(2000);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
                System.out.println("任务" +  taskId + "完成");
            });
        }
        //关闭进程池
        threadPool.shutdown();

    }
}
