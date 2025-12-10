package com.ray.javastudy02.controller;

import com.ray.javastudy02.service.DeepSeekAiService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/chat")
public class ChatController {

    //注入 AI Service 接口
    private final DeepSeekAiService aiService;

    //构造器注入 （Spring 推荐方式） ？
    public ChatController(DeepSeekAiService aiService) {
        this.aiService = aiService;
    }

    @GetMapping("/simple")
    public String simpleChat(@RequestParam String question) {
        //一行代码调用，屏蔽 HTTP 的细节
        return aiService.chat(question);
    }

    @GetMapping("/expert")
    public String expertChat(@RequestParam String question) {
        return aiService.chatWithSystem(question);
    }

}
