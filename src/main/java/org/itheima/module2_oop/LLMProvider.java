package org.itheima.module2_oop;


//接口：只定义“要做什么”，不定义“怎么做”
public interface LLMProvider {
    // 接口里的方法默认是 public abstract
    String generateResponse(String prompt);

    String getProviderName();
}
