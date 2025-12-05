package org.itheima.consultant.controller;

import dev.langchain4j.model.openai.OpenAiChatModel;
import org.itheima.consultant.aiservice.ConsultantService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Flux;

//贴在类上
@RestController
//定义 类 public 关键修饰符 ：表示公开的，其他包的类可以访问这个类
public class ChatController {

    @Autowired
    //ConsultantService 是一个接口（定义的 public interface ConsultantService），
    // 而 consultantService 是这个接口类型的 “引用变量”—— 就像一个 “容器”，用来存放实现了该接口的对象。
    private ConsultantService consultantService;

    @RequestMapping(value = "/chat",produces = "text/html;charset=utf-8")
    //返回值Flux<String>：这是 Reactor 响应式编程库中的类型，表示异步流式返回的字符串序列。
    // 用途：适合处理 "实时生成、分段返回" 的场景（比如 AI 生成回复时，边生成边返回给前端，不用等全部生成完）
    //public Flux<String> chat(String message)表示一个可被其他调用的公共方法chat，处理输入的 string类型的messgge，返回Flux<String>类型的 result
    // Flux<String> result = consultantService.chat(message);表示 使用接口ConsultantService中定义的chat方法（有AiService来实现），在这里通过consultantService.chat来调用，输入message，返回Flux<String>的result。
    //错误理解：且 这里使用的  consultantService表示基于ConsultService定义的私有的，仅在本类中可以被使用的接口 ，名称是自定义的，也可以是private ConsultantService getService的格式，后续通过 Flux<String> answer = getService.chat(message)来实现
    // 这里使用的 consultantService 表示用接口类型ConsultService定义的变量，参考String message；consultantService 变量能调用接口中定义的方法（如chat()），但这些方法的具体实现来自于它所指向的 “实现类对象”，而不是接口本身，
    public Flux<String> chat(String memoryId, String message){
        Flux<String> result = consultantService.chat(memoryId, message);
        return result;
    }

//    @RequestMapping("/chat")
//    public String chat(String message){
//        String result = consultantService.chat(message);
//        return result;
//    }

    //直接调用OpenAiChatModel
      //贴在方法上。自动注入
//    @Autowired
//    private OpenAiChatModel model;
//
//    @RequestMapping("/chat")
      //方法（Method):类的 功能/动作，实现具体逻辑
      // public：修饰符，表示方法可以被外部调用；
      // String：返回类型表示方法执行后返回一个字符串
      // chat: 方法名，“驼峰命名法”（首字母小写，后面单词首字母大写）
      // String message： 参数列表，表示方法需要接受的数据，格式：类型+变量名，多个参数用逗号分隔
//    public String chat(String message){//浏览器传递的问题
//        String result = model.chat(message);
//        return result;
//    }


}
