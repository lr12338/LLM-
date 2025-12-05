package com.ray.javastudy02.model;

/**
 * 定义输入参数
 */
import lombok.Data;

@Data // Lombok自动生成 Getter/Setter/Tostring
public class ChatRequest {
    private String model;
    private String prompt;
    private String temperature;
}
