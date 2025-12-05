package org.itheima.module5.concurrency;

/**
 * 线程安全 (Thread Safety)：并发的噩梦
 * 当多个线程同时修改同一个变量时，如果不加保护，数据会错乱。这叫“线程不安全”。
 * 解决方案:
 * synchronized (锁): 笨重，但安全。
 * Atomic 类 (CAS): 轻量级，性能好。
 * 🏗️ 架构铺垫 (For Spring)
 * Spring 的 Controller 默认是单例 (Singleton) 的。这意味着所有用户的请求用的都是同一个 Controller 对象。
 * 千万不要在 Controller 里定义普通的成员变量用来存用户数据！ 否则 A 用户的请求可能会读到 B 用户的数据。这就是著名的“Spring 单例线程安全问题”。
 */

import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicInteger;

public class AtomicTest {
    //static in count = 0 ,普通int在多线程下不安全
    //使用原子类，底层利用CPU指令保证线程安全
    static AtomicInteger atomicCount = new AtomicInteger(0);

    public static void main(String[] args) throws InterruptedException {
        int userCount = 1000;
        ExecutorService pool = Executors.newFixedThreadPool(20);

        //倒计时锁 用来让主线程等待所有子线程结束
        CountDownLatch latch = new CountDownLatch(userCount);

        for (int i = 0; i < userCount; i++) {
            pool.execute(() -> {
                //模拟点赞逻辑 count++ 这种写法在并发下会丢失数据
                atomicCount.incrementAndGet();//原子➕1
                latch.countDown();//任务完成，倒计时假1

            });
        }
        //主线程阻塞在这，直至倒计时为0
        latch.await();

        System.out.println("预期点赞数量：" + userCount);
        System.out.println("实际点赞数量：" +  atomicCount.get());

        pool.shutdown();
    }

}
