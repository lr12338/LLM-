package com.ray.javastudy02.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

//@RestController = @Controller + @ResponseBody
//告诉 Spring： 这是一个处理 HTTP 请求的类，返回数据为 JSON
@RestController
public class HelloController {
    // 对应HTTP GET 请求 ,路径上 /hello
    // 类似 Python FaseAPI 中的  @app.get("/hello")
    @GetMapping("/hello")
    public String sayHello() {
        return "Hello World!";
    }
}
