package org.itheima.consultant.aiservice;

import dev.langchain4j.service.MemoryId;
import dev.langchain4j.service.SystemMessage;
import dev.langchain4j.service.UserMessage;
import dev.langchain4j.service.V;
import dev.langchain4j.service.spring.AiService;
import dev.langchain4j.service.spring.AiServiceWiringMode;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;

//Aiservice 声明式使用
@AiService(
        wiringMode = AiServiceWiringMode.EXPLICIT,//手动装配
        chatModel = "openAiChatModel",//指定模型
        streamingChatModel = "openAiStreamingChatModel",
        //chatMemory = "chatMemory"//配置会话记忆对象
        chatMemoryProvider = "chatMemoryProvider",//配置会话记忆提供者对象
        contentRetriever = "contentRetriever"//配置向量数据库检索对象

)
//可直接使用
//@AiService

//接口（interface）：代码的 规范/协议。 只声明方法

//使用方式：
//@Autowired
//private ConsultantService consultantService;

//ConsultantService 是 “接口”（只有方法声明，没有实现），consultantService 是接口类型的变量，它必须指向一个 “实现了ConsultantService接口的类的对象”（比如框架自动生成的实现类对象），
// consultantService.chat()调用的是这个实现类写好的逻辑（比如上述已通过@AiService声明调用 OpenAI 的逻辑）。
public interface  ConsultantService {

    //public String chat(String message);

    //@SystemMessage("你是东哥的助手小月月，人美心善又多金！")//系统注解
    @SystemMessage(fromResource = "system.txt")

    //@UserMessage("你是东哥的助手小月月，人美心善又多金！{{it}}")
//    @UserMessage("你是东哥的助手小月月，人美心善又多金！{{msg}}")
//    public Flux<String> chat(@V("msg")String message);

    //规定了 “处理聊天消息” 必须有一个方法，名叫chat，接收用户消息（String message），返回流式的 AI 回复（Flux<String>）
    public Flux<String> chat(@MemoryId String memoryId, @UserMessage String message);

}
