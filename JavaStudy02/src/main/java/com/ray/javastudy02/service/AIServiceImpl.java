package com.ray.javastudy02.service;

import com.ray.javastudy02.model.ChatResopnse;
import com.ray.javastudy02.model.ChatRequest;
import org.springframework.stereotype.Service;

//重点： @Service 注解 ：告诉Spring是 干活的厨师，放在容器里直接管理
@Service
public class AIServiceImpl implements AIService {

    @Override
    public ChatResopnse chat(ChatRequest request) {
        System.out.println("收到请求，模型：" + request.getModel() + "\nprompt:" + request.getPrompt() + "\ntemperature:" + request.getTemperature());
        System.out.println("模型思考中...");
        String answer = "这是来自 请求：" + request.getPrompt() + "的回复\n" + "你好，我是AI";
        int tokens = answer.length() + request.getPrompt().length();

        return new ChatResopnse(answer,tokens,"success");

    }
}
