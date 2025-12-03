package org.itheima.module1_syntax;

import java.util.Scanner;

public class ModelRouter {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);

        System.out.println("请选择模型服务商：1。 OpenAI  2. Deepseek");
        int choice = scanner.nextInt();

        //定义接口变量 provider
        LLMProvider provider;
        //实际对象都支持
        if (choice == 1) {
            provider = new OpenAIProvider();
        } else {
            provider = new DeepSeekProvider();
        }
        //
        System.out.println("已连接"+provider.getProviderName());
        String result = provider.generateResponse("请介绍你自己");
        System.out.println(result);
    }
}
