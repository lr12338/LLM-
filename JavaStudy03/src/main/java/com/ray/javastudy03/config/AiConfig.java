package com.ray.javastudy03.config;

import dev.langchain4j.store.memory.chat.ChatMemoryStore;
import dev.langchain4j.store.memory.chat.redis.RedisChatMemoryStore;
import dev.langchain4j.memory.chat.MessageWindowChatMemory;
import dev.langchain4j.memory.chat.ChatMemoryProvider;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class AiConfig
{
    /**
     * 1.配置存储介质： Redis
     * host port
     */
    @Bean
    public ChatMemoryStore chatMemoryStore(){
        return RedisChatMemoryStore.builder()
                .host("localhost")
                .port(6379)
                .build();
    }

    /**
     * 2.配置记忆策略： Provider
     * 当 AI 服务需要记忆时，调用该 Bean
     */
    @Bean
    public ChatMemoryProvider chatMemoryProvider(ChatMemoryStore chatMemoryStore){
        return memoryID -> MessageWindowChatMemory.builder()
                .id(memoryID) // 记忆的唯一标识
                .maxMessages(10) // 核心策略：只保留最近10条消息
                .chatMemoryStore(chatMemoryStore) // 绑定上述创建的 redis 存储介质
                .build();
    }
}
