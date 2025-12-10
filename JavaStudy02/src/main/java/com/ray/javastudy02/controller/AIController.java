package com.ray.javastudy02.controller;

import com.ray.javastudy02.model.ChatRequest;
import com.ray.javastudy02.model.ChatResponse ;
import com.ray.javastudy02.model.SummaryRequest;
import com.ray.javastudy02.model.SummaryResponse;
import com.ray.javastudy02.service.AIService;
import com.ray.javastudy02.service.LlmService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

//@RestController
//@RequestMapping("/api/ai") //统一访问路径
//public class AIController {
//
//    @Autowired
//    private AIService aiService;
//
//    @Autowired
//    private LlmService llmService;
//    //POST 常用于提交数据
//    //@RequestBody 告诉Spring 把前端传来的 JSON 自动转换成 Java对象 ChatRequest
//    @PostMapping("/chat")
//    public ChatResponse  chat(@RequestBody ChatRequest request){
//
//        //教研逻辑
//        if (request.getPrompt() == null || request.getPrompt().isEmpty()){
//            return new ChatResponse ("prompt 不能为空", 0, "failed");
//        }
//        return aiService.chat(request);
//
//    }
//
//    @PostMapping("/summary")
//    public SummaryResponse summary(@RequestBody SummaryRequest request){
//        if (request.getText() == null || request.getMaxlength() == 0){
//            return new SummaryResponse("参数有误", "failed");
//        }
//        return aiService.summary(request);
//    }
//
//}

@RestController
@RequestMapping("/api/real-ai")
@CrossOrigin(origins = "*")
public class AIController {

    @Autowired
    private LlmService llmService;

    @PostMapping("/chat")
    public ChatResponse chat(@RequestBody ChatRequest chatRequest){
        try{
            //1.调用真实大模型
            String answer = llmService.callAI(chatRequest.getPrompt());

            //2.返回结果
            return new ChatResponse(answer, 0, "success_real_api");
        }catch (Exception e){
            e.printStackTrace();
            return new ChatResponse("调用出错："+e.getMessage(),0, "error");
        }
    }

    @PostMapping(value = "/stream", produces = org.springframework.http.MediaType.TEXT_EVENT_STREAM_VALUE)
    public org.springframework.web.servlet.mvc.method.annotation.SseEmitter streamChat(@RequestBody ChatRequest request) {
        // 直接调用 Service 返回 emitter
        return llmService.streamAI(request.getPrompt());
        }

}
