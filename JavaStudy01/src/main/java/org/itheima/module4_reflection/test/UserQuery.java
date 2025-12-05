package org.itheima.module4_reflection.test;

import java.lang.annotation.Target;


public class UserQuery {
    String username;

    @Sensitive
    String phoneNumber;

    @Sensitive
    String idCard;

    //添加 toString()
    //如果不加 toString()，直接打印对象会输出类似 UserQuery@1b6d3586 的内存地址，看不出里面的值变没变。
    @Override
    public String toString() {
        return "UserQuery{"+
                "username='" + username + '\'' +
                ", phoneNumber='" + phoneNumber +'\\' +
                ", idCard;'" + idCard + '\'' +
                '}';
    }
}
