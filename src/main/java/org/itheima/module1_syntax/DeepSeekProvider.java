package org.itheima.module1_syntax;

import org.itheima.module2_oop.LLMProvider;

public class DeepSeekProvider implements LLMProvider {

    @Override
    public String generateResponse(String prompt) {
        return "Deepseek R1 回复：" + prompt;
    }

    @Override
    public String getProviderName() {
        return "Deepseek R1";
    }


}
