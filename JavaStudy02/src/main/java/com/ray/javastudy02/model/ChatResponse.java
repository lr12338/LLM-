package com.ray.javastudy02.model;

import lombok.Data;
import lombok.AllArgsConstructor;
/**
 * 定义输出的参数格式
 */
@Data
@AllArgsConstructor // 自动生成全参数构造函数
public class ChatResponse {
    private String answer; // AI 回复
    private int tokenUsage;// 消耗 tokens
    private String status; // 状态 success/fail
}
