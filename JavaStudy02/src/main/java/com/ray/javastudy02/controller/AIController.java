package com.ray.javastudy02.controller;

import com.ray.javastudy02.model.ChatRequest;
import com.ray.javastudy02.model.ChatResopnse;
import com.ray.javastudy02.service.AIService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/ai") //统一访问路径
public class AIController {

    @Autowired
    private AIService aiService;
    //POST 常用于提交数据
    //@RequestBody 告诉Spring 把前端传来的 JSON 自动转换成 Java对象 ChatRequest
    @PostMapping("/chat")
    public ChatResopnse chat(@RequestBody ChatRequest request){

        //教研逻辑
        if (request.getPrompt() == null || request.getPrompt().isEmpty()){
            return new ChatResopnse("prompt 不能为空", 0, "failed");
        }
        return aiService.chat(request);

    }

}
