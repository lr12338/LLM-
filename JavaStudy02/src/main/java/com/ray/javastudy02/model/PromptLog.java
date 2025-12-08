package com.ray.javastudy02.model;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.baomidou.mybatisplus.annotation.IdType;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("prompt_log")
public class PromptLog {

    //@TableId 声明主键
    @TableId(type = IdType.AUTO)
    private Long id;

    private String model;
    private String userInput;
    private String aiResponse;
    private Integer tokenUsage;
    private LocalDateTime createTime;
}
