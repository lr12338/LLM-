package com.ray.javastudy02.service;

import com.ray.javastudy02.model.ChatRequest;
import com.ray.javastudy02.model.ChatResopnse;


public interface AIService {
    ChatResopnse chat(ChatRequest request);
}
