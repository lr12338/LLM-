package org.itheima.module4_reflection;

import java.lang.reflect.Method;

public class FrameworkDemo {
    public static void main(String[] args) {
        //模拟：在配置文件只配置了类名（字符串），常见于 插件化结构中
        String[] clasNames = {
                "org.itheima.module4_reflection.GPT4",
                "org.itheima.module4_reflection.DEEPSEEK"
        };

        System.out.println("---扫描AI框架---");

        for (String className : clasNames) {
            try{
                //1.反射核心:根据字符串加载类 Class对象；此时JVM才知道有这个类存在
                Class<?> clazz = Class.forName(className);

                //2.检查类是否贴了ModelConfig标签
                if(clazz.isAnnotationPresent(ModelConfig.class)){

                    //3.读取标签内容
                    ModelConfig config = clazz.getAnnotation(ModelConfig.class);
                    System.out.println("发现模型："+config.name());
                    System.out.println("价格："+ config.price());
                    System.out.println("合规性："+ config.isSafe());

                    //4.高级反射：动态创建对象并执行方法,类似于 new GPT4()
                    // getDeclaredConstructor() → 获取类的「无参构造方法」（必须有，否则报错）
                    // newInstance() → 用无参构造创建对象（返回Object类型，因为不知道具体是哪个类）
                    Object instance = clazz.getDeclaredConstructor().newInstance();

                    //相当于 instance.run(), 假设所有模型都有run()方法
                    // getMethod("run") → 获取类的「public无参run()方法」（必须有，否则报错）
                    // runMethod.invoke(instance) → 让创建的对象（instance）执行run()方法
                    Method runMethod = clazz.getMethod("run");
                    runMethod.invoke(instance);

                    System.out.println("------------");
                }
            } catch (Exception e){
                e.printStackTrace();
            }
        }
    }
}
