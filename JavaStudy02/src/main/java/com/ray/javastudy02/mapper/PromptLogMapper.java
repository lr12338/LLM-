package com.ray.javastudy02.mapper;


import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;
import com.ray.javastudy02.model.PromptLog;

// @Mapper: 告诉 Spring Boot 这是一个操作数据库的接口
@Mapper
public interface PromptLogMapper extends BaseMapper<PromptLog> {
    // 继承 BaseMapper 后，你自动拥有了 insert, delete, update, selectById 等方法
    // 这一行代码值千金！
}
