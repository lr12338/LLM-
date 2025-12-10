package com.ray.javastudy03.service;

import dev.langchain4j.service.MemoryId;
import dev.langchain4j.service.SystemMessage;
import dev.langchain4j.service.UserMessage;
import dev.langchain4j.service.spring.AiService;

/**
 * 声明式的 AI 服务接口
 * LangChain4j 会自动为它生成实现类，并注入配置好的 ChatModel。
 */
@AiService
public interface DeepSeekAiService {
    /**
     * @MemoryID 标记这个参数是用于查找记忆的 Key
     * @UserMessage： 标记该参数是用户的实际提问
     */
    //简单对话接口
    String chat(@MemoryId String userId, @UserMessage String userMessage);

    // 带 System Prompt
    @SystemMessage("你是一名专业的 Java 助手，回答请简练并包含代码示例。")
    String chatWithSystem(@MemoryId String userId, @UserMessage String usermessage);
}
