package org.itheima.module4_reflection;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * @Annotation 元 注解
 */

// 元注解1: 声明标签贴在哪里 （TYPE 表示贴在类上 class,METHOD 表示贴在方法上
@Target(ElementType.TYPE)
//元注解 2:标签存活多久？ RUNTIME 表示在程序运行时可以通过反射读取
//重要！ 若不写，运行后标签无法识别
@Retention(RetentionPolicy.RUNTIME)
public @interface ModelConfig {
    // 定义标签里的属性（看起来像方法，其实是属性）
    String name();
    double price() default 0.01;//默认值
    boolean isSafe() default true;

}
