package com.ray.javastudy02.service;

import com.ray.javastudy02.model.ChatRequest;
import com.ray.javastudy02.model.ChatResponse ;
import com.ray.javastudy02.model.SummaryRequest;
import com.ray.javastudy02.model.SummaryResponse;

public interface AIService {
    ChatResponse chat(ChatRequest request);
    SummaryResponse summary(SummaryRequest text);
}
