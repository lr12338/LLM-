package com.ray.javastudy02.controller;

import com.ray.javastudy02.model.ChatRequest;
import com.ray.javastudy02.model.ChatResponse ;
import com.ray.javastudy02.model.SummaryRequest;
import com.ray.javastudy02.model.SummaryResponse;
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
    public ChatResponse  chat(@RequestBody ChatRequest request){

        //教研逻辑
        if (request.getPrompt() == null || request.getPrompt().isEmpty()){
            return new ChatResponse ("prompt 不能为空", 0, "failed");
        }
        return aiService.chat(request);

    }

    @PostMapping("/summary")
    public SummaryResponse summary(@RequestBody SummaryRequest request){
        if (request.getText() == null || request.getMaxlength() == 0){
            return new SummaryResponse("参数有误", "failed");
        }
        return aiService.summary(request);
    }

}
