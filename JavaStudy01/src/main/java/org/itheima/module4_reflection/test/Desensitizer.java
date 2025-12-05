package org.itheima.module4_reflection.test;

import java.lang.reflect.Field;

/**
 * 作业：敏感字段脱敏工具
 * 在 AI 产品中，保护用户隐私（PII）至关重要。我们来做一个自动脱敏工具。
 * 任务要求：
 * 定义注解 @Sensitive，属性 strategy 默认为 "STAR" (用星号替换)。
 * 创建一个 UserQuery 类，包含属性：
 * username (普通字段)
 * phoneNumber (打上 @Sensitive 标签)
 * idCard (打上 @Sensitive 标签)
 * 编写一个工具类 Desensitizer，包含静态方法 public static void process(Object obj)。
 * 反射逻辑：
 * 获取 obj 的所有字段 (clazz.getDeclaredFields())。
 * 遍历字段，检查是否有 @Sensitive。
 * 如果有，强制设置该字段可访问 (field.setAccessible(true) -> 这是为了突破 private 限制)。
 * 读取原值，替换为 "***"，再写回字段 (field.set(obj, "***"))。
 * 在 main 方法中，创建一个 UserQuery 对象，填入真实数据，调用工具方法，然后打印对象，看手机号是否变成了 "***"。
 * 💡 提示: field.setAccessible(true) 是反射中最暴力的操作，它能无视 private 关键字。这也是为什么有时候大家说 Java 的封装是“防君子不防小人”。
 *
 * 注意：
 * 1.注解@@Target(ElementType.TYPE) TYPE 表示只能贴在类上； FIELD 表示能贴在字段上
 * 2.针对 field.set()必须在 try-catch 中运行 ，Java 有“受检异常 (Checked Exception)”机制。field.set() 抛出的异常属于这一类
 *
 */
public class Desensitizer {
    public static void process(Object obj) {

        // 获取obj所属类的所有字段
        Field[] fields = obj.getClass().getDeclaredFields();

        //
        for (Field field : fields) {
            //检查字段上是否有Sensitive注释
            if (field.isAnnotationPresent(Sensitive.class)) {
                try {
                    //1.暴力破解 private 权限
                    field.setAccessible(true);
                    //2.修改值 ，必须放在 try catch 中
                    //修改对象，修改值
                    field.set(obj, "***");
                } catch (IllegalAccessException e) {
                    //修改失败，打印错误信息
                    e.printStackTrace();
                }
            }
        }
    }


    public static void main(String[] args) {
        UserQuery userQuery = new UserQuery();
        userQuery.username= "aa";
        userQuery.phoneNumber = "123";
        userQuery.idCard = "222";

        System.out.println("修改前：" + userQuery);
        process(userQuery);
        System.out.println("修改后：" + userQuery);

    }
}
