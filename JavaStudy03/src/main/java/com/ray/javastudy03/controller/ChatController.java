package com.ray.javastudy03.controller;

import com.ray.javastudy03.service.DeepSeekAiService;
import dev.langchain4j.service.UserMessage;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/chat")
public class ChatController {

//    @Autowired // 字段注入
//    private DeepSeekAiService aiService;

    //注入 AI Service 接口
    private final DeepSeekAiService aiService;

    //构造器注入 （Spring 推荐方式） ？：Spring 创建 Controller 时，自动把 AI 服务（aiService）传进去，推荐用是因为安全、能早发现问题
    //相比较 字段注入 ，避免 “工具缺失”，代码更安全，不用写 @Autowired
    public ChatController(DeepSeekAiService aiService) {
        this.aiService = aiService;
    }

    @GetMapping("/simple")
    //@RequestParam：把 URL 里的参数（比如 question、userId）和 Controller 方法的参数绑定起来，让 Controller 能拿到前端传的问题
    // /http://localhost:8080/api/chat/expert?question= 你是谁？
    public String simpleChat(@RequestParam String userId, @UserMessage String question) {
        //一行代码调用，屏蔽 HTTP 的细节
        return aiService.chat(userId, question);
    }

    @GetMapping("/expert")
    public String expertChat(@RequestParam String userId, @UserMessage String question) {
        return aiService.chatWithSystem(userId, question);
    }
    
    @GetMapping("/conversation")
    public String chatWithMemory(@RequestParam String userId, @UserMessage String question) {
        return aiService.chatWithSystem(userId, question);
    }

}
