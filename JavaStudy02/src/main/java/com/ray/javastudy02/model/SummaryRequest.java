package com.ray.javastudy02.model;

import lombok.Data;

@Data
public class SummaryRequest {
    private String text;
    private int maxlength;
}
