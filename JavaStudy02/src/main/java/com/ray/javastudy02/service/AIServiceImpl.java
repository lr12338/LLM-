package com.ray.javastudy02.service;

import com.ray.javastudy02.mapper.PromptLogMapper;
import com.ray.javastudy02.model.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.time.LocalDateTime;
import java.util.concurrent.TimeUnit;

import org.springframework.data.redis.core.StringRedisTemplate;

//重点： @Service 注解 ：告诉Spring是 干活的厨师，放在容器里直接管理
@Service
public class AIServiceImpl implements AIService {

    // 注入 Mapper
    @Autowired
    private PromptLogMapper promptLogMapper;

    // 注入 Redis 工具类
    @Autowired
    private StringRedisTemplate redisTemplate;

        //1.构造缓存key
        //2.缓存查询逻辑
        //3.缓存未命中，执行真实业务，AI业务
        //4.写入数据库
        //5.写入Redis缓存
        @Override
        public ChatResponse chat(ChatRequest request) {
            // 1. 构造缓存 Key (架构师习惯：加前缀防止冲突，比如 "cache:model:prompt")
            // 这里的 Key 是由 "模型名:用户问题" 组成的，确保唯一性
            String cacheKey = "ai_cache:" + request.getModel() + ":" + request.getPrompt();
//            String Key = request.getModel() + ":" + request.getPrompt();

            // 2. --- 缓存查询逻辑 ---
            // Boolean.TRUE.equals 是为了防止 null 指针异常
            if (Boolean.TRUE.equals(redisTemplate.hasKey(cacheKey))) {
                System.out.println("⚡⚡⚡ 命中 Redis 缓存！直接返回结果");
                // 从 Redis 获取值
                String cachedAnswer = redisTemplate.opsForValue().get(cacheKey);
                // 构造返回结果 (Token数这里暂时模拟为0或者从缓存里取，为了简化先设为0)
                return new ChatResponse(cachedAnswer, 0, "success_from_cache");
            }

            // 3. --- 缓存未命中，执行真实业务 (模拟调用 AI) ---
            System.out.println("🐢 缓存未命中，正在调用大模型...");
            // 模拟 AI 推理耗时 (比如睡 2 秒)
            try { Thread.sleep(2000); } catch (InterruptedException e) {}

            String answer = "来自 " + request.getModel() + " 的新回复: " + request.getPrompt();
            int tokens = request.getPrompt().length() + answer.length();

            // 4. --- 写入数据库 (持久化) ---
            PromptLog log = new PromptLog();
            log.setModel(request.getModel());
            log.setUserInput(request.getPrompt());
            log.setAiResponse(answer);
            log.setTokenUsage(tokens);
            log.setCreateTime(LocalDateTime.now());
            promptLogMapper.insert(log);

            // 5. --- 写入 Redis 缓存 (关键步骤) ---
            // opsForValue().set(Key, Value, Time, Unit)
            // 设置 10 分钟过期。过期后 Redis 会自动删除，释放内存。
            redisTemplate.opsForValue().set(cacheKey, answer, 10, TimeUnit.MINUTES);

            return new ChatResponse(answer, tokens, "success_new");
        }


//    @Override
//    public ChatResponse chat(ChatRequest request) {
//        //1.AI业务逻辑
//        System.out.println("收到请求，模型：" + request.getModel() + "\nprompt:" + request.getPrompt() + "\ntemperature:" + request.getTemperature());
//        System.out.println("模型思考中...");
//        String answer = "这是来自 请求：" + request.getPrompt() + "的回复\n" + "你好，我是AI";
//        int tokens = answer.length() + request.getPrompt().length();
//
//        //2. ---新增逻辑：数据持久化---
//        PromptLog log = new PromptLog();
//        log.setModel(request.getModel());
//        log.setUserInput(request.getPrompt());
//        log.setAiResponse(answer);
//        log.setTokenUsage(tokens);
//        log.setCreateTime(LocalDateTime.now());
//        //数据插入数据库
//        promptLogMapper.insert(log);
//
//        System.out.println("日志已保存：" + log.getId());
//
//        //3，返回结果
//        return new ChatResponse(answer,tokens,"success");
//
//    }

    @Override
    public SummaryResponse summary(SummaryRequest request) {
        System.out.println("收到请求，针对文本："+ request.getText() + " 总结摘要，字数限制" + request.getMaxlength());
        System.out.println("模型思考中...");
        String content = request.getText().substring(0,request.getMaxlength()) +"...";

        return new SummaryResponse(content, "success");

    }
}
