package org.itheima.module1_syntax;

import java.util.Scanner;
/**
 * AI Java实战学习-基于Googel AI Studio
 */
/* java面向对象 ，程序基本单位是 class， class 为关键字，此处定义 Main */
// public 表示这个类是公开的，其他地方可以用；
// class：定义类等关键字；
// MainTest：类名，（必须大写开头，驼峰命名，文件名必须相同）；
public class MainTest {
    // Java入口程序规定的方法必须是 static 静态方法，方法名必须为 main，括号内的参数必须是String数组
    // 固定使用static void ，作为程序入口
    public static void main01(String[] args) {
        System.out.println("程序启动中...");
        // 定义常量  （final 定义规范：全大写字母 + 下划线分隔）
        final double GPT4_INPUT_PRICE = 0.03;

        // 定义变量
        int inputTokens = 500;//整数,必须声明，强类型
        int outputTokens = 200;

        // 字符串 （String 数引用类型，首字母大写，不是基本类型）
        String modelName = "GPT-4";

        System.out.println("当前模型"+modelName);

        String prompt = "请帮我写一个程序：";
        String input = "用户：" + prompt;//java 常用 + 拼接或 String.format,python用 f"输出{变量}"
        System.out.println(input);

        //流程控制：python 用缩进；java 用 {}
        if (inputTokens < 1111){
            System.out.println("true");
        } else {
            System.out.println("false");
        }
        //Loop 循环：
        for (int i=0; i<5; i++){
            System.out.println("重试"+i+"次");
        }
    }
    public static void main02(String[] args) {
        //1.准备工具：Scanner用于读取控制台输入
        Scanner scanner = new Scanner(System.in);

        //2.定义模型单价 final
        final double PRICE_INPUT_2K = 0.02;
        final double PRICE_OUTPUT_2K = 0.05;
        final double USD_TO_CNY_RATE = 7;

        final double PRICE_INPUT_2K_GPT3 = 0.01;
        final double PRICE_OUTPUT_2K_GPT3 = 0.03;



        System.out.println("---模型价格计算器---\n价格标准：\n"+ "输入价格（/1k tokens）：" + PRICE_INPUT_2K + "\n输出价格（/1k tokens）：" + PRICE_OUTPUT_2K);

        //3.接收用户输入 配置参数：模型名称，输入数量，输出数
        System.out.println("请输入模型名称：\n");
        String modelName = scanner.next(); // 接收字符串

        System.out.println("输入tokens数：\n");
        double inputTokens = scanner.nextInt(); // 接收整数

        System.out.println("输出tokens数：\n");
        int outputTokens = scanner.nextInt();

        //4.业务逻辑计算 计算价格
        //公式：（tokens数 /1000）* price
        double totalPrice = 0.0;//必须在外部定义
        if (modelName.equals("GPT4")){
            double inputPrice = (inputTokens / 1000.0) * PRICE_INPUT_2K * USD_TO_CNY_RATE; //1000.0 运算都是同一类型
            double outputPrice = (outputTokens / 1000.0) * PRICE_OUTPUT_2K * USD_TO_CNY_RATE;
            totalPrice = inputPrice + outputPrice;//double totalPrice = inputPrice + outputPrice;如果在此定义，则为局部变量
        }else if (modelName.equals("GPT3")){
            double inputPrice = (inputTokens / 1000.0) * PRICE_INPUT_2K_GPT3  * USD_TO_CNY_RATE; //1000.0 运算都是同一类型
            double outputPrice = (outputTokens / 1000.0) * PRICE_OUTPUT_2K_GPT3  * USD_TO_CNY_RATE;
            totalPrice = inputPrice + outputPrice;
        }

        //5.逻辑判断 判断是否超过临界点
        boolean isExpense = totalPrice > 1.0;//定义布尔数来判断是否超过值
        //6.格式化输出结果
        System.out.println("---计算结果---\n" + "使用模型：" + modelName + "\n");

        System.out.printf("总成本（CNY）：¥%.1f \n" ,totalPrice);//专门支持格式化System.out.printf(" %.1f",num)

        if (isExpense){
            System.out.println("成本较贵");
        } else {
            System.out.println("成本可控");
        }

        //关闭资源
        scanner.close();

    }
    public static void main(String[] args) {
        AIModel gpt = new AIModel("GPT-4",2.0);
        gpt.describe();
        gpt.setTemperature(3.0);
        gpt.describe();
    }
}
