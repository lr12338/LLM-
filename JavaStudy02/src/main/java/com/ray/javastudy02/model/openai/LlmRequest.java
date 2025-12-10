package com.ray.javastudy02.model.openai;

import lombok.Builder;
import lombok.Data;

import java.util.List;

//(发送给 API 的请求体)
@Data
@Builder// 建造者模式，方便链式调用
public class LlmRequest {
    private String model;
    private List<Message> messages;
    private boolean stream;
    private Double temperature;
}
