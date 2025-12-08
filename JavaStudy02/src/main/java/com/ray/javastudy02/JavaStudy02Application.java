package com.ray.javastudy02;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
@MapperScan("com.ray.javastudy02.mapper")
public class JavaStudy02Application {

    public static void main(String[] args) {
        SpringApplication.run(JavaStudy02Application.class, args);
    }

}
