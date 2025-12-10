package com.ray.javastudy02.service;

import dev.langchain4j.service.SystemMessage;
import dev.langchain4j.service.spring.AiService;

/**
 * 声明式的 AI 服务接口
 * LangChain4j 会自动为它生成实现类，并注入配置好的 ChatModel。
 */
@AiService
public interface DeepSeekAiService {
    //简单对话接口
    String chat(String userMessage);

    // 带 System Prompt
    @SystemMessage("你是一名专业的 Java 助手，回答请简练并包含代码示例。")
    String chatWithSystem(String usermessage);
}
