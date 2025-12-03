package org.itheima.module1_syntax;

// implements 关键字表示：遵守 LLMProvider 的合同
public class OpenAIProvider implements LLMProvider {

    @Override
    public String generateResponse(String prompt){
        //模拟调用 OpenAI API
        return "[OpenAI GPT-4] 回复：" + prompt;
    }

    @Override
    public String getProviderName() {
        return "OpenAI GPT-4";
    }
}
