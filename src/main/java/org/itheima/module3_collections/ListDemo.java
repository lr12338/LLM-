package org.itheima.module3_collections;

/**
 * 1.java 的 集合框架
     * List 列表：对应 python 的list。有序，可重复。
     * Map 映射：对应python德dict 字典。键值对，Key唯一。
 * 2.Java 泛型：<DataType> 规定容器中只能装什么
     * List<String>:只能装字符串
     * List<AIModel>：只能装定义的AIModel 对象
     * List<Integer> 整数类型
 * 3.ArrayList : 动态数组
 */
import java.util.ArrayList;
import java.util.List;

public class ListDemo {
    public static void main(String[] args) {
        //1.创建一个List
        //左边：List（接口）-> 为了解耦
        //右边：ArrayList(实现类）-> 具体的底层逻辑
        //<String>: 泛型，规定只能存放 字符串
        List<String> history = new ArrayList<>();

        //2.增(Add)
        history.add("user：你好");
        history.add("bot:你好，有问题欢迎询问！");
        history.add("user:你是谁");

        //3.查（Get）- 索引从0开始 get(0)
        String text = history.get(0);
        System.out.println("第一条信息："+text);

        //4.获取长度（SIZE）.size - python len
        int len = history.size();
        System.out.println("历史会话长度"+len);

        //5.遍历 loop - for-each 循环
        System.out.println("完整对话：");
//        for (int i = 0; i < len; i++) {
//            System.out.println(history.get(i));
//        }
        for(String msg : history){
            System.out.println(msg);
        }
    }
}
